import { DeterministicBrain, BrainDecision } from './deterministic';
import { OpenAIProvider } from './providers/openai';
import { OllamaProvider } from './providers/ollama';

export class Brain {
  private provider: string;
  private model: string;
  private apiKey?: string;
  private ollamaHost: string;
  private debug: boolean;

  constructor(config: {
    provider?: string;
    model?: string;
    apiKey?: string;
    ollamaHost?: string;
    debug?: boolean;
  }) {
    this.provider = config.provider || 'deterministic';
    this.model = config.model || 'llama3.1:8b';
    this.apiKey = config.apiKey;
    this.ollamaHost = config.ollamaHost || 'http://localhost:11434';
    this.debug = config.debug || false;
  }

  async think(prompt: string): Promise<BrainDecision> {
    if (this.debug) {
      console.error(`[DEBUG] Provider: ${this.provider}, Model: ${this.model}`);
    }

    try {
      switch (this.provider) {
        case 'openai':
          if (!this.apiKey) {
            throw new Error('OpenAI API key is required');
          }
          const openai = new OpenAIProvider(this.apiKey, this.model);
          return await openai.generate([{ role: 'user', content: prompt }]);

        case 'ollama':
          const ollama = new OllamaProvider(this.ollamaHost, this.model);
          return await ollama.generate([{ role: 'user', content: prompt }]);

        case 'deterministic':
        default:
          const deterministic = new DeterministicBrain();
          return deterministic.decide(prompt);
      }
    } catch (error) {
      // Return error as a decision for proper JSON output
      return {
        action: `RESPOND:Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }
}