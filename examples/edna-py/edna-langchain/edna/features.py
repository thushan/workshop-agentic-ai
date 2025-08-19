"""Feature computation for mentor-mentee pairs."""

from datetime import datetime, timezone
from typing import Optional, List
from .types import Features, Message, Checkin, Goal, GoalStatus, UserRole
from .io_loaders import DataLoader


def compute_features(pair_id: str, data: DataLoader) -> Optional[Features]:
    """Compute features for a mentor-mentee pair."""
    
    if pair_id not in data.pairings:
        return None
    
    pairing = data.pairings[pair_id]
    now = datetime.now(timezone.utc)
    
    # Get programme cadence
    programme = data.programmes.get(pairing.programme_id)
    cadence_days = programme.cadence_days if programme else 14
    
    # Filter data for this pair
    pair_messages = [m for m in data.messages if m.pair_id == pair_id]
    pair_checkins = [c for c in data.checkins if c.pair_id == pair_id]
    pair_goals = [g for g in data.goals if g.pair_id == pair_id]
    
    # Days since pair started
    pair_started_days_ago = (now - pairing.started_at).total_seconds() / 86400
    
    # Days since last message
    days_since_last_message = None
    if pair_messages:
        last_msg_time = max(m.timestamp for m in pair_messages)
        days_since_last_message = (now - last_msg_time).total_seconds() / 86400
    
    # Days since last checkin
    days_since_last_checkin = None
    if pair_checkins:
        last_checkin_time = max(c.timestamp for c in pair_checkins)
        days_since_last_checkin = (now - last_checkin_time).total_seconds() / 86400
    
    # 14-day window message counts
    cutoff_14d = (now - datetime.now(timezone.utc).replace(tzinfo=timezone.utc)).total_seconds() / 86400
    recent_messages = [m for m in pair_messages 
                      if (now - m.timestamp).total_seconds() / 86400 <= 14]
    
    msg_count_14d = len(recent_messages)
    mentor_msgs_14d = sum(1 for m in recent_messages if m.author_role == UserRole.MENTOR)
    mentee_msgs_14d = sum(1 for m in recent_messages if m.author_role == UserRole.MENTEE)
    mentor_pct_14d = mentor_msgs_14d / max(1, msg_count_14d)
    
    # Goals analysis
    open_statuses = {GoalStatus.OPEN, GoalStatus.AT_RISK, GoalStatus.BLOCKED}
    blocked_statuses = {GoalStatus.BLOCKED, GoalStatus.AT_RISK}
    
    goals_open = sum(1 for g in pair_goals if g.status in open_statuses)
    goals_blocked = sum(1 for g in pair_goals if g.status in blocked_statuses)
    
    # Days since goal update (for open/blocked goals)
    days_since_goal_update_max = None
    open_blocked_goals = [g for g in pair_goals if g.status in open_statuses]
    if open_blocked_goals:
        most_recent_update = max(g.updated_at for g in open_blocked_goals)
        days_since_goal_update_max = (now - most_recent_update).total_seconds() / 86400
    
    return Features(
        pair_id=pair_id,
        days_since_last_message=days_since_last_message,
        days_since_last_checkin=days_since_last_checkin,
        msg_count_14d=msg_count_14d,
        mentor_msgs_14d=mentor_msgs_14d,
        mentee_msgs_14d=mentee_msgs_14d,
        mentor_pct_14d=mentor_pct_14d,
        goals_open=goals_open,
        goals_blocked=goals_blocked,
        days_since_goal_update_max=days_since_goal_update_max,
        cadence_days=cadence_days,
        pair_started_days_ago=pair_started_days_ago,
        has_any_messages=len(pair_messages) > 0
    )