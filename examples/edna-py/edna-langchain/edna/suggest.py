"""Main suggestion generation logic."""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from tabulate import tabulate

from .io_loaders import DataLoader
from .features import compute_features
from .classify import classify
from .retriever import TipsRetriever
from .llm_provider import get_chat_model, get_embedding
from .prompts import draft_template
from .evaluator import evaluate
from .planner import plan_nudge_delivery
from .types import Suggestion

logger = logging.getLogger(__name__)


def filter_active_pairs(
    data: DataLoader, 
    since_days: int = 30
) -> List[str]:
    """Filter pairs with any activity in the last N days."""
    
    if since_days <= 0:
        return list(data.pairings.keys())
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=since_days)
    
    active_pairs = set()
    
    # Check messages
    for msg in data.messages:
        if msg.timestamp > cutoff:
            active_pairs.add(msg.pair_id)
    
    # Check checkins
    for checkin in data.checkins:
        if checkin.timestamp > cutoff:
            active_pairs.add(checkin.pair_id)
    
    # Check goal updates
    for goal in data.goals:
        if goal.updated_at > cutoff:
            active_pairs.add(goal.pair_id)
    
    # Include new pairings
    for pair_id, pairing in data.pairings.items():
        if pairing.started_at > cutoff:
            active_pairs.add(pair_id)
    
    return list(active_pairs)


def generate_suggestions(
    data_dir: Path,
    output_path: Path,
    since_days: int = 30,
    limit: int = 20,
    channel_override: Optional[str] = None,
    mark_as_sent: bool = False,
    dry_run: bool = True
) -> List[Suggestion]:
    """Generate nudge suggestions for mentor-mentee pairs."""
    
    # Load data
    logger.info("Loading data...")
    data = DataLoader(data_dir).load_all()
    
    # Initialize LLM and retriever
    logger.info("Initializing LLM and retriever...")
    llm = get_chat_model()
    if not llm:
        logger.error("Failed to initialize LLM")
        return []
    
    embeddings = get_embedding()
    retriever = TipsRetriever(data.tips, embeddings)
    
    # Filter pairs
    active_pairs = filter_active_pairs(data, since_days)
    logger.info(f"Found {len(active_pairs)} active pairs")
    
    # Generate suggestions
    suggestions = []
    sent_log_path = output_path.parent / "sent_log.jsonl"
    
    for pair_id in active_pairs[:limit]:
        try:
            # Compute features
            features = compute_features(pair_id, data)
            if not features:
                continue
            
            # Classify
            result = classify(features, data)
            if not result.classification:
                continue
            
            # Retrieve tips
            citations = retriever.search(
                result.classification.value,
                result.explanations,
                top_k=3
            )
            
            # Get mentee info
            pairing = data.pairings[pair_id]
            mentee = data.users.get(pairing.mentee_id)
            mentee_name = mentee.first_name if mentee else ""
            mentee_timezone = mentee.timezone if mentee else "Australia/Melbourne"
            
            # Prepare tips text
            tip_texts = []
            for citation in citations:
                tip = next((t for t in data.tips if t.tip_id == citation.tip_id), None)
                if tip:
                    tip_texts.append(tip.text)
            tips_joined = " • ".join(tip_texts[:3])
            
            # Draft nudge
            draft_prompt = draft_template.format(
                first_name=mentee_name,
                cadence_days=features.cadence_days,
                classification=result.classification.value,
                explanations="\n".join(f"- {e}" for e in result.explanations),
                tips_joined=tips_joined
            )
            
            nudge_response = llm.invoke(draft_prompt)
            nudge_draft = nudge_response.content.strip()
            
            # Evaluate
            eval_context = {
                "pair_id": pair_id,
                "classification": result.classification.value,
                "explanations": result.explanations
            }
            safety_checks = evaluate(nudge_draft, eval_context, llm, sent_log_path)
            
            # Plan delivery
            pair_messages = [m for m in data.messages if m.pair_id == pair_id]
            channel, send_time = plan_nudge_delivery(
                result.classification.value,
                pair_messages,
                mentee_timezone,
                channel_override
            )
            
            # Create suggestion
            suggestion = Suggestion(
                pair_id=pair_id,
                classification=result.classification.value,
                confidence=result.confidence,
                explanations=result.explanations,
                suggested_channel=channel,
                suggested_send_time_local=send_time,
                timezone=mentee_timezone or "Australia/Melbourne",
                nudge_draft=nudge_draft,
                citations=[{"tip_id": c.tip_id, "score": c.score} for c in citations],
                safety_checks={
                    "tone_supportive": safety_checks.tone_supportive,
                    "no_private_data_leak": safety_checks.no_private_data_leak,
                    "not_duplicate_last_7d": safety_checks.not_duplicate_last_7d,
                    "reason_if_any": safety_checks.reason_if_any
                }
            )
            
            suggestions.append(suggestion)
            logger.info(f"Generated suggestion for {pair_id}: {result.classification.value}")
            
        except Exception as e:
            logger.error(f"Error processing pair {pair_id}: {e}")
            continue
    
    # Write output
    if suggestions:
        write_suggestions(suggestions, output_path, sent_log_path, mark_as_sent)
        print_summary_table(suggestions)
    else:
        logger.info("No suggestions generated")
    
    return suggestions


def write_suggestions(
    suggestions: List[Suggestion],
    output_path: Path,
    sent_log_path: Path,
    mark_as_sent: bool
):
    """Write suggestions to JSONL file."""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write suggestions
    with open(output_path, 'a', encoding='utf-8') as f:
        for suggestion in suggestions:
            json_line = json.dumps({
                "pair_id": suggestion.pair_id,
                "classification": suggestion.classification,
                "confidence": suggestion.confidence,
                "explanations": suggestion.explanations,
                "suggested_channel": suggestion.suggested_channel,
                "suggested_send_time_local": suggestion.suggested_send_time_local,
                "timezone": suggestion.timezone,
                "nudge_draft": suggestion.nudge_draft,
                "citations": suggestion.citations,
                "safety_checks": suggestion.safety_checks
            })
            f.write(json_line + '\n')
    
    logger.info(f"Wrote {len(suggestions)} suggestions to {output_path}")
    
    # Update sent log if requested
    if mark_as_sent:
        with open(sent_log_path, 'a', encoding='utf-8') as f:
            for suggestion in suggestions:
                log_entry = {
                    "pair_id": suggestion.pair_id,
                    "classification": suggestion.classification,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Updated sent log at {sent_log_path}")


def print_summary_table(suggestions: List[Suggestion]):
    """Print summary table of suggestions."""
    
    table_data = []
    for s in suggestions:
        send_time = s.suggested_send_time_local.split('T')[0] + ' ' + \
                   s.suggested_send_time_local.split('T')[1][:5]
        table_data.append([
            s.pair_id,
            s.classification,
            f"{s.confidence:.2f}",
            send_time,
            s.suggested_channel
        ])
    
    headers = ["Pair ID", "Classification", "Confidence", "Send Time", "Channel"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))