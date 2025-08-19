"""Configuration management for EDNA."""

import os
import logging
from pathlib import Path
from typing import Optional

# Setup logging
def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Default paths - use shared examples/data directory
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "out"

# Environment configuration
class Config:
    """Configuration container."""
    
    def __init__(self):
        self.provider = os.getenv("PROVIDER", "openai")
        self.model = os.getenv("MODEL")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        
        self.data_dir = DEFAULT_DATA_DIR
        self.output_dir = DEFAULT_OUTPUT_DIR
    
    def validate(self) -> bool:
        """Validate configuration."""
        if self.provider == "openai" and not self.openai_api_key:
            logging.error("OPENAI_API_KEY required for OpenAI provider")
            return False
        return True