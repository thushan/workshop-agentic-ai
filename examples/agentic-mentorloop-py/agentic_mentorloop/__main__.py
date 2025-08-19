#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from typing import Dict, Optional
from dotenv import load_dotenv

from .brain.index import Brain
from .tools.csv_pulse import EngagementPulse
from .tools.rag_tips import MentorTips
from .tools.compose_nudge import ComposeNudge

# Load environment variables
load_dotenv()


async def main():
    # Parse command line arguments
    args = sys.argv[1:]
    prompt = ''
    provider = os.getenv('PROVIDER')
    model = os.getenv('MODEL')
    pair_id = None
    mentee_id = None
    debug = False
    limit = 5
    json_only = False
    compose = False
    
    i = 0
    while i < len(args):
        if args[i] == '--prompt':
            i += 1
            prompt = args[i] if i < len(args) else ''
        elif args[i] == '--provider':
            i += 1
            provider = args[i] if i < len(args) else None
        elif args[i] == '--model':
            i += 1
            model = args[i] if i < len(args) else None
        elif args[i] == '--pair-id':
            i += 1
            pair_id = args[i] if i < len(args) else None
        elif args[i] == '--mentee-id':
            i += 1
            mentee_id = args[i] if i < len(args) else None
        elif args[i] == '--debug':
            debug = True
        elif args[i] == '--limit':
            i += 1
            limit = int(args[i]) if i < len(args) else 5
        elif args[i] == '--json-only':
            json_only = True
        elif args[i] == '--compose':
            compose = True
        elif args[i] == '--help':
            print("""
Agentic MentorLoop - Minimal agent loop for mentorship scenarios

Usage: python -m agentic_mentorloop [options]

Options:
  --prompt <text>      The prompt to process
  --provider <type>    Provider type (deterministic|ollama|openai)
  --model <name>       Model name (default: llama3.1:8b)
  --pair-id <id>       Specific pair ID for operations
  --mentee-id <id>     Specific mentee ID for operations
  --limit <n>          Limit for list results (default: 5)
  --json-only          Output only the observation JSON
  --compose            Chain tips to compose_nudge for a complete nudge
  --debug              Enable debug output
  --help               Show this help message

Examples:
  python -m agentic_mentorloop --prompt "check engagement pulse"
  PROVIDER=ollama python -m agentic_mentorloop --prompt "dormant mentee tips"
  PROVIDER=openai MODEL=gpt-4o-mini python -m agentic_mentorloop --prompt "compose nudge"
""")
            sys.exit(0)
        i += 1
    
    if not prompt:
        print('Error: --prompt is required', file=sys.stderr)
        sys.exit(1)
    
    # Initialise brain
    brain = Brain(
        provider=provider,
        model=model,
        api_key=os.getenv('OPENAI_API_KEY'),
        ollama_host=os.getenv('OLLAMA_HOST'),
        debug=debug
    )
    
    # Agent loop: think → decide → act → reflect
    result = {
        'thought': f'Processing: "{prompt}"',
        'action': '',
        'observation': '',
        'reflection': 'needs improvement'
    }
    
    try:
        # Think and decide
        decision = await brain.think(prompt)
        result['action'] = decision.action
        
        # Act based on decision
        if decision.action.startswith('USE:'):
            tool_parts = decision.action[4:].split(':')
            tool = tool_parts[0]
            tool_mode = tool_parts[1] if len(tool_parts) > 1 else getattr(decision, 'mode', None)
            
            if tool == 'engagement_pulse':
                pulse = EngagementPulse()
                pulse_result = pulse.run({
                    'mode': tool_mode or 'summary',
                    'limit': limit,
                    'prompt': getattr(decision, 'prompt', prompt) or prompt
                })
                result['observation'] = pulse_result
                result['reflection'] = 'needs improvement' if pulse_result.get('type') == 'error' else 'looks ok'
            
            elif tool == 'mentor_tips':
                tips = MentorTips()
                tips_result = tips.retrieve(prompt)
                result['observation'] = tips_result
                result['reflection'] = 'needs improvement' if tips_result.get('type') == 'error' else 'looks ok'
                
                # Chain to compose_nudge if --compose flag is set
                if compose and tips_result.get('type') == 'tips' and tips_result.get('hits'):
                    pulse_for_compose = EngagementPulse()
                    engagement_data_obj = pulse_for_compose.run({'mode': 'summary'})
                    if engagement_data_obj.get('type') == 'summary':
                        engagement_data = f"sample={engagement_data_obj['sample']} dormant={engagement_data_obj['dormant']} balance={engagement_data_obj['balance']} last_checkin_days={engagement_data_obj['last_checkin_days']}"
                    else:
                        engagement_data = 'sample=0 dormant=0 balance=balanced last_checkin_days=0'
                    
                    # Format tips for compose_nudge (using top 1-2 tips)
                    top_tips = ' | '.join([f"({h['id']} {h['score']}) {h['text']}" for h in tips_result['hits'][:2]])
                    
                    nudge = ComposeNudge()
                    nudge_text = nudge.compose(engagement_data, top_tips, pair_id)
                    
                    # Parse nudge text into structured format
                    lines = nudge_text.split('\n')
                    subject_line = next((l for l in lines if l.startswith('Subject:')), None)
                    body_lines = [l for l in lines if l.startswith('Body:')]
                    
                    nudge_result = {
                        'type': 'nudge',
                        'subject': subject_line.replace('Subject: ', '') if subject_line else 'Mentorship update',
                        'body': body_lines[0].replace('Body: ', '') if body_lines else nudge_text
                    }
                    
                    # Add nudge to observation if composing
                    result['observation'] = {
                        'tips': tips_result,
                        'nudge': nudge_result
                    }
            
            elif tool == 'compose_nudge':
                # First get engagement data and tips
                pulse_for_nudge = EngagementPulse()
                engagement_data_obj = pulse_for_nudge.run({'mode': 'summary'})
                # Convert structured data back to string format for compose_nudge
                if engagement_data_obj.get('type') == 'summary':
                    engagement_data = f"sample={engagement_data_obj['sample']} dormant={engagement_data_obj['dormant']} balance={engagement_data_obj['balance']} last_checkin_days={engagement_data_obj['last_checkin_days']}"
                else:
                    engagement_data = 'sample=0 dormant=0 balance=balanced last_checkin_days=0'
                tips_for_nudge = MentorTips()
                tips_result = tips_for_nudge.retrieve(prompt)
                # Format tips as string for compose_nudge
                if tips_result.get('type') == 'tips' and tips_result.get('hits'):
                    tips_data = ' | '.join([f"({h['id']} {h['score']}) {h['text']}" for h in tips_result['hits'][:2]])
                else:
                    tips_data = 'No relevant tips found'
                
                nudge = ComposeNudge()
                result['observation'] = nudge.compose(engagement_data, tips_data, pair_id)
                result['reflection'] = 'looks ok'
            
            elif tool == 'echo':
                result['observation'] = f'Echo: {prompt}'
                result['reflection'] = 'looks ok'
            
            else:
                result['observation'] = f'Unknown tool: {tool}'
                result['reflection'] = 'needs improvement'
        
        elif decision.action.startswith('RESPOND:'):
            result['observation'] = decision.action[8:]
            result['reflection'] = 'looks ok'
        
        else:
            result['observation'] = decision.action
            result['reflection'] = 'looks ok'
    
    except Exception as e:
        result['observation'] = f'Error: {str(e)}'
        result['reflection'] = 'needs improvement'
    
    # Output JSON result
    if json_only and result['observation']:
        print(json.dumps(result['observation'], indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f'Fatal error: {e}', file=sys.stderr)
        sys.exit(1)