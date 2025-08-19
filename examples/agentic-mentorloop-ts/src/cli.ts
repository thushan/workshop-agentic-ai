#!/usr/bin/env node
import * as dotenv from 'dotenv';
import { Brain } from './brain';
import { EngagementPulse } from './tools/csvPulse';
import { MentorTips } from './tools/ragTips';
import { ComposeNudge } from './tools/composeNudge';

// Load environment variables
dotenv.config();

interface AgentResult {
  thought: string;
  action: string;
  observation: any;
  reflection: string;
}

async function main() {
  // Parse command line arguments
  const args = process.argv.slice(2);
  let prompt = '';
  let provider = process.env.PROVIDER;
  let model = process.env.MODEL;
  let pairId: string | undefined;
  let menteeId: string | undefined;
  let debug = false;
  let limit = 5;
  let jsonOnly = false;
  let compose = false;

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--prompt':
        prompt = args[++i] || '';
        break;
      case '--provider':
        provider = args[++i];
        break;
      case '--model':
        model = args[++i];
        break;
      case '--pair-id':
        pairId = args[++i];
        break;
      case '--mentee-id':
        menteeId = args[++i];
        break;
      case '--debug':
        debug = true;
        break;
      case '--limit':
        limit = parseInt(args[++i] || '5');
        break;
      case '--json-only':
        jsonOnly = true;
        break;
      case '--compose':
        compose = true;
        break;
      case '--help':
        console.log(`
Agentic MentorLoop - Minimal agent loop for mentorship scenarios

Usage: npx ts-node src/cli.ts [options]

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
  npx ts-node src/cli.ts --prompt "check engagement pulse"
  PROVIDER=ollama npx ts-node src/cli.ts --prompt "dormant mentee tips"
  PROVIDER=openai MODEL=gpt-4o-mini npx ts-node src/cli.ts --prompt "compose nudge"
`);
        process.exit(0);
    }
  }

  if (!prompt) {
    console.error('Error: --prompt is required');
    process.exit(1);
  }

  // Initialise brain
  const brain = new Brain({
    provider,
    model,
    apiKey: process.env.OPENAI_API_KEY,
    ollamaHost: process.env.OLLAMA_HOST,
    debug
  });

  // Agent loop: think → decide → act → reflect
  const result: AgentResult = {
    thought: `Processing: "${prompt}"`,
    action: '',
    observation: null,
    reflection: 'needs improvement'
  };

  try {
    // Think and decide
    const decision = await brain.think(prompt);
    result.action = decision.action;

    // Act based on decision
    if (decision.action.startsWith('USE:')) {
      const toolParts = decision.action.substring(4).split(':');
      const tool = toolParts[0];
      const toolMode = toolParts[1] || decision.mode;
      
      switch (tool) {
        case 'engagement_pulse':
          const pulse = new EngagementPulse();
          const pulseResult = pulse.run({
            mode: toolMode as 'summary' | 'list',
            limit,
            prompt: decision.prompt || prompt
          });
          result.observation = pulseResult;
          result.reflection = pulseResult.type === 'error' ? 'needs improvement' : 'looks ok';
          break;
          
        case 'mentor_tips':
          const tips = new MentorTips();
          const tipsResult = tips.retrieve(prompt);
          result.observation = tipsResult;
          result.reflection = tipsResult.type === 'error' ? 'needs improvement' : 'looks ok';
          
          // Chain to compose_nudge if --compose flag is set
          if (compose && tipsResult.type === 'tips' && tipsResult.hits.length > 0) {
            const pulseForCompose = new EngagementPulse();
            const engagementDataObj = pulseForCompose.run({ mode: 'summary' });
            const engagementData = engagementDataObj.type === 'summary' 
              ? `sample=${engagementDataObj.sample} dormant=${engagementDataObj.dormant} balance=${engagementDataObj.balance} last_checkin_days=${engagementDataObj.last_checkin_days}`
              : 'sample=0 dormant=0 balance=balanced last_checkin_days=0';
            
            // Format tips for compose_nudge (using top 1-2 tips)
            const topTips = tipsResult.hits.slice(0, 2).map(h => `(${h.id} ${h.score}) ${h.text}`).join(' | ');
            
            const nudge = new ComposeNudge();
            const nudgeText = nudge.compose(engagementData, topTips, pairId);
            
            // Parse nudge text into structured format
            const lines = nudgeText.split('\n');
            const subjectLine = lines.find(l => l.startsWith('Subject:'));
            const bodyLines = lines.filter(l => l.startsWith('Body:'));
            
            const nudgeResult = {
              type: 'nudge',
              subject: subjectLine ? subjectLine.replace('Subject: ', '') : 'Mentorship update',
              body: bodyLines.length > 0 ? bodyLines[0].replace('Body: ', '') : nudgeText
            };
            
            // Add nudge to observation if composing
            result.observation = {
              tips: tipsResult,
              nudge: nudgeResult
            };
          }
          break;
          
        case 'compose_nudge':
          // First get engagement data and tips
          const pulseForNudge = new EngagementPulse();
          const engagementDataObj = pulseForNudge.run({ mode: 'summary' });
          // Convert structured data back to string format for compose_nudge
          const engagementData = engagementDataObj.type === 'summary' 
            ? `sample=${engagementDataObj.sample} dormant=${engagementDataObj.dormant} balance=${engagementDataObj.balance} last_checkin_days=${engagementDataObj.last_checkin_days}`
            : 'sample=0 dormant=0 balance=balanced last_checkin_days=0';
          const tipsForNudge = new MentorTips();
          const tipsDataObj = tipsForNudge.retrieve(prompt);
          
          // Format tips as string for compose_nudge
          let tipsDataStr = 'No relevant tips found';
          if (tipsDataObj.type === 'tips' && tipsDataObj.hits.length > 0) {
            tipsDataStr = tipsDataObj.hits.slice(0, 2).map(h => `(${h.id} ${h.score}) ${h.text}`).join(' | ');
          }
          
          const nudge = new ComposeNudge();
          result.observation = nudge.compose(engagementData, tipsDataStr, pairId);
          result.reflection = 'looks ok';
          break;
          
        case 'echo':
          result.observation = `Echo: ${prompt}`;
          result.reflection = 'looks ok';
          break;
          
        default:
          result.observation = `Unknown tool: ${tool}`;
          result.reflection = 'needs improvement';
      }
    } else if (decision.action.startsWith('RESPOND:')) {
      result.observation = decision.action.substring(8);
      result.reflection = 'looks ok';
    } else {
      result.observation = decision.action;
      result.reflection = 'looks ok';
    }
  } catch (error) {
    result.observation = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
    result.reflection = 'needs improvement';
  }

  // Output JSON result
  if (jsonOnly && result.observation) {
    console.log(JSON.stringify(result.observation, null, 2));
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

// Run the CLI
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});