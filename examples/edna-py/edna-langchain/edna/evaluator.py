"""Evaluation logic for nudge messages."""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from .types import SafetyChecks
from .prompts import evaluation_template

logger = logging.getLogger(__name__)


def check_duplicate_local(
    pair_id: str, 
    classification: str, 
    sent_log_path: Path,
    days_threshold: int = 7
) -> bool:
    """Check if similar nudge was sent recently by reading sent_log."""
    
    if not sent_log_path.exists():
        return False
    
    try:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days_threshold)
        
        with open(sent_log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if (entry.get("pair_id") == pair_id and 
                        entry.get("classification") == classification):
                        timestamp = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                        if timestamp > cutoff:
                            return True
                except Exception:
                    continue
    except Exception as e:
        logger.warning(f"Error checking sent log: {e}")
    
    return False


def evaluate(
    nudge_draft: str,
    context: Dict[str, Any],
    llm,
    sent_log_path: Optional[Path] = None
) -> SafetyChecks:
    """Evaluate nudge message for safety and quality."""
    
    # Prepare context for LLM evaluation
    eval_prompt = evaluation_template.format(
        nudge_draft=nudge_draft,
        classification=context.get("classification", ""),
        explanations="\n".join(context.get("explanations", []))
    )
    
    # Get LLM evaluation
    safety_checks = SafetyChecks(
        tone_supportive=True,
        no_private_data_leak=True,
        not_duplicate_last_7d=True
    )
    
    if llm:
        try:
            response = llm.invoke(eval_prompt)
            eval_result = json.loads(response.content)
            
            safety_checks.tone_supportive = eval_result.get("tone_supportive", True)
            safety_checks.no_private_data_leak = eval_result.get("no_private_data_leak", True)
            safety_checks.not_duplicate_last_7d = eval_result.get("not_duplicate_last_7d", True)
            safety_checks.reason_if_any = eval_result.get("reason_if_any", "")
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed, using defaults: {e}")
    
    # Override duplicate check with local check if sent_log exists
    if sent_log_path and context.get("pair_id") and context.get("classification"):
        is_duplicate = check_duplicate_local(
            context["pair_id"],
            context["classification"],
            sent_log_path
        )
        if is_duplicate:
            safety_checks.not_duplicate_last_7d = False
            if not safety_checks.reason_if_any:
                safety_checks.reason_if_any = "Similar nudge sent in last 7 days"
    
    return safety_checks