"""Tests for feature computation."""

import pytest
from datetime import datetime, timezone, timedelta
from edna.types import Pairing, Message, Checkin, Goal, Programme, UserRole, Channel, GoalStatus
from edna.features import compute_features
from edna.io_loaders import DataLoader


def create_test_data():
    """Create test data for feature computation."""
    data = DataLoader(None)
    
    # Create test pairing
    data.pairings["p001"] = Pairing(
        pair_id="p001",
        mentor_id="m001",
        mentee_id="u001",
        programme_id="prog001",
        started_at=datetime.now(timezone.utc) - timedelta(days=60)
    )
    
    # Create programme
    data.programmes["prog001"] = Programme(
        programme_id="prog001",
        name="Test Programme",
        cadence_days=10,
        success_markers=[]
    )
    
    return data


def test_days_since_last_message():
    """Test calculation of days since last message."""
    data = create_test_data()
    
    # Add messages
    now = datetime.now(timezone.utc)
    data.messages = [
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=5),
            author_role=UserRole.MENTOR,
            channel=Channel.EMAIL,
            text="Hello"
        ),
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=10),
            author_role=UserRole.MENTEE,
            channel=Channel.EMAIL,
            text="Hi"
        )
    ]
    
    features = compute_features("p001", data)
    assert features is not None
    assert 4.9 < features.days_since_last_message < 5.1


def test_14d_window_counts():
    """Test message counts in 14-day window."""
    data = create_test_data()
    
    now = datetime.now(timezone.utc)
    data.messages = [
        # Within 14 days
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=5),
            author_role=UserRole.MENTOR,
            channel=Channel.EMAIL,
            text="Message 1"
        ),
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=10),
            author_role=UserRole.MENTOR,
            channel=Channel.EMAIL,
            text="Message 2"
        ),
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=12),
            author_role=UserRole.MENTEE,
            channel=Channel.EMAIL,
            text="Message 3"
        ),
        # Outside 14 days
        Message(
            pair_id="p001",
            timestamp=now - timedelta(days=20),
            author_role=UserRole.MENTEE,
            channel=Channel.EMAIL,
            text="Old message"
        )
    ]
    
    features = compute_features("p001", data)
    assert features.msg_count_14d == 3
    assert features.mentor_msgs_14d == 2
    assert features.mentee_msgs_14d == 1
    assert abs(features.mentor_pct_14d - 0.667) < 0.01


def test_goal_metrics():
    """Test goal-related feature computation."""
    data = create_test_data()
    
    now = datetime.now(timezone.utc)
    data.goals = [
        Goal(
            pair_id="p001",
            goal_id="g001",
            title="Goal 1",
            status=GoalStatus.OPEN,
            updated_at=now - timedelta(days=15)
        ),
        Goal(
            pair_id="p001",
            goal_id="g002",
            title="Goal 2",
            status=GoalStatus.BLOCKED,
            updated_at=now - timedelta(days=30)
        ),
        Goal(
            pair_id="p001",
            goal_id="g003",
            title="Goal 3",
            status=GoalStatus.COMPLETED,
            updated_at=now - timedelta(days=5)
        )
    ]
    
    features = compute_features("p001", data)
    assert features.goals_open == 2  # OPEN + BLOCKED
    assert features.goals_blocked == 1  # Only BLOCKED
    assert 14.9 < features.days_since_goal_update_max < 15.1


def test_checkin_recency():
    """Test days since last checkin calculation."""
    data = create_test_data()
    
    now = datetime.now(timezone.utc)
    data.checkins = [
        Checkin(
            pair_id="p001",
            timestamp=now - timedelta(days=7),
            mentee_score=4,
            mentor_score=5,
            notes="Good progress"
        ),
        Checkin(
            pair_id="p001",
            timestamp=now - timedelta(days=21),
            mentee_score=3,
            mentor_score=4,
            notes="Some challenges"
        )
    ]
    
    features = compute_features("p001", data)
    assert 6.9 < features.days_since_last_checkin < 7.1


def test_no_messages():
    """Test features when pair has no messages."""
    data = create_test_data()
    
    features = compute_features("p001", data)
    assert features.days_since_last_message is None
    assert features.msg_count_14d == 0
    assert features.has_any_messages is False
    assert features.mentor_pct_14d == 0.0