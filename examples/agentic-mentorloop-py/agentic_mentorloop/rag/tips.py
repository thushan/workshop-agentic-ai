import re
import math
from typing import Dict, List, Tuple, Optional


class TipsRAG:
    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'your', 'you', 'our'
        }
    
    def vectorise(self, text: str) -> Dict[str, int]:
        """Enhanced vectorisation with stop words and bigrams"""
        # Lowercase and strip punctuation
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = [w for w in clean_text.split() if w]
        vector = {}
        
        # Add unigrams (single words)
        for word in words:
            if len(word) > 2 and word not in self.stop_words:
                vector[word] = vector.get(word, 0) + 1
        
        # Add bigrams (two-word phrases)
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words and words[i + 1] not in self.stop_words:
                bigram = f"{words[i]}_{words[i + 1]}"
                vector[bigram] = vector.get(bigram, 0) + 1
        
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
        """Cosine similarity between two vectors"""
        all_words = set(vec1.keys()) | set(vec2.keys())
        dot_product = 0
        norm1 = 0
        norm2 = 0
        
        for word in all_words:
            v1 = vec1.get(word, 0)
            v2 = vec2.get(word, 0)
            dot_product += v1 * v2
            norm1 += v1 * v1
            norm2 += v2 * v2
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))
    
    def find_similar(self, query: str, documents: List[Dict], top_k: int = 2) -> List[Dict]:
        """Find most similar documents to query"""
        query_vector = self.vectorise(query)
        
        scores = []
        for doc in documents:
            doc_vector = self.vectorise(doc['text'])
            score = self.cosine_similarity(query_vector, doc_vector)
            scores.append({
                'id': doc['id'],
                'score': score,
                'text': doc['text'],
                'tags': doc.get('tags', [])
            })
        
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_k]