import sys
from typing import Optional
from .deterministic import DeterministicBrain, BrainDecision
from .providers.openai import OpenAIProvider
from .providers.ollama import OllamaProvider


class Brain:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None,
                 api_key: Optional[str] = None, ollama_host: Optional[str] = None,
                 debug: bool = False):
        self.provider = provider or 'deterministic'
        self.model = model or 'llama3.1:8b'
        self.api_key = api_key
        self.ollama_host = ollama_host or 'http://localhost:11434'
        self.debug = debug
    
    async def think(self, prompt: str) -> BrainDecision:
        if self.debug:
            print(f'[DEBUG] Provider: {self.provider}, Model: {self.model}', file=sys.stderr)
        
        try:
            if self.provider == 'openai':
                if not self.api_key:
                    raise Exception('OpenAI API key is required')
                openai = OpenAIProvider(self.api_key, self.model)
                return openai.generate([{'role': 'user', 'content': prompt}])
            
            elif self.provider == 'ollama':
                ollama = OllamaProvider(self.ollama_host, self.model)
                return ollama.generate([{'role': 'user', 'content': prompt}])
            
            else:  # deterministic
                deterministic = DeterministicBrain()
                return deterministic.decide(prompt)
                
        except Exception as e:
            # Return error as a decision for proper JSON output
            return BrainDecision(f'RESPOND:Error: {str(e)}')