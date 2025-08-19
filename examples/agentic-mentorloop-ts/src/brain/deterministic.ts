export interface BrainDecision {
  action: string;
  mode?: 'summary' | 'list';
  prompt?: string;
}

export class DeterministicBrain {
  decide(prompt: string): BrainDecision {
    const lowerPrompt = prompt.toLowerCase();
    
    // Check for specific keywords and return appropriate actions
    if (lowerPrompt.includes('engagement') || lowerPrompt.includes('pulse') || lowerPrompt.includes('checkin')) {
      // Infer mode based on list-related keywords
      const listPattern = /\b(which|who|list|show)\b/i;
      const mode = listPattern.test(prompt) ? 'list' : 'summary';
      return { action: `USE:engagement_pulse:${mode}`, mode, prompt };
    }
    
    if (lowerPrompt.includes('dormant') || lowerPrompt.includes('inactive')) {
      if (lowerPrompt.includes('tip') || lowerPrompt.includes('advice')) {
        return { action: 'USE:mentor_tips' };
      }
      // Infer mode for dormant checks
      const listPattern = /\b(which|who|list|show)\b/i;
      const mode = listPattern.test(prompt) ? 'list' : 'summary';
      return { action: `USE:engagement_pulse:${mode}`, mode, prompt };
    }
    
    if (lowerPrompt.includes('one sided') || lowerPrompt.includes('one-sided') || lowerPrompt.includes('imbalance')) {
      return { action: 'USE:mentor_tips' };
    }
    
    if (lowerPrompt.includes('tip') || lowerPrompt.includes('advice') || lowerPrompt.includes('suggestion')) {
      return { action: 'USE:mentor_tips' };
    }
    
    if (lowerPrompt.includes('echo')) {
      return { action: 'USE:echo' };
    }
    
    if (lowerPrompt.includes('debug')) {
      return { action: 'RESPOND:Debug mode - all systems operational' };
    }
    
    // Default response for unmatched patterns
    return { action: `RESPOND:I understand you're asking about "${prompt}". Let me help with that.` };
  }
}