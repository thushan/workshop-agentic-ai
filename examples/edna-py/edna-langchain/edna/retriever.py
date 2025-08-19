"""RAG retriever for mentoring tips."""

import logging
from typing import List, Optional, Dict
from pathlib import Path
import numpy as np

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.embeddings.base import Embeddings

from .types import Tip, Citation

logger = logging.getLogger(__name__)


class TipsRetriever:
    """Retriever for mentoring tips using vector search or BM25 fallback."""
    
    def __init__(self, tips: List[Tip], embeddings: Optional[Embeddings] = None):
        self.tips = tips
        self.embeddings = embeddings
        self.vectorstore = None
        self.bm25_retriever = None
        self.tip_id_map = {tip.tip_id: tip for tip in tips}
        
        # Create documents from tips
        self.documents = [
            Document(
                page_content=tip.text,
                metadata={"tip_id": tip.tip_id, "situation": tip.situation}
            )
            for tip in tips
        ]
        
        # Initialize retriever based on available embeddings
        if embeddings:
            self._init_vector_store()
        else:
            self._init_bm25()
    
    def _init_vector_store(self):
        """Initialize FAISS vector store."""
        try:
            if self.documents:
                self.vectorstore = FAISS.from_documents(
                    self.documents, 
                    self.embeddings
                )
                logger.info(f"Initialized FAISS vector store with {len(self.documents)} tips")
        except Exception as e:
            logger.warning(f"Failed to initialize vector store, falling back to BM25: {e}")
            self._init_bm25()
    
    def _init_bm25(self):
        """Initialize BM25 retriever as fallback."""
        if self.documents:
            self.bm25_retriever = BM25Retriever.from_documents(self.documents)
            self.bm25_retriever.k = 3
            logger.info(f"Initialized BM25 retriever with {len(self.documents)} tips")
    
    def search(
        self, 
        classification: str, 
        explanations: List[str], 
        top_k: int = 3
    ) -> List[Citation]:
        """Search for relevant tips based on classification and explanations."""
        
        # Build query
        query = f"{classification} {' '.join(explanations)}"
        
        # Perform search
        results = []
        if self.vectorstore:
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    query, 
                    k=top_k
                )
                results = [
                    Citation(
                        tip_id=doc.metadata["tip_id"],
                        score=float(1 / (1 + score))  # Convert distance to similarity
                    )
                    for doc, score in docs_with_scores
                ]
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to BM25: {e}")
        
        # Fallback to BM25 if vector search failed or unavailable
        if not results and self.bm25_retriever:
            docs = self.bm25_retriever.get_relevant_documents(query)[:top_k]
            # BM25 doesn't provide scores, so we create synthetic ones
            results = [
                Citation(
                    tip_id=doc.metadata["tip_id"],
                    score=0.5 + (0.3 * (1 - i / top_k))  # Synthetic decreasing scores
                )
                for i, doc in enumerate(docs)
            ]
        
        # Filter by situation if matches classification
        situation_map = {
            "dormant": "dormant",
            "blocked_goal": "blocked_goal",
            "one_sided": "one_sided",
            "celebrate_wins": "celebrate_wins"
        }
        
        if classification in situation_map:
            target_situation = situation_map[classification]
            # Boost scores for matching situations
            for citation in results:
                tip = self.tip_id_map.get(citation.tip_id)
                if tip and tip.situation == target_situation:
                    citation.score = min(1.0, citation.score * 1.2)
        
        # Sort by score and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]