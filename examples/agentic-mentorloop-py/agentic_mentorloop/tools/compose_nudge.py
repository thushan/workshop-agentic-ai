import csv
import json
import os
import random
import re
from typing import Dict, List, Optional


class ComposeNudge:
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '../../../data')
        self.data_path = data_path
    
    def compose(self, engagement_data: str, tips: str, pair_id: Optional[str] = None) -> str:
        # Parse engagement data
        match = re.search(r'last_checkin_days=(\d+)', engagement_data)
        last_checkin_days = int(match.group(1)) if match else 14
        
        # Load data
        users = self._load_users()
        pairings = self._load_pairings()
        programmes = self._load_programmes()
        
        # Find a dormant pair
        if pair_id:
            target_pair = next((p for p in pairings if p['pair_id'] == pair_id), None)
        else:
            target_pair = random.choice(pairings)
        
        if not target_pair:
            return 'Error: No pairing found'
        
        mentee = next((u for u in users if u['user_id'] == target_pair['mentee_id']), None)
        mentor = next((u for u in users if u['user_id'] == target_pair['mentor_id']), None)
        programme = next((p for p in programmes if p['programme_id'] == target_pair['programme_id']), None)
        
        if not mentee or not mentor or not programme:
            return 'Error: Missing data for nudge composition'
        
        # Extract a tip suggestion
        tip_match = re.search(r'\) ([^|]+)', tips)
        tip_text = tip_match.group(1).strip() if tip_match else 'Stay connected with your mentor'
        
        # Compose nudge based on programme cadence
        is_overdue = last_checkin_days > programme['cadence_days']
        
        suggested_questions = [
            "What's one win from this week you'd like to share?",
            "What challenge could benefit from another perspective?",
            "How are you progressing on your current goals?",
            "What's one thing you'd like feedback on?"
        ]
        
        question = random.choice(suggested_questions)
        
        if is_overdue:
            body = (f"Hi {mentee['first_name']}, noticed it has been {last_checkin_days} days since your last check-in. "
                   f"{tip_text} Here's a gentle prompt you can use with {mentor['first_name']}: \"{question}\"")
        else:
            body = (f"Hi {mentee['first_name']}, great to see you're staying connected! "
                   f"Here's a conversation starter for your next session with {mentor['first_name']}: \"{question}\"")
        
        return f"""To: {mentee['first_name']}
Subject: Checking in on your {programme['name']} progress
Body: {body}"""
    
    def _load_users(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'users.csv')
        users = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
        return users
    
    def _load_pairings(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'pairings.csv')
        pairings = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pairings.append(row)
        return pairings
    
    def _load_programmes(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'programmes.json')
        with open(file_path, 'r') as f:
            return json.load(f)