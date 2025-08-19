import json
import requests
from typing import List, Dict
from ..deterministic import BrainDecision


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.openai.com/v1/chat/completions'
    
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
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'messages': full_messages,
            'temperature': 0.3,
            'max_tokens': 100
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Parse the action and add mode if it's engagement_pulse
            if 'USE:engagement_pulse' in content:
                inferred_mode = 'list' if ':list' in content else 'summary' if ':summary' in content else mode
                return BrainDecision(content, inferred_mode, last_message)
            else:
                return BrainDecision(content)
            
        except requests.exceptions.Timeout:
            raise Exception('OpenAI request timed out')
        except requests.exceptions.RequestException as e:
            raise Exception(f'OpenAI request failed: {str(e)}')
        except Exception as e:
            raise Exception(f'Failed to parse OpenAI response: {str(e)}')