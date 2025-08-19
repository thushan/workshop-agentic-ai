import json
import os
import re
from typing import List, Dict, Union
from ..rag.tips import TipsRAG


class MentorTips:
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '../../../data')
        self.data_path = data_path
        self.rag = TipsRAG()
    
    def retrieve(self, query: str) -> Dict:
        try:
            tips = self._load_tips()
            documents = [
                {
                    'id': tip['tip_id'],
                    'text': f"{tip['situation']} {tip['text']}",
                    'tags': re.split(r'[,_\s]+', tip['situation'])
                }
                for tip in tips
            ]
            
            results = self.rag.find_similar(query, documents, 2)
            
            if not results:
                return {
                    'type': 'tips',
                    'hits': []
                }
            
            # Map results to structured format
            hits = []
            for r in results:
                tip = next(t for t in tips if t['tip_id'] == r['id'])
                hits.append({
                    'id': r['id'],
                    'score': round(r['score'], 2),
                    'text': tip['text'],
                    'tags': [tag for tag in r.get('tags', []) if tag]
                })
            
            return {
                'type': 'tips',
                'hits': hits
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': str(e),
                'hint': 'Check that tips.json exists and is properly formatted'
            }
    
    def _load_tips(self) -> List[Dict]:
        file_path = os.path.join(self.data_path, 'tips.json')
        with open(file_path, 'r') as f:
            return json.load(f)