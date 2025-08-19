import * as https from 'https';
import { BrainDecision } from '../deterministic';

export class OpenAIProvider {
  private apiKey: string;
  private model: string;

  constructor(apiKey: string, model: string = 'gpt-4o-mini') {
    this.apiKey = apiKey;
    this.model = model;
  }

  async generate(messages: Array<{role: string, content: string}>): Promise<BrainDecision> {
    const lastMessage = messages[messages.length - 1]?.content || '';
    const listPattern = /\b(which|who|list|show)\b/i;
    const mode = listPattern.test(lastMessage) ? 'list' : 'summary';
    
    const systemPrompt = `You are an agent that decides which tool to use.
Return EXACTLY one of these responses:
- USE:engagement_pulse:summary (for engagement summary metrics)
- USE:engagement_pulse:list (for listing specific mentees)
- USE:mentor_tips (for getting mentorship advice)
- USE:echo (to echo back input)
- RESPOND:<your text> (for direct responses)

If the user asks "which", "who", "list", or "show" mentees, use USE:engagement_pulse:list
Otherwise for engagement checks, use USE:engagement_pulse:summary

Be concise and decisive.`;

    const requestBody = JSON.stringify({
      model: this.model,
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages
      ],
      temperature: 0.3,
      max_tokens: 100
    });

    const options = {
      hostname: 'api.openai.com',
      port: 443,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Length': Buffer.byteLength(requestBody)
      },
      timeout: 30000
    };

    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            const response = JSON.parse(data);
            if (response.error) {
              reject(new Error(`OpenAI API error: ${response.error.message}`));
              return;
            }
            const content = response.choices[0].message.content.trim();
            
            // Parse the action and add mode if it's engagement_pulse
            if (content.includes('USE:engagement_pulse')) {
              const inferredMode = content.includes(':list') ? 'list' : 
                                   content.includes(':summary') ? 'summary' : mode;
              resolve({ action: content, mode: inferredMode, prompt: lastMessage });
            } else {
              resolve({ action: content });
            }
          } catch (error) {
            reject(new Error(`Failed to parse OpenAI response: ${error}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`OpenAI request failed: ${error.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('OpenAI request timed out'));
      });

      req.write(requestBody);
      req.end();
    });
  }
}