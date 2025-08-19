"""Classification rules for mentor-mentee pair engagement."""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from .types import Features, Classification, ClassificationResult, Goal, GoalStatus
from .io_loaders import DataLoader


def classify(features: Features, data: DataLoader = None) -> ClassificationResult:
    """Classify pair engagement status based on features."""
    
    explanations = []
    classification = None
    confidence = 0.0
    
    # Check for dormant first (highest priority)
    if features.days_since_last_message is not None:
        threshold = features.cadence_days * 1.5
        if features.days_since_last_message > threshold:
            classification = Classification.DORMANT
            gap_ratio = features.days_since_last_message / features.cadence_days
            confidence = min(0.9, 0.6 + (gap_ratio - 1.5) * 0.1)
            explanations.append(
                f"last message {int(features.days_since_last_message)} days ago vs cadence {features.cadence_days}"
            )
    
    if not classification and features.days_since_last_checkin is not None:
        threshold = features.cadence_days * 1.5
        if features.days_since_last_checkin > threshold:
            classification = Classification.DORMANT
            gap_ratio = features.days_since_last_checkin / features.cadence_days
            confidence = min(0.9, 0.6 + (gap_ratio - 1.5) * 0.1)
            explanations.append(
                f"no check-ins recorded in {int(features.days_since_last_checkin)} days"
            )
    
    # Check for blocked goals (second priority)
    if not classification:
        if features.goals_blocked > 0:
            classification = Classification.BLOCKED_GOAL
            confidence = 0.75
            explanations.append(f"{features.goals_blocked} blocked goal(s)")
        elif features.goals_open > 0 and features.days_since_goal_update_max is not None:
            if features.days_since_goal_update_max > 28:
                classification = Classification.BLOCKED_GOAL
                confidence = 0.7
                explanations.append(
                    f"goal blocked since {int(features.days_since_goal_update_max)} days"
                )
    
    # Check for one-sided conversation (third priority)
    if not classification:
        if features.msg_count_14d >= 4 and features.mentor_pct_14d > 0.7:
            classification = Classification.ONE_SIDED
            confidence = 0.65 + (features.mentor_pct_14d - 0.7) * 0.5
            explanations.append(
                f"mentor speaking {int(features.mentor_pct_14d * 100)}% over last 14d"
            )
    
    # Check for celebration opportunities (fourth priority)
    if not classification and data:
        # Check recent checkins for high scores
        pair_checkins = [c for c in data.checkins if c.pair_id == features.pair_id]
        if len(pair_checkins) >= 2:
            recent_checkins = sorted(pair_checkins, key=lambda c: c.timestamp, reverse=True)[:2]
            avg_mentee_score = sum(c.mentee_score for c in recent_checkins) / len(recent_checkins)
            if avg_mentee_score >= 4:
                classification = Classification.CELEBRATE_WINS
                confidence = 0.7
                explanations.append(f"average mentee score {avg_mentee_score:.1f} in recent check-ins")
        
        # Check for recently completed goals
        if not classification:
            now = datetime.now(timezone.utc)
            pair_goals = [g for g in data.goals if g.pair_id == features.pair_id]
            recent_completed = [
                g for g in pair_goals 
                if g.status == GoalStatus.COMPLETED and 
                (now - g.updated_at).total_seconds() / 86400 <= 14
            ]
            if recent_completed:
                classification = Classification.CELEBRATE_WINS
                confidence = 0.75
                explanations.append(f"{len(recent_completed)} goal(s) completed recently")
    
    # Fallback for pairs with no activity
    if not classification and not features.has_any_messages:
        if features.pair_started_days_ago > features.cadence_days * 2:
            classification = Classification.DORMANT
            confidence = 0.55
            explanations.append(
                f"no messages after {int(features.pair_started_days_ago)} days since pairing"
            )
    
    # If no classification found, return None with low confidence
    if not classification:
        explanations.append("no engagement issues detected")
    
    return ClassificationResult(
        classification=classification,
        confidence=confidence,
        explanations=explanations
    )