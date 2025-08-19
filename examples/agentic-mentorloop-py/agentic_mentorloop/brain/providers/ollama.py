import json
import requests
from typing import List, Dict
from ..deterministic import BrainDecision


class OllamaProvider:
    def __init__(self, host: str = 'http://localhost:11434', model: str = 'llama3.1:8b'):
        self.host = host.rstrip('/')
        self.model = model
        self.api_url = f'{self.host}/api/chat'
    
    def generate(self, messages: List[Dict[str, str]]) -> BrainDecision:
        import re
        last_message = messages[-1]['content'] if messages else ''
        list_pattern = re.compile(r'\b(which|who|list|show)\b', re.IGNORECASE)
        mode = 'list' if list_pattern.search(last_message) else 'summary'
        
        system_prompt = """You are an agent that decides which tool to use.
Return EXACTLY one of these responses:
- USE:engagement_pulse:summary (for engagement summary metrics)
- USE:engagement_pulse:list (for listing specific mentees)
- USE:mentor_tips (for getting mentorship advice)
- USE:echo (to echo back input)
- RESPOND:<your text> (for direct responses)

If the user asks "which", "who", "list", or "show" mentees, use USE:engagement_pulse:list
Otherwise for engagement checks, use USE:engagement_pulse:summary

Be concise and decisive."""
        
        full_messages = [
            {'role': 'system', 'content': system_prompt},
            *messages
        ]
        
        payload = {
            'model': self.model,
            'messages': full_messages,
            'stream': False,
            'options': {
                'temperature': 0.3,
                'num_predict': 100
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")
            
            data = response.json()
            if 'error' in data:
                raise Exception(f"Ollama API error: {data['error']}")
            
            content = data.get('message', {}).get('content', 'RESPOND:No response from model').strip()
            
            # Parse the action and add mode if it's engagement_pulse
            if 'USE:engagement_pulse' in content:
                inferred_mode = 'list' if ':list' in content else 'summary' if ':summary' in content else mode
                return BrainDecision(content, inferred_mode, last_message)
            else:
                return BrainDecision(content)
            
        except requests.exceptions.Timeout:
            raise Exception('Ollama request timed out')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Ollama request failed: {str(e)}')
        except Exception as e:
            if 'Ollama' in str(e):
                raise e
            raise Exception(f'Failed to parse Ollama response: {str(e)}')