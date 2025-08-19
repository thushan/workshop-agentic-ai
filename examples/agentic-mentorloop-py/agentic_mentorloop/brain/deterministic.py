import re

class BrainDecision:
    def __init__(self, action: str, mode: str = None, prompt: str = None):
        self.action = action
        self.mode = mode
        self.prompt = prompt


class DeterministicBrain:
    def decide(self, prompt: str) -> BrainDecision:
        lower_prompt = prompt.lower()
        
        # Check for specific keywords and return appropriate actions
        if 'engagement' in lower_prompt or 'pulse' in lower_prompt or 'checkin' in lower_prompt:
            # Infer mode based on list-related keywords
            list_pattern = re.compile(r'\b(which|who|list|show)\b', re.IGNORECASE)
            mode = 'list' if list_pattern.search(prompt) else 'summary'
            return BrainDecision(f'USE:engagement_pulse:{mode}', mode, prompt)
        
        if 'dormant' in lower_prompt or 'inactive' in lower_prompt:
            if 'tip' in lower_prompt or 'advice' in lower_prompt:
                return BrainDecision('USE:mentor_tips')
            # Infer mode for dormant checks
            list_pattern = re.compile(r'\b(which|who|list|show)\b', re.IGNORECASE)
            mode = 'list' if list_pattern.search(prompt) else 'summary'
            return BrainDecision(f'USE:engagement_pulse:{mode}', mode, prompt)
        
        if 'one sided' in lower_prompt or 'one-sided' in lower_prompt or 'imbalance' in lower_prompt:
            return BrainDecision('USE:mentor_tips')
        
        if 'tip' in lower_prompt or 'advice' in lower_prompt or 'suggestion' in lower_prompt:
            return BrainDecision('USE:mentor_tips')
        
        if 'echo' in lower_prompt:
            return BrainDecision('USE:echo')
        
        if 'debug' in lower_prompt:
            return BrainDecision('RESPOND:Debug mode - all systems operational')
        
        # Default response for unmatched patterns
        return BrainDecision(f'RESPOND:I understand you\'re asking about "{prompt}". Let me help with that.')