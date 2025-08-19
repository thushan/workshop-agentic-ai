# Agentic MentorLoop - TypeScript

A minimal agent loop demonstration for MentorLoop scenarios with realistic fake data. This example shows a simple think → decide → act → reflect pattern using deterministic rules or LLM providers.

## Features

- **Deterministic brain**: Works offline with keyword-based decision making
- **LLM support**: OpenAI and Ollama providers for intelligent decisions
- **MentorLoop tools**:
  - `engagement_pulse`: Analyses check-in patterns and message balance
  - `mentor_tips`: Retrieves relevant tips using simple RAG (bag-of-words + cosine similarity)
  - `compose_nudge`: Creates supportive nudges for mentees based on engagement data

## Setup

### Prerequisites

- Node.js 16+ and npm
- (Optional) Ollama installed locally for LLM support
- (Optional) OpenAI API key for GPT support

### Installation

```bash
cd examples/agentic-mentorloop-ts
npm install
cp .env.example .env
```

### Configuration

Edit `.env` to configure providers:

```env
# Provider configuration
PROVIDER=ollama       # deterministic | ollama | openai
MODEL=llama3.1:8b     # Model name for LLM providers

# OpenAI configuration (when PROVIDER=openai)
OPENAI_API_KEY=sk-your-key-here

# Ollama configuration (when PROVIDER=ollama)
OLLAMA_HOST=http://localhost:11434
```

## Usage Examples

### Deterministic Offline (No LLM Required)

```bash
# Works without any external dependencies
unset PROVIDER OPENAI_API_KEY
npx ts-node src/cli.ts --prompt "please echo mentorloop onboarding nudge"

# Check engagement metrics
npx ts-node src/cli.ts --prompt "check engagement pulse for pairs"

# Get mentorship tips
npx ts-node src/cli.ts --prompt "tips for dormant mentees"
```

### TypeScript + Ollama

```bash
# First, ensure Ollama is running and pull the model
ollama pull llama3.1:8b

# Use Ollama for intelligent decisions
PROVIDER=ollama MODEL=llama3.1:8b npx ts-node src/cli.ts \
  --prompt "compose a supportive nudge for mentee dormant 21 days"

# Check for dormant mentees
PROVIDER=ollama npx ts-node src/cli.ts \
  --prompt "which mentees look dormant engagement"
```

### TypeScript + OpenAI

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-***

# Use GPT for decisions
PROVIDER=openai MODEL=gpt-4o-mini npx ts-node src/cli.ts \
  --prompt "which mentees look dormant engagement"

# Generate nudges with GPT
PROVIDER=openai npx ts-node src/cli.ts \
  --prompt "compose supportive nudge for inactive pair"
```

### Using NPM Scripts

The package includes convenient demo scripts:

```bash
# Run deterministic demo
npm run demo:deterministic

# Run Ollama demo (requires Ollama running)
npm run demo:ollama

# Run OpenAI demo (requires API key in .env)
npm run demo:openai
```

## Command Line Options

```
npx ts-node src/cli.ts [options]

Options:
  --prompt <text>      The prompt to process (required)
  --provider <type>    Provider type (deterministic|ollama|openai)
  --model <name>       Model name (default: llama3.1:8b)
  --pair-id <id>       Specific pair ID for operations
  --mentee-id <id>     Specific mentee ID for operations
  --debug              Enable debug output
  --help               Show help message
```

## Output Format

All commands return JSON with the agent's thinking process:

```json
{
  "thought": "Processing: \"check engagement pulse\"",
  "action": "USE:engagement_pulse",
  "observation": "sample=10 dormant=3 balance=balanced last_checkin_days=21",
  "reflection": "looks ok"
}
```

## Project Structure

```
agentic-mentorloop-ts/
├── src/
│   ├── cli.ts                    # Main entry point
│   ├── brain/
│   │   ├── deterministic.ts      # Rule-based decision making
│   │   ├── index.ts              # Brain orchestrator
│   │   └── providers/
│   │       ├── openai.ts         # OpenAI HTTP client
│   │       └── ollama.ts         # Ollama HTTP client
│   ├── tools/
│   │   ├── csvPulse.ts          # Engagement metrics analyser
│   │   ├── ragTips.ts           # Tip retrieval with RAG
│   │   └── composeNudge.ts      # Nudge message composer
│   └── rag/
│       └── tips.ts               # Simple RAG implementation
├── package.json
├── tsconfig.json
└── .env.example

../data/                          # Shared datasets (CSV and JSON)
├── users.csv                     # Mentors and mentees
├── pairings.csv                  # Mentor-mentee relationships
├── messages.csv                  # Communication history
├── checkins.csv                  # Regular check-in records
├── goals.csv                     # Mentorship goals
├── programmes.json               # Programme configurations
└── tips.json                     # Mentorship tips
```

## Troubleshooting

### Ollama Connection Issues

If you get connection errors with Ollama:

1. Check Ollama is running: `ollama list`
2. Verify the host in `.env` matches your setup
3. Ensure the model is pulled: `ollama pull llama3.1:8b`

### OpenAI API Errors

1. Verify your API key is correct in `.env`
2. Check you have credits/quota available
3. Ensure the model name is valid (e.g., `gpt-4o-mini`)

### TypeScript Compilation Errors

```bash
# Clean install dependencies
rm -rf node_modules package-lock.json
npm install

# Run TypeScript compiler check
npx tsc --noEmit
```

## Data Files

The `data/` directory contains realistic fake datasets:

- `users.csv`: Mentors and mentees with Australian timezones
- `pairings.csv`: Mentor-mentee relationships
- `messages.csv`: Communication history
- `checkins.csv`: Regular check-in records
- `goals.csv`: Mentorship goals and progress
- `programmes.json`: Programme configurations
- `tips.json`: Mentorship tips for various situations

## Notes

- Uses Australian English spelling throughout
- Designed for terminal/CLI demonstration
- Minimal dependencies (no LangChain/LlamaIndex)
- Works completely offline in deterministic mode
- Supports both local (Ollama) and cloud (OpenAI) LLMs