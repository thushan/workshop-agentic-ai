"""Type definitions for EDNA."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class UserRole(str, Enum):
    MENTOR = "mentor"
    MENTEE = "mentee"
    ADMIN = "admin"


class Channel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"


class GoalStatus(str, Enum):
    OPEN = "open"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class Classification(str, Enum):
    DORMANT = "dormant"
    BLOCKED_GOAL = "blocked_goal"
    ONE_SIDED = "one_sided"
    CELEBRATE_WINS = "celebrate_wins"


@dataclass
class User:
    user_id: str
    role: UserRole
    email: str
    timezone: Optional[str]
    first_name: str
    joined_at: datetime


@dataclass
class Pairing:
    pair_id: str
    mentor_id: str
    mentee_id: str
    programme_id: str
    started_at: datetime


@dataclass
class Message:
    pair_id: str
    timestamp: datetime
    author_role: UserRole
    channel: Channel
    text: str


@dataclass
class Checkin:
    pair_id: str
    timestamp: datetime
    mentee_score: int
    mentor_score: int
    notes: Optional[str]


@dataclass
class Goal:
    pair_id: str
    goal_id: str
    title: str
    status: GoalStatus
    updated_at: datetime


@dataclass
class Programme:
    programme_id: str
    name: str
    cadence_days: int
    success_markers: List[str]


@dataclass
class Tip:
    tip_id: str
    situation: str
    text: str


@dataclass
class Features:
    pair_id: str
    days_since_last_message: Optional[float]
    days_since_last_checkin: Optional[float]
    msg_count_14d: int
    mentor_msgs_14d: int
    mentee_msgs_14d: int
    mentor_pct_14d: float
    goals_open: int
    goals_blocked: int
    days_since_goal_update_max: Optional[float]
    cadence_days: int
    pair_started_days_ago: float
    has_any_messages: bool


@dataclass
class ClassificationResult:
    classification: Optional[Classification]
    confidence: float
    explanations: List[str]


@dataclass
class Citation:
    tip_id: str
    score: float


@dataclass
class SafetyChecks:
    tone_supportive: bool
    no_private_data_leak: bool
    not_duplicate_last_7d: bool
    reason_if_any: str = ""


@dataclass
class Suggestion:
    pair_id: str
    classification: str
    confidence: float
    explanations: List[str]
    suggested_channel: str
    suggested_send_time_local: str
    timezone: str
    nudge_draft: str
    citations: List[Dict[str, Any]]
    safety_checks: Dict[str, Any]