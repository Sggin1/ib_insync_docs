# IB_INSYNC Documentation Deduplication

**Fast, cheap, AI-powered deduplication using OpenRouter DeepSeek**

This tool extracts code examples from ib_insync markdown documentation, identifies duplicates, and intelligently merges them using DeepSeek AI to create clean, deduplicated documentation.

## Why This Approach?

✅ **Super cheap** - ~$0.04 for complete processing (DeepSeek pricing)
✅ **Fast** - 15-25 minutes for full docs
✅ **No local setup** - Uses cloud API (no Ollama, no GPU needed)
✅ **Great for code** - DeepSeek specialized in code understanding
✅ **Simple config** - Just need API key

Can upgrade to Claude 3.5 Sonnet for ~$1.57 if DeepSeek results aren't good enough.

## Quick Start

### 1. Get OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up for free account
3. Go to https://openrouter.ai/keys
4. Create new API key
5. Copy the key (starts with `sk-or-v1-...`)

### 2. Install Dependencies

```bash
cd dedup_new
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Add this line to `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 4. Run Deduplication

```bash
python scripts/run_dedup.py
```

That's it! The script will:
1. Extract all code examples from `../docs/*.md` files
2. Find duplicate/similar examples
3. Use DeepSeek AI to intelligently merge duplicates
4. Generate clean output in `outputs/` directory

## Configuration

Edit `config.yaml` to customize:

### Switch AI Models

```yaml
ai:
  openrouter:
    # Option 1: DeepSeek R1 (cheapest, excellent for code)
    model: deepseek/deepseek-r1

    # Option 2: Claude 3.5 Sonnet (best quality, more expensive)
    # model: anthropic/claude-3.5-sonnet

    # Option 3: DeepSeek Coder (older, still good)
    # model: deepseek/deepseek-coder
```

### Adjust Similarity Threshold

```yaml
merging:
  # How similar examples need to be to merge (0-1)
  # 0.85 = 85% similar
  similarity_threshold: 0.85  # Lower = more aggressive merging
```

### Development Mode (Test on Small Subset)

```yaml
development:
  enabled: true        # Set to true for testing
  max_files: 2         # Only process 2 files
  max_examples: 20     # Only process 20 examples
```

## Output Files

After running, you'll get:

```
outputs/
├── 1_extracted/
│   └── examples.json           # All extracted examples with metadata
├── 2_merged/
│   └── merged_examples.json    # Deduplicated examples
└── 3_final/
    ├── DEDUPLICATION_REPORT.md      # Human-readable report
    └── ib_insync_deduplicated.md    # Clean deduplicated docs
```

### Main Output: `ib_insync_deduplicated.md`

This is your final deduplicated documentation organized by topic with all redundancy removed.

### Deduplication Report

Shows:
- Original vs. deduplicated example counts
- Cost breakdown (tokens, pricing)
- Top merged examples with sources
- Processing statistics

## Cost Estimates

Based on ~7,000 lines of ib_insync docs:

| Model | Estimated Cost | Quality | Speed |
|-------|---------------|---------|-------|
| DeepSeek R1 | $0.04 | Excellent | Fast (15-25 min) |
| DeepSeek Coder | $0.02 | Very Good | Fast (15-25 min) |
| Claude 3.5 Sonnet | $1.57 | Best | Fast (15-25 min) |

**Recommendation:** Start with DeepSeek R1. Upgrade to Claude if needed.

## How It Works

### Step 1: Extraction

- Parses all `*.md` files in `../docs/`
- Extracts code blocks with surrounding context
- Captures metadata (source file, line number, heading, tags)
- Auto-detects tags from code patterns (connection, order, data, etc.)

### Step 2: Clustering

- Normalizes code (removes whitespace, comments for comparison)
- Calculates similarity using RapidFuzz string matching
- Groups similar examples into clusters (default: 85% threshold)
- Single examples (no duplicates) kept as-is

### Step 3: AI Merging

For each cluster:
- Sends all variants to DeepSeek AI
- AI identifies best canonical version
- AI creates comprehensive description covering all variations
- AI notes important differences between variants
- Returns merged example with metadata

### Step 4: Report Generation

- Generates JSON outputs for programmatic use
- Creates markdown report for human review
- Organizes deduplicated docs by topic
- Tracks costs and statistics

## Troubleshooting

### "OPENROUTER_API_KEY not found"

Make sure you:
1. Created `.env` file (copy from `.env.example`)
2. Added your API key to `.env`
3. Running from `dedup_new/` directory

### "Rate limit exceeded"

OpenRouter has rate limits. Adjust in `config.yaml`:

```yaml
ai:
  openrouter:
    requests_per_minute: 10  # Lower this
    concurrent_requests: 1    # Lower this
```

### "Out of budget"

Increase max budget in `config.yaml`:

```yaml
ai:
  openrouter:
    max_budget: 10.00  # Increase safety limit
```

### Testing Before Full Run

Enable development mode to test on small subset:

```yaml
development:
  enabled: true
  max_files: 1
  max_examples: 10
```

This lets you verify setup without spending credits.

## Project Structure

```
dedup_new/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration
├── .env.example           # API key template
├── .env                   # Your API key (gitignored)
│
├── src/                   # Source code
│   ├── models.py          # Pydantic data models
│   ├── extractor.py       # Markdown extraction
│   ├── ai_client.py       # OpenRouter API client
│   └── deduplicator.py    # Deduplication logic
│
├── scripts/               # Runnable scripts
│   └── run_dedup.py       # Main pipeline script
│
└── outputs/               # Generated files (gitignored)
    ├── 1_extracted/
    ├── 2_merged/
    └── 3_final/
```

## Next Steps

After deduplication, the clean examples will be used to:
1. Train an AI agent for ib_insync testing
2. Generate comprehensive test suites
3. Create interactive documentation
4. Build RAG-powered Q&A system

## Support

Issues or questions? Check:
- OpenRouter docs: https://openrouter.ai/docs
- DeepSeek model card: https://openrouter.ai/models/deepseek/deepseek-r1
- This README

## License

MIT
