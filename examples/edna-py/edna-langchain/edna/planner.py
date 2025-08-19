"""Planning utilities for nudge suggestions."""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from .types import Message, Channel
from .utils_time import suggest_send_time, choose_channel


def get_recent_channel(messages: List[Message], days: int = 14) -> Optional[str]:
    """Get most recent communication channel from messages."""
    
    if not messages:
        return None
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    
    recent_messages = [
        m for m in messages 
        if m.timestamp > cutoff
    ]
    
    if recent_messages:
        # Get the most recent message's channel
        latest = max(recent_messages, key=lambda m: m.timestamp)
        return latest.channel.value
    
    return None


def plan_nudge_delivery(
    classification: str,
    messages: List[Message],
    mentee_timezone: Optional[str] = None,
    channel_override: Optional[str] = None
) -> tuple[str, str]:
    """Plan when and how to deliver the nudge."""
    
    # Determine channel
    if channel_override:
        channel = channel_override
    else:
        recent_channel = get_recent_channel(messages)
        channel = choose_channel(classification, recent_channel)
    
    # Determine send time
    send_time = suggest_send_time(mentee_timezone)
    
    return channel, send_time