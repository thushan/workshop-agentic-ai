"""LLM provider adapter for OpenAI and Ollama."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.chat_models.base import BaseChatModel

logger = logging.getLogger(__name__)


def get_chat_model() -> Optional[BaseChatModel]:
    """Get chat model based on environment configuration."""
    
    provider = os.getenv("PROVIDER", "openai").lower()
    model = os.getenv("MODEL")
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            return None
        
        model = model or "gpt-4o-mini"
        try:
            chat_model = ChatOpenAI(
                model=model,
                temperature=0.7,
                openai_api_key=api_key
            )
            logger.info(f"Using OpenAI model: {model}")
            return chat_model
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI model: {e}")
            return None
    
    elif provider == "ollama":
        model = model or "llama3.1:8b"
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        try:
            chat_model = ChatOllama(
                model=model,
                base_url=base_url,
                temperature=0.7
            )
            logger.info(f"Using Ollama model: {model} at {base_url}")
            return chat_model
        except Exception as e:
            logger.error(f"Failed to initialize Ollama model: {e}")
            return None
    
    else:
        logger.error(f"Unknown provider: {provider}")
        return None


def get_embedding() -> Optional[Embeddings]:
    """Get embedding model based on environment configuration."""
    
    provider = os.getenv("PROVIDER", "openai").lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, falling back to BM25")
            return None
        
        try:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
            logger.info("Using OpenAI embeddings: text-embedding-3-small")
            return embeddings
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
            return None
    
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        
        try:
            embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url=base_url
            )
            logger.info(f"Using Ollama embeddings: {embedding_model}")
            return embeddings
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama embeddings, falling back to BM25: {e}")
            return None
    
    else:
        logger.warning(f"Unknown provider: {provider}, falling back to BM25")
        return None