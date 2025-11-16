# Quick Start Guide - IB_INSYNC Deduplication

Get up and running in 5 minutes!

## Step 1: Get OpenRouter API Key (2 minutes)

1. Visit https://openrouter.ai/
2. Click "Sign Up" (free)
3. After signing in, go to https://openrouter.ai/keys
4. Click "Create Key"
5. Copy the key (starts with `sk-or-v1-...`)

**Cost:** ~$0.04 with DeepSeek R1 model for complete docs

## Step 2: Setup (1 minute)

```bash
cd dedup_new

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY-HERE" > .env
```

Replace `YOUR-KEY-HERE` with the key you copied.

## Step 3: Test Setup (30 seconds)

```bash
python scripts/test_setup.py
```

You should see:
```
✓ models.py imports OK
✓ extractor.py imports OK
✓ ai_client.py imports OK
✓ deduplicator.py imports OK
✓ config.yaml loads OK
✓ docs directory found (10 .md files)

✓ All tests passed! Setup is ready.
```

## Step 4: Run Deduplication (15-25 minutes)

```bash
python scripts/run_dedup.py
```

Watch the progress:
```
═══════════════════════════════════════════════
  IB_INSYNC DOCUMENTATION DEDUPLICATION
═══════════════════════════════════════════════

─────── Step 1: Extract Code Examples ───────
Processing 10 markdown files...

Extracting from ib_insync_complete_guide.md...
  ✓ Found 125 examples
...

─────── Step 2: Deduplicate Examples ───────
Finding duplicate clusters...
  ✓ Found 85 clusters

Merging clusters with AI...
[████████████████████████] 85/85 100%
...
```

## Step 5: Check Results (1 minute)

Results are saved to `outputs/`:

```bash
# View the main report
cat outputs/3_final/DEDUPLICATION_REPORT.md

# View deduplicated docs
cat outputs/3_final/ib_insync_deduplicated.md
```

## What You Get

### Main Output Files

1. **ib_insync_deduplicated.md** - Clean, organized documentation with duplicates removed
2. **DEDUPLICATION_REPORT.md** - Summary report with stats and examples
3. **merged_examples.json** - All deduplicated examples with metadata
4. **examples.json** - Raw extracted examples (before deduplication)

### Expected Results

- **Original examples:** ~450
- **Deduplicated:** ~180-200 (60-65% reduction)
- **Cost:** $0.04 - $0.06
- **Time:** 15-25 minutes

## Testing First (Optional)

To test on small subset before processing everything:

Edit `config.yaml`:
```yaml
development:
  enabled: true        # Enable test mode
  max_files: 2         # Process only 2 files
  max_examples: 20     # Process only 20 examples
```

Run:
```bash
python scripts/run_dedup.py
```

Cost: ~$0.002 (less than a penny!)

## Troubleshooting

### Error: "OPENROUTER_API_KEY not found"

Make sure `.env` file exists:
```bash
ls -la .env
cat .env  # Should show your API key
```

### Error: "Rate limit exceeded"

Lower the request rate in `config.yaml`:
```yaml
ai:
  openrouter:
    requests_per_minute: 10  # Lower from 20
```

### Want better quality?

Switch to Claude 3.5 Sonnet in `config.yaml`:
```yaml
ai:
  openrouter:
    model: anthropic/claude-3.5-sonnet  # Change from deepseek/deepseek-r1
```

Cost: ~$1.57 (vs $0.04 for DeepSeek)

## Next Steps

After deduplication:
- Review `ib_insync_deduplicated.md` for quality
- Check `DEDUPLICATION_REPORT.md` for stats
- Use merged examples for AI training, testing, documentation

## Support

- OpenRouter docs: https://openrouter.ai/docs
- DeepSeek model: https://openrouter.ai/models/deepseek/deepseek-r1
- README: See `README.md` for detailed documentation
