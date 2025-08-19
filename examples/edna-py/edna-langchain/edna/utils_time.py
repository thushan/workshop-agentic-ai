"""Time utilities for EDNA."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Optional


def suggest_send_time(mentee_timezone: Optional[str] = None) -> str:
    """Suggest optimal send time in mentee's timezone."""
    
    # Default to Melbourne if no timezone provided
    tz_str = mentee_timezone or "Australia/Melbourne"
    
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        # Fallback to Melbourne if invalid timezone
        tz = ZoneInfo("Australia/Melbourne")
    
    # Get current time in target timezone
    now_local = datetime.now(tz)
    
    # Target time is 9:15 AM
    target_hour = 9
    target_minute = 15
    
    # If current time is before 9:00 AM today, use today
    if now_local.hour < target_hour:
        send_date = now_local.date()
    else:
        # Otherwise, use next business day
        send_date = now_local.date() + timedelta(days=1)
    
    # Skip weekends
    while send_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        send_date += timedelta(days=1)
    
    # Create datetime with target time
    send_time = datetime(
        send_date.year,
        send_date.month,
        send_date.day,
        target_hour,
        target_minute,
        0,
        tzinfo=tz
    )
    
    return send_time.isoformat()


def choose_channel(classification: str, recent_channel: Optional[str] = None) -> str:
    """Choose appropriate communication channel."""
    
    # Use recent channel if available
    if recent_channel and recent_channel in ["email", "in_app", "slack"]:
        return recent_channel
    
    # Default based on classification
    if classification in ["dormant", "blocked_goal"]:
        return "email"
    elif classification == "celebrate_wins":
        return "in_app"
    else:
        return "email"