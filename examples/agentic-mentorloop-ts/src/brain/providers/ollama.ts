import * as http from 'http';
import { BrainDecision } from '../deterministic';

export class OllamaProvider {
  private host: string;
  private model: string;

  constructor(host: string = 'http://localhost:11434', model: string = 'llama3.1:8b') {
    this.host = host.replace(/^https?:\/\//, '');
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
      stream: false,
      options: {
        temperature: 0.3,
        num_predict: 100
      }
    });

    const [hostname, port] = this.host.split(':');
    const options = {
      hostname: hostname || 'localhost',
      port: parseInt(port || '11434'),
      path: '/api/chat',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(requestBody)
      },
      timeout: 30000
    };

    return new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            const response = JSON.parse(data);
            if (response.error) {
              reject(new Error(`Ollama API error: ${response.error}`));
              return;
            }
            const content = response.message?.content?.trim() || 'RESPOND:No response from model';
            
            // Parse the action and add mode if it's engagement_pulse
            if (content.includes('USE:engagement_pulse')) {
              const inferredMode = content.includes(':list') ? 'list' : 
                                   content.includes(':summary') ? 'summary' : mode;
              resolve({ action: content, mode: inferredMode, prompt: lastMessage });
            } else {
              resolve({ action: content });
            }
          } catch (error) {
            reject(new Error(`Failed to parse Ollama response: ${error}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`Ollama request failed: ${error.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Ollama request timed out'));
      });

      req.write(requestBody);
      req.end();
    });
  }
}