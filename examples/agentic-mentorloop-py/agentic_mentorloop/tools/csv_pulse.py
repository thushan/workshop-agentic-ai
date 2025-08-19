import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Union


class EngagementPulse:
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '../../../data')
        self.data_path = data_path
    
    def run(self, options: Optional[Dict] = None) -> Dict:
        try:
            mode = options.get('mode', 'summary') if options else 'summary'
            limit = options.get('limit', 5) if options else 5
            
            checkins = self._load_checkins()
            messages = self._load_messages()
            users = self._load_users()
            pairings = self._load_pairings()
            
            now = datetime.now()
            pair_stats = {}
            
            # Analyse checkins
            for checkin in checkins:
                pair_id = checkin['pair_id']
                checkin_date = datetime.fromisoformat(checkin['timestamp'].replace('Z', '+00:00'))
                
                if pair_id not in pair_stats or checkin_date > pair_stats[pair_id]['last_checkin']:
                    days_since = (now - checkin_date.replace(tzinfo=None)).days
                    pair_stats[pair_id] = {
                        'last_checkin': checkin_date,
                        'balance': 'balanced',
                        'days_since': days_since
                    }
            
            # Analyse message balance for last 50 messages per pair
            pair_messages = {}
            for msg in messages:
                pair_id = msg['pair_id']
                if pair_id not in pair_messages:
                    pair_messages[pair_id] = []
                pair_messages[pair_id].append(msg)
            
            for pair_id, msgs in pair_messages.items():
                recent_messages = msgs[-50:]
                mentor_count = sum(1 for m in recent_messages if m['author_role'] == 'mentor')
                mentee_count = sum(1 for m in recent_messages if m['author_role'] == 'mentee')
                
                balance = 'balanced'
                if mentor_count > mentee_count * 1.5:
                    balance = 'mentor_heavy'
                elif mentee_count > mentor_count * 1.5:
                    balance = 'mentee_heavy'
                
                if pair_id in pair_stats:
                    pair_stats[pair_id]['balance'] = balance
            
            # Find dormant pairs (> 14 days)
            dormant_pairs = []
            for pair_id, stats in pair_stats.items():
                if stats['days_since'] > 14:
                    dormant_pairs.append({'pair_id': pair_id, 'days_since': stats['days_since']})
            
            if mode == 'list':
                # Sort dormant pairs by days since last checkin (descending)
                dormant_pairs.sort(key=lambda x: x['days_since'], reverse=True)
                
                # Map to mentee information
                dormant_mentees = []
                for item in dormant_pairs[:limit]:
                    pair_id = item['pair_id']
                    days_since = item['days_since']
                    
                    pairing = next((p for p in pairings if p['pair_id'] == pair_id), None)
                    if not pairing:
                        dormant_mentees.append({
                            'mentee_id': 'unknown',
                            'first_name': 'Unknown',
                            'pair_id': pair_id,
                            'last_checkin_days': days_since
                        })
                        continue
                    
                    mentee = next((u for u in users if u['user_id'] == pairing['mentee_id']), None)
                    dormant_mentees.append({
                        'mentee_id': pairing['mentee_id'],
                        'first_name': mentee['first_name'] if mentee else 'Unknown',
                        'pair_id': pair_id,
                        'last_checkin_days': days_since
                    })
                
                return {
                    'type': 'list',
                    'dormant_count': len(dormant_pairs),
                    'mentees': dormant_mentees
                }
            else:
                # Summary mode
                max_days = 0
                for stats in pair_stats.values():
                    if stats['days_since'] > max_days:
                        max_days = stats['days_since']
                
                # Get overall balance
                balances = [s['balance'] for s in pair_stats.values()]
                mentor_heavy = sum(1 for b in balances if b == 'mentor_heavy')
                mentee_heavy = sum(1 for b in balances if b == 'mentee_heavy')
                
                if mentor_heavy > len(balances) / 2:
                    overall_balance = 'mentor_heavy'
                elif mentee_heavy > len(balances) / 2:
                    overall_balance = 'mentee_heavy'
                else:
                    overall_balance = 'balanced'
                
                return {
                    'type': 'summary',
                    'sample': len(pair_stats),
                    'dormant': len(dormant_pairs),
                    'balance': overall_balance,
                    'last_checkin_days': max_days
                }
        except Exception as e:
            return {
                'type': 'error',
                'message': str(e),
                'hint': 'Check that data files exist and are properly formatted'
            }
    
    def _load_checkins(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'checkins.csv')
        checkins = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                checkins.append(row)
        return checkins
    
    def _load_messages(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'messages.csv')
        messages = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                messages.append(row)
        return messages
    
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