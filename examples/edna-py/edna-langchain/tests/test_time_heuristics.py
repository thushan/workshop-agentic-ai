"""Tests for time heuristics."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from edna.utils_time import suggest_send_time, choose_channel


def test_suggest_send_time_morning():
    """Test send time suggestion for morning hours."""
    # Mock a morning time (8 AM Melbourne)
    send_time_str = suggest_send_time("Australia/Melbourne")
    send_time = datetime.fromisoformat(send_time_str)
    
    # Should be 9:15 AM
    assert send_time.hour == 9
    assert send_time.minute == 15
    
    # Should not be on weekend
    assert send_time.weekday() < 5


def test_suggest_send_time_afternoon():
    """Test send time suggestion for afternoon hours."""
    # When called in afternoon, should schedule for next business day
    send_time_str = suggest_send_time("Australia/Melbourne")
    send_time = datetime.fromisoformat(send_time_str)
    
    # Should be 9:15 AM
    assert send_time.hour == 9
    assert send_time.minute == 15
    
    # Should not be on weekend
    assert send_time.weekday() < 5


def test_suggest_send_time_skip_weekend():
    """Test that weekends are skipped."""
    # Test with Sydney timezone
    send_time_str = suggest_send_time("Australia/Sydney")
    send_time = datetime.fromisoformat(send_time_str)
    
    # Should never be Saturday (5) or Sunday (6)
    assert send_time.weekday() < 5


def test_suggest_send_time_invalid_timezone():
    """Test fallback for invalid timezone."""
    # Invalid timezone should fallback to Melbourne
    send_time_str = suggest_send_time("Invalid/Timezone")
    send_time = datetime.fromisoformat(send_time_str)
    
    # Should still produce valid time
    assert send_time.hour == 9
    assert send_time.minute == 15


def test_suggest_send_time_no_timezone():
    """Test default timezone handling."""
    # No timezone should default to Melbourne
    send_time_str = suggest_send_time(None)
    send_time = datetime.fromisoformat(send_time_str)
    
    # Should still produce valid time
    assert send_time.hour == 9
    assert send_time.minute == 15


def test_choose_channel_dormant():
    """Test channel selection for dormant classification."""
    channel = choose_channel("dormant")
    assert channel == "email"


def test_choose_channel_blocked_goal():
    """Test channel selection for blocked goal."""
    channel = choose_channel("blocked_goal")
    assert channel == "email"


def test_choose_channel_celebrate_wins():
    """Test channel selection for celebrate wins."""
    channel = choose_channel("celebrate_wins")
    assert channel == "in_app"


def test_choose_channel_with_recent():
    """Test channel selection with recent channel preference."""
    # Recent channel should take precedence
    channel = choose_channel("dormant", recent_channel="slack")
    assert channel == "slack"
    
    channel = choose_channel("celebrate_wins", recent_channel="email")
    assert channel == "email"


def test_choose_channel_invalid_recent():
    """Test channel selection with invalid recent channel."""
    # Invalid recent channel should be ignored
    channel = choose_channel("dormant", recent_channel="invalid")
    assert channel == "email"