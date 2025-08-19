"""Data loading utilities for EDNA."""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from .types import (
    User, Pairing, Message, Checkin, Goal, Programme, Tip,
    UserRole, Channel, GoalStatus
)

logger = logging.getLogger(__name__)


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO8601 datetime string."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception:
        return datetime.fromisoformat(dt_str)


def load_users(filepath: Path) -> Dict[str, User]:
    """Load users from CSV."""
    users = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    user = User(
                        user_id=row['user_id'],
                        role=UserRole(row['role']),
                        email=row['email'],
                        timezone=row.get('timezone') or None,
                        first_name=row['first_name'],
                        joined_at=parse_datetime(row['joined_at'])
                    )
                    users[user.user_id] = user
                except Exception as e:
                    logger.warning(f"Skipping invalid user row: {e}")
    except FileNotFoundError:
        logger.warning(f"Users file not found: {filepath}")
    return users


def load_pairings(filepath: Path) -> Dict[str, Pairing]:
    """Load pairings from CSV."""
    pairings = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pairing = Pairing(
                        pair_id=row['pair_id'],
                        mentor_id=row['mentor_id'],
                        mentee_id=row['mentee_id'],
                        programme_id=row['programme_id'],
                        started_at=parse_datetime(row['started_at'])
                    )
                    pairings[pairing.pair_id] = pairing
                except Exception as e:
                    logger.warning(f"Skipping invalid pairing row: {e}")
    except FileNotFoundError:
        logger.warning(f"Pairings file not found: {filepath}")
    return pairings


def load_messages(filepath: Path) -> List[Message]:
    """Load messages from CSV."""
    messages = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    message = Message(
                        pair_id=row['pair_id'],
                        timestamp=parse_datetime(row['timestamp']),
                        author_role=UserRole(row['author_role']),
                        channel=Channel(row['channel']),
                        text=row['text']
                    )
                    messages.append(message)
                except Exception as e:
                    logger.warning(f"Skipping invalid message row: {e}")
    except FileNotFoundError:
        logger.warning(f"Messages file not found: {filepath}")
    return messages


def load_checkins(filepath: Path) -> List[Checkin]:
    """Load checkins from CSV."""
    checkins = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    checkin = Checkin(
                        pair_id=row['pair_id'],
                        timestamp=parse_datetime(row['timestamp']),
                        mentee_score=int(row['mentee_score']),
                        mentor_score=int(row['mentor_score']),
                        notes=row.get('notes') or None
                    )
                    checkins.append(checkin)
                except Exception as e:
                    logger.warning(f"Skipping invalid checkin row: {e}")
    except FileNotFoundError:
        logger.warning(f"Checkins file not found: {filepath}")
    return checkins


def load_goals(filepath: Path) -> List[Goal]:
    """Load goals from CSV."""
    goals = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    goal = Goal(
                        pair_id=row['pair_id'],
                        goal_id=row['goal_id'],
                        title=row['title'],
                        status=GoalStatus(row['status']),
                        updated_at=parse_datetime(row['updated_at'])
                    )
                    goals.append(goal)
                except Exception as e:
                    logger.warning(f"Skipping invalid goal row: {e}")
    except FileNotFoundError:
        logger.warning(f"Goals file not found: {filepath}")
    return goals


def load_programmes(filepath: Path) -> Dict[str, Programme]:
    """Load programmes from JSON."""
    programmes = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                try:
                    programme = Programme(
                        programme_id=item['programme_id'],
                        name=item['name'],
                        cadence_days=item['cadence_days'],
                        success_markers=item.get('success_markers', [])
                    )
                    programmes[programme.programme_id] = programme
                except Exception as e:
                    logger.warning(f"Skipping invalid programme: {e}")
    except FileNotFoundError:
        logger.warning(f"Programmes file not found: {filepath}")
    return programmes


def load_tips(filepath: Path) -> List[Tip]:
    """Load tips from JSON."""
    tips = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                try:
                    tip = Tip(
                        tip_id=item['tip_id'],
                        situation=item['situation'],
                        text=item['text']
                    )
                    tips.append(tip)
                except Exception as e:
                    logger.warning(f"Skipping invalid tip: {e}")
    except FileNotFoundError:
        logger.warning(f"Tips file not found: {filepath}")
    return tips


class DataLoader:
    """Central data loader for all EDNA data."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.users: Dict[str, User] = {}
        self.pairings: Dict[str, Pairing] = {}
        self.messages: List[Message] = []
        self.checkins: List[Checkin] = []
        self.goals: List[Goal] = []
        self.programmes: Dict[str, Programme] = {}
        self.tips: List[Tip] = []
    
    def load_all(self):
        """Load all data files."""
        self.users = load_users(self.data_dir / "users.csv")
        self.pairings = load_pairings(self.data_dir / "pairings.csv")
        self.messages = load_messages(self.data_dir / "messages.csv")
        self.checkins = load_checkins(self.data_dir / "checkins.csv")
        self.goals = load_goals(self.data_dir / "goals.csv")
        self.programmes = load_programmes(self.data_dir / "programmes.json")
        self.tips = load_tips(self.data_dir / "tips.json")
        
        logger.info(f"Loaded: {len(self.users)} users, {len(self.pairings)} pairings, "
                   f"{len(self.messages)} messages, {len(self.checkins)} checkins, "
                   f"{len(self.goals)} goals, {len(self.programmes)} programmes, "
                   f"{len(self.tips)} tips")
        
        return self