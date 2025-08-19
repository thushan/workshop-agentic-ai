"""Tests for classification rules."""

import pytest
from datetime import datetime, timezone, timedelta
from edna.types import Features, Classification, Checkin, Goal, GoalStatus
from edna.classify import classify
from edna.io_loaders import DataLoader


def test_dormant_classification():
    """Test dormant classification based on message gap."""
    features = Features(
        pair_id="p001",
        days_since_last_message=20,
        days_since_last_checkin=None,
        msg_count_14d=0,
        mentor_msgs_14d=0,
        mentee_msgs_14d=0,
        mentor_pct_14d=0.0,
        goals_open=0,
        goals_blocked=0,
        days_since_goal_update_max=None,
        cadence_days=10,
        pair_started_days_ago=60,
        has_any_messages=True
    )
    
    result = classify(features)
    assert result.classification == Classification.DORMANT
    assert result.confidence >= 0.6
    assert "last message 20 days ago vs cadence 10" in result.explanations[0]


def test_blocked_goal_classification():
    """Test blocked goal classification."""
    features = Features(
        pair_id="p001",
        days_since_last_message=8,
        days_since_last_checkin=None,
        msg_count_14d=5,
        mentor_msgs_14d=3,
        mentee_msgs_14d=2,
        mentor_pct_14d=0.6,
        goals_open=2,
        goals_blocked=1,
        days_since_goal_update_max=35,
        cadence_days=10,
        pair_started_days_ago=60,
        has_any_messages=True
    )
    
    result = classify(features)
    assert result.classification == Classification.BLOCKED_GOAL
    assert "1 blocked goal(s)" in result.explanations[0]


def test_one_sided_classification():
    """Test one-sided conversation classification."""
    features = Features(
        pair_id="p001",
        days_since_last_message=5,
        days_since_last_checkin=None,
        msg_count_14d=10,
        mentor_msgs_14d=8,
        mentee_msgs_14d=2,
        mentor_pct_14d=0.8,
        goals_open=0,
        goals_blocked=0,
        days_since_goal_update_max=None,
        cadence_days=10,
        pair_started_days_ago=60,
        has_any_messages=True
    )
    
    result = classify(features)
    assert result.classification == Classification.ONE_SIDED
    assert "mentor speaking 80% over last 14d" in result.explanations[0]


def test_celebrate_wins_classification():
    """Test celebrate wins classification with high checkin scores."""
    data = DataLoader(None)
    now = datetime.now(timezone.utc)
    
    # Add recent high-scoring checkins
    data.checkins = [
        Checkin(
            pair_id="p001",
            timestamp=now - timedelta(days=3),
            mentee_score=5,
            mentor_score=5,
            notes="Excellent"
        ),
        Checkin(
            pair_id="p001",
            timestamp=now - timedelta(days=10),
            mentee_score=4,
            mentor_score=4,
            notes="Good"
        )
    ]
    
    features = Features(
        pair_id="p001",
        days_since_last_message=5,
        days_since_last_checkin=3,
        msg_count_14d=3,
        mentor_msgs_14d=2,
        mentee_msgs_14d=1,
        mentor_pct_14d=0.67,
        goals_open=0,
        goals_blocked=0,
        days_since_goal_update_max=None,
        cadence_days=10,
        pair_started_days_ago=60,
        has_any_messages=True
    )
    
    result = classify(features, data)
    assert result.classification == Classification.CELEBRATE_WINS
    assert "average mentee score" in " ".join(result.explanations)


def test_priority_ordering():
    """Test that dormant takes priority over other classifications."""
    features = Features(
        pair_id="p001",
        days_since_last_message=25,  # Triggers dormant
        days_since_last_checkin=None,
        msg_count_14d=5,  # Would trigger one-sided
        mentor_msgs_14d=4,
        mentee_msgs_14d=1,
        mentor_pct_14d=0.8,
        goals_open=1,  # Would trigger blocked goal
        goals_blocked=1,
        days_since_goal_update_max=30,
        cadence_days=10,
        pair_started_days_ago=60,
        has_any_messages=True
    )
    
    result = classify(features)
    # Dormant should take priority
    assert result.classification == Classification.DORMANT


def test_no_activity_fallback():
    """Test classification for pairs with no messages."""
    features = Features(
        pair_id="p001",
        days_since_last_message=None,
        days_since_last_checkin=None,
        msg_count_14d=0,
        mentor_msgs_14d=0,
        mentee_msgs_14d=0,
        mentor_pct_14d=0.0,
        goals_open=0,
        goals_blocked=0,
        days_since_goal_update_max=None,
        cadence_days=10,
        pair_started_days_ago=30,  # More than 2x cadence
        has_any_messages=False
    )
    
    result = classify(features)
    assert result.classification == Classification.DORMANT
    assert result.confidence == 0.55
    assert "no messages after 30 days since pairing" in result.explanations[0]