# EDNA LangChain - Engagement Development Nudge Agent

Production-ready CLI application for detecting and addressing engagement issues in mentor-mentee relationships using LangChain, RAG and LLM evaluation.

## Features

- Detects mentor-mentee pairs at risk of disengagement
- Retrieves relevant mentoring tips using vector search (FAISS) or BM25 fallback
- Generates supportive nudges in Australian English
- Evaluates draft quality and duplication risk
- Supports OpenAI and Ollama providers

## Installation

```bash
cd examples/edna-py/edna-langchain

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file
cp .env.example .env
```

## Data Setup

This project uses the shared data files from `examples/data/`. No need to copy files - they're already available in the parent directory.

### Data Files Structure

The following files are expected in `examples/data/`:

**pairings.csv**
```csv
pair_id,mentor_id,mentee_id,programme_id,started_at
p001,m001,u001,prog001,2025-06-01T00:00:00Z
```

**users.csv**
```csv
user_id,role,email,timezone,first_name,joined_at
u001,mentee,priya@example.com,Australia/Melbourne,Priya,2025-05-01T00:00:00Z
m001,mentor,sarah@example.com,Australia/Sydney,Sarah,2025-04-01T00:00:00Z
```

**messages.csv**
```csv
pair_id,timestamp,author_role,channel,text
p001,2025-07-15T10:00:00Z,mentor,email,How are your goals progressing?
```

**checkins.csv**
```csv
pair_id,timestamp,mentee_score,mentor_score,notes
p001,2025-07-10T09:00:00Z,4,5,Good progress this week
```

**goals.csv**
```csv
pair_id,goal_id,title,status,updated_at
p001,g001,Complete project documentation,open,2025-07-01T00:00:00Z
```

**programmes.json**
```json
[
  {
    "programme_id": "prog001",
    "name": "Tech Leadership Programme",
    "cadence_days": 10,
    "success_markers": ["regular_checkins", "goal_progress"]
  }
]
```

**tips.json**
```json
[
  {
    "tip_id": "t1",
    "situation": "dormant",
    "text": "Consider scheduling a brief check-in to reconnect and realign on goals"
  }
]
```

## Configuration

### Setup Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# For Ollama (default):
#   PROVIDER=ollama
#   MODEL=llama3.2:3b
# For OpenAI:
#   PROVIDER=openai
#   MODEL=gpt-4o-mini
#   OPENAI_API_KEY=your-api-key
```

## Usage

Run from the `examples/edna-py/edna-langchain` directory:

### With Environment File (Recommended)

```bash
cd examples/edna-py/edna-langchain

# After configuring .env file
python -m edna.cli suggest --since-days 30 --limit 10
```

### With Environment Variables

#### OpenAI Provider

```bash
PROVIDER=openai MODEL=gpt-4o-mini OPENAI_API_KEY=sk-xxx \
python -m edna.cli suggest --since-days 30 --limit 10
```

#### Ollama Provider

```bash
# Start Ollama first
ollama serve

# Pull required models (one-time setup)
ollama pull llama3.2:3b
ollama pull nomic-embed-text  # Optional, for embeddings

# Run EDNA
PROVIDER=ollama MODEL=llama3.2:3b \
python -m edna.cli suggest --since-days 30 --limit 10
```

### Command Options

```bash
python -m edna.cli suggest [OPTIONS]

Options:
  --since-days INT          Filter pairs with activity in last N days (default: 30)
  --limit INT              Max suggestions to generate (default: 20)
  --channel CHANNEL        Override channel: email|in_app|slack
  --emit PATH             Output JSONL path (default: out/edna_suggestions.jsonl)
  --dry-run               Don't update sent log (default: true)
  --mark-as-sent          Mark suggestions as sent in log
  --verbose               Enable verbose logging
```

## Environment Variables

Configuration can be set via `.env` file or environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PROVIDER` | LLM provider | `openai` | `ollama`, `openai` |
| `MODEL` | Model to use | - | `llama3.2:3b`, `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key (required for OpenAI) | - | `sk-xxx` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://127.0.0.1:11434` | - |
| `EMBEDDING_MODEL` | Embedding model for Ollama | `nomic-embed-text` | `none` to use BM25 |

## Output

### Terminal Table
```
+----------+----------------+------------+-------------------+---------+
| Pair ID  | Classification | Confidence | Send Time         | Channel |
+----------+----------------+------------+-------------------+---------+
| p001     | dormant        | 0.78       | 2025-08-21 09:15  | email   |
| p002     | one_sided      | 0.72       | 2025-08-21 09:15  | in_app  |
+----------+----------------+------------+-------------------+---------+
```

### JSONL Output (out/edna_suggestions.jsonl)
```json
{
  "pair_id": "p001",
  "classification": "dormant",
  "confidence": 0.78,
  "explanations": ["last message 23 days ago vs cadence 10"],
  "suggested_channel": "email",
  "suggested_send_time_local": "2025-08-21T09:15:00+10:00",
  "timezone": "Australia/Melbourne",
  "nudge_draft": "Hi Priya — no rush here, just checking in...",
  "citations": [{"tip_id": "t1", "score": 0.73}],
  "safety_checks": {
    "tone_supportive": true,
    "no_private_data_leak": true,
    "not_duplicate_last_7d": true
  }
}
```

## Duplicate Prevention

The system maintains a `out/sent_log.jsonl` file when `--mark-as-sent` is used to prevent sending duplicate nudges within 7 days for the same pair and classification.

## Fallback to BM25

If embeddings are unavailable (e.g., Ollama embedding model not installed), the system automatically falls back to BM25 keyword search for tip retrieval.

## Testing

```bash
cd examples/edna-py/edna-langchain
pytest -q
```

Tests run offline without LLM calls, using synthetic data to verify:
- Feature computation accuracy
- Classification rule priority
- Time heuristics and weekend skipping

## Classifications

1. **dormant** - No recent activity beyond expected cadence
2. **blocked_goal** - Goals are blocked or stale
3. **one_sided** - Mentor doing most of the talking
4. **celebrate_wins** - High checkin scores or completed goals

## Architecture

- **LangChain** for LLM orchestration and prompts
- **FAISS** for vector similarity search
- **BM25** as fallback retriever
- **Pydantic** for type validation
- **Tabulate** for terminal output