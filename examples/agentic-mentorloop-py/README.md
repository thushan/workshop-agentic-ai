# Agentic MentorLoop - Python

A minimal agent loop demonstration for MentorLoop scenarios with realistic fake data. This example shows a simple think → decide → act → reflect pattern using deterministic rules or LLM providers.

## Features

- **Deterministic brain**: Works offline with keyword-based decision making
- **LLM support**: OpenAI and Ollama providers for intelligent decisions
- **MentorLoop tools**:
  - `csv_pulse`: Analyses check-in patterns and message balance
  - `rag_tips`: Retrieves relevant tips using simple RAG (bag-of-words + cosine similarity)
  - `compose_nudge`: Creates supportive nudges for mentees based on engagement data

## Setup

### Prerequisites

- Python 3.8+
- pip package manager
- (Optional) Ollama installed locally for LLM support
- (Optional) OpenAI API key for GPT support

### Installation

```bash
cd examples/agentic-mentorloop-py

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
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
python -m agentic_mentorloop --prompt "please echo mentorloop onboarding nudge"

# Check engagement metrics
python -m agentic_mentorloop --prompt "check engagement pulse for pairs"

# Get mentorship tips
python -m agentic_mentorloop --prompt "tips for dormant mentees"
```

### Python + pip + venv + Ollama

```bash
cd examples/agentic-mentorloop-py
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ensure Ollama is running and pull the model
ollama pull llama3.1:8b

# Use Ollama for intelligent decisions
PROVIDER=ollama MODEL=llama3.1:8b python -m agentic_mentorloop \
  --prompt "tip to reduce one sided conversations"

# Check for dormant mentees
PROVIDER=ollama python -m agentic_mentorloop \
  --prompt "compose supportive nudge for dormant mentee"
```

### Python + OpenAI

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Set your OpenAI API key
export OPENAI_API_KEY=sk-***

# Use GPT for decisions
PROVIDER=openai MODEL=gpt-4o-mini python -m agentic_mentorloop \
  --prompt "which mentees need engagement support"

# Generate nudges with GPT
PROVIDER=openai python -m agentic_mentorloop \
  --prompt "compose nudge for inactive mentorship pair"
```

## Command Line Options

```
python -m agentic_mentorloop [options]

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
agentic-mentorloop-py/
├── agentic_mentorloop/
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── deterministic.py      # Rule-based decision making
│   │   ├── index.py              # Brain orchestrator
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── openai.py         # OpenAI HTTP client
│   │       └── ollama.py         # Ollama HTTP client
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── csv_pulse.py         # Engagement metrics analyser
│   │   ├── rag_tips.py          # Tip retrieval with RAG
│   │   └── compose_nudge.py     # Nudge message composer
│   └── rag/
│       ├── __init__.py
│       └── tips.py               # Simple RAG implementation
├── requirements.txt
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

### Virtual Environment Issues

```bash
# Deactivate and recreate if needed
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Ollama Connection Issues

If you get connection errors with Ollama:

1. Check Ollama is running: `ollama list`
2. Verify the host in `.env` matches your setup
3. Ensure the model is pulled: `ollama pull llama3.1:8b`
4. Test connection: `curl http://localhost:11434/api/tags`

### OpenAI API Errors

1. Verify your API key is correct in `.env`
2. Check you have credits/quota available
3. Ensure the model name is valid (e.g., `gpt-4o-mini`)
4. Test with curl:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### Module Import Errors

```bash
# Ensure you're in the right directory
cd examples/agentic-mentorloop-py

# Run as a module, not a script
python -m agentic_mentorloop --help  # Correct
python agentic_mentorloop/__main__.py --help  # May fail
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

## Development

### Running Tests

```bash
# No external test framework required
# Test deterministic mode
python -m agentic_mentorloop --prompt "engagement pulse"

# Test each tool
python -m agentic_mentorloop --prompt "tips for one sided conversations"
python -m agentic_mentorloop --prompt "echo test message"
```

### Adding New Tools

1. Create a new file in `agentic_mentorloop/tools/`
2. Implement a class with a method that returns a string
3. Add the tool case in `__main__.py` under the action handling
4. Update the brain's decision logic if needed

## Notes

- Uses Australian English spelling throughout
- Designed for terminal/CLI demonstration
- Minimal dependencies (only `requests` and `python-dotenv`)
- Works completely offline in deterministic mode
- Supports both local (Ollama) and cloud (OpenAI) LLMs
- Async-ready architecture for future enhancements