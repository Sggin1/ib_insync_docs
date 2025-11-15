# ib_insync Documentation Deduplication Project

**Goal:** Transform overlapping ib_insync documentation into a unified, deduplicated knowledge base optimized for AI training and testing.

## Project Overview

This project processes multiple ib_insync documentation files (~7,000 lines across 4 MD files) to:
- Extract and deduplicate code examples
- Build comprehensive API reference
- Identify patterns, gotchas, and best practices
- Create hierarchical knowledge structure
- Preserve all unique information while removing redundancy

## Source Documents

- `ib.md` (144KB, 4,071 lines) - Mixed API reference + examples
- `ib_insync_complete_guide.md` (52KB, 1,578 lines) - Comprehensive tutorial
- `ib_insync_futures_update.md` (18KB, 522 lines) - Futures-focused guide
- `index.md` (66KB, 892 lines) - API reference index

## Architecture

### Technology Stack

| Component | Library | Rationale |
|-----------|---------|-----------|
| **Data Models** | Pydantic | Type safety, validation, JSON serialization |
| **Embeddings** | sentence-transformers | Free, local, excellent code understanding |
| **Clustering** | scikit-learn (DBSCAN) | Density-based, handles variable cluster sizes |
| **String Similarity** | RapidFuzz | Faster than difflib for exact matching |
| **Code Parsing** | AST + regex | Understand code structure |
| **Markdown Parsing** | python-markdown | Extract structure and metadata |
| **AI Merging (Primary)** | Anthropic Claude API | Best context understanding (~$3 for ~200 clusters) |
| **AI Merging (Fallback)** | Local LLM (Ollama) | Free, slower, for dev/testing |
| **Vector DB** | ChromaDB | Simple, local-first, SQLite backend for future RAG |

### Hybrid AI Strategy

**Phase 1: Fast Clustering (Automated, Local)**
```
sentence-transformers (local embeddings)
    ↓
DBSCAN clustering (>0.85 similarity)
    ↓
~200-300 example clusters identified
```

**Phase 2: Intelligent Merging (AI-Assisted)**
```
For each cluster:
    ↓
Local LLM (Ollama) - First pass analysis
    ↓
If complex/ambiguous → Claude API (high-quality merge)
    ↓
Final deduplicated examples with metadata
```

**Cost-Effective Approach:**
- Use embeddings for comparison (local, fast, free)
- Use local LLM for simple merges (70% of cases)
- Use Claude API only for complex merges (30% of cases)
- Estimated cost: $1-2 instead of $3-5

## Pipeline Stages

### 1. Extraction (`outputs/1_extracted/`)
Parse markdown files and extract:
- Code examples with context
- API method signatures and descriptions
- Conceptual explanations
- Gotchas and warnings
- Cross-references

**Output:** `extracted_content.json` (Pydantic models)

### 2. Embedding (`outputs/2_embedded/`)
Generate embeddings for:
- Normalized code (comments/whitespace removed)
- Operation descriptions
- Method signatures

**Output:** `embedded_content.json` + embeddings

### 3. Clustering (`outputs/3_clustered/`)
Group similar items:
- Code examples by operation
- API methods by functionality
- Concepts by topic

**Output:** `clusters.json` with similarity scores

### 4. AI Merging (`outputs/4_merged/`)
For each cluster:
- Identify canonical version
- Extract unique information from variants
- Preserve source locations
- Flag conflicts for review

**Output:** `merged_clusters.json`

### 5. Final Build (`outputs/5_final/`)
Create unified knowledge base:
- `api_reference.json` - Complete API documentation
- `examples.json` - Deduplicated code examples with hierarchy
- `patterns.json` - Identified patterns and best practices
- `gotchas.json` - Common pitfalls and solutions
- `dedup_database.json` - Complete unified database

## Folder Structure

```
dedup/
├── README.md              # This file
├── TODO.md                # Task tracking
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration (API keys, thresholds)
│
├── src/                   # Source code
│   ├── __init__.py
│   ├── models.py          # Pydantic data models
│   ├── extractors.py      # Parse MD files
│   ├── embeddings.py      # Generate embeddings
│   ├── clustering.py      # Group similar content
│   ├── ai_merger.py       # AI-assisted merging
│   ├── builders.py        # Build final schema
│   └── validators.py      # Validate outputs
│
├── scripts/               # Runnable pipeline steps
│   ├── 01_extract.py      # Extract all content
│   ├── 02_embed.py        # Generate embeddings
│   ├── 03_cluster.py      # Cluster similar items
│   ├── 04_merge.py        # AI-assisted merging
│   ├── 05_build.py        # Build final outputs
│   └── run_all.py         # Run complete pipeline
│
├── outputs/               # Generated data (gitignored)
│   ├── 1_extracted/
│   ├── 2_embedded/
│   ├── 3_clustered/
│   ├── 4_merged/
│   └── 5_final/
│
└── tests/                 # Unit tests
    ├── __init__.py
    ├── test_extractors.py
    └── test_clustering.py
```

## Usage

### Quick Start

```bash
# Install dependencies
cd dedup
pip install -r requirements.txt

# Configure (edit config.yaml with API keys if using Claude)
cp config.yaml.example config.yaml
vim config.yaml

# Run complete pipeline
python scripts/run_all.py

# Or run step by step
python scripts/01_extract.py
python scripts/02_embed.py
python scripts/03_cluster.py
python scripts/04_merge.py
python scripts/05_build.py
```

### Development Mode

```bash
# Run with local LLM only (no API costs)
python scripts/run_all.py --local-only

# Run and inspect outputs between stages
python scripts/01_extract.py && cat outputs/1_extracted/summary.json
python scripts/02_embed.py && cat outputs/2_embedded/summary.json
# ... continue

# Run specific stage only
python scripts/03_cluster.py --input outputs/2_embedded/
```

## Configuration

Edit `config.yaml`:

```yaml
# AI Strategy
ai:
  mode: hybrid  # Options: claude_only, local_only, hybrid
  claude_api_key: null  # Set to use Claude API
  local_model: qwen2.5:7b  # Ollama model for local merging

# Clustering
clustering:
  similarity_threshold: 0.85
  min_cluster_size: 2
  embedding_model: all-MiniLM-L6-v2

# Output
output:
  preserve_sources: true
  include_diffs: true
  validation_level: strict
```

## Success Metrics

- **Deduplication Ratio:** Target 60-70% reduction in example count
- **Information Preservation:** 100% of unique information retained
- **Source Tracking:** All content traceable to original files/lines
- **API Coverage:** 100% of documented methods indexed
- **Quality:** All examples validated, executable, well-documented

## Next Steps

After deduplication is complete, the unified knowledge base will be used to:
1. Train an AI agent for ib_insync testing
2. Generate comprehensive test suites
3. Create interactive documentation
4. Build RAG-powered Q&A system

See `../agent/README.md` for the testing agent project (future work).

## Development Status

See `TODO.md` for current progress and upcoming tasks.
