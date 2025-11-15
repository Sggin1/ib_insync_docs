# Deduplication Architecture - Final Plan Summary

**Date:** 2025-11-15
**Status:** Planning Complete, Ready for Implementation

---

## Overview

Complete planning and architecture for deduplicating ib_insync documentation (~7,000 lines across 4 MD files) into a unified, AI-training-ready knowledge base.

## What Was Created

### Project Structure

```
ib_insync_docs/
├── dedup/                              # Main deduplication project
│   ├── README.md                       # Complete project documentation
│   ├── TODO.md                         # Detailed task tracking
│   ├── ANALYSIS.md                     # Document analysis & AI strategy
│   ├── requirements.txt                # Python dependencies
│   ├── config.yaml                     # Active configuration
│   ├── config.yaml.example             # Configuration template
│   ├── .gitignore                      # Git ignore rules
│   │
│   ├── src/                            # Source code
│   │   ├── __init__.py
│   │   ├── models.py                   # ✓ Complete Pydantic models
│   │   ├── extractors.py               # TODO: Implement
│   │   ├── embeddings.py               # TODO: Implement
│   │   ├── clustering.py               # TODO: Implement
│   │   ├── ai_merger.py                # TODO: Implement
│   │   ├── builders.py                 # TODO: Implement
│   │   └── validators.py               # TODO: Implement
│   │
│   ├── scripts/                        # Pipeline scripts (templates created)
│   │   ├── 01_extract.py
│   │   ├── 02_embed.py
│   │   ├── 03_cluster.py
│   │   ├── 04_merge.py
│   │   ├── 05_build.py
│   │   └── run_all.py
│   │
│   ├── outputs/                        # Generated data (gitignored)
│   │   ├── 1_extracted/
│   │   ├── 2_embedded/
│   │   ├── 3_clustered/
│   │   ├── 4_merged/
│   │   └── 5_final/
│   │
│   ├── logs/                           # Logs (gitignored)
│   │
│   └── tests/                          # Unit tests
│       └── __init__.py
│
└── agent/                              # Future: Testing agent (placeholder)
    └── README.md
```

### Key Documents

1. **dedup/README.md** - Complete project overview, architecture, usage
2. **dedup/TODO.md** - Comprehensive task breakdown for all 6 phases
3. **dedup/ANALYSIS.md** - Deep document analysis & hybrid AI strategy
4. **dedup/src/models.py** - Complete Pydantic data models (ready to use)
5. **dedup/config.yaml** - Configuration with sensible defaults

---

## Architecture Decisions - Finalized

### Technology Stack ✓

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Data Models** | Pydantic 2.0+ | Type safety, validation, JSON serialization |
| **Embeddings** | sentence-transformers<br/>(all-MiniLM-L6-v2) | Free, local, fast, 384-dim vectors |
| **Clustering** | scikit-learn DBSCAN | Density-based, handles variable cluster sizes |
| **String Similarity** | RapidFuzz | Faster than difflib |
| **AI Merging** | Hybrid:<br/>- Ollama (qwen2.5:7b)<br/>- Claude API | Cost-effective, high quality |
| **Vector DB** | ChromaDB (optional) | For future RAG applications |

### Hybrid AI Strategy ✓

**Recommended Approach:** Local LLM + Claude API

```
Phase 1: Fast Clustering (Local, Free)
    sentence-transformers → embeddings
    DBSCAN → ~200-300 clusters

Phase 2: Smart Merging (Hybrid)
    70% clusters → Local LLM (Ollama)
        - High similarity (>0.95)
        - Simple variations
        - <5 variants

    30% clusters → Claude API
        - Complex logic
        - Event handlers
        - Order placement
        - >5 variants
        - Conflicts
```

**Cost Estimate:** $1-2 (vs $3-5 for Claude-only)

### Decision Matrix

| Condition | AI Strategy |
|-----------|-------------|
| Similarity >0.95 AND <5 variants | **Local LLM** |
| Similarity 0.85-0.95 AND simple pattern | **Local LLM** |
| Content type: connection, basic requests | **Local LLM** |
| Content type: orders, events, patterns | **Claude API** |
| Similarity <0.95 AND >5 variants | **Claude API** |
| Conflicts detected | **Claude API** |

---

## Data Models - Implemented ✓

Complete Pydantic models in `dedup/src/models.py`:

### Core Models
- `CodeExample` - Code snippets with metadata, hashing, embeddings
- `ExampleCluster` - Groups of similar examples
- `APIMethod` - API reference entries
- `Pattern` - Usage patterns and best practices
- `Concept` - Tutorial content
- `Gotcha` - Common pitfalls
- `DedupDatabase` - Complete unified knowledge base

### Supporting Models
- `SourceLocation` - Source file tracking
- `APIParameter` - Method parameters
- `DedupMetrics` - Quality metrics

### Pipeline Models
- `ExtractionOutput`
- `EmbeddingOutput`
- `ClusteringOutput`
- `MergingOutput`

All models support JSON serialization and include validation.

---

## Configuration ✓

### Three Operating Modes

1. **local_only** (Default for development)
   - Uses only Ollama
   - Cost: $0
   - Good for testing and iteration

2. **claude_only** (Highest quality)
   - Uses Claude API for all merging
   - Cost: $3-5
   - Best quality, slower

3. **hybrid** (Recommended for production)
   - Uses local LLM + Claude API
   - Cost: $1-2
   - Best balance of cost/quality

### Key Configuration Options

```yaml
ai:
  mode: local_only  # Start with this

embeddings:
  model: all-MiniLM-L6-v2
  device: cpu

clustering:
  similarity_threshold: 0.85

development:
  debug: false
  limits:
    enabled: false  # Set true to limit processing for testing
```

---

## Expected Results

### Quantitative

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Total Examples | 250-300 | 90-120 | **60-65%** |
| Exact Duplicates | 50-80 | 0 | **100%** |
| API Methods | 100-150 | 100-150 | 0% (preserved) |
| Information | 100% | 100% | 0% (preserved) |

### Qualitative

✓ Single source of truth per operation
✓ Clear hierarchy (canonical → variants)
✓ All unique information preserved
✓ Source tracking for every example
✓ AI-generated notes on differences
✓ Patterns and gotchas extracted
✓ Training-ready JSON format
✓ Embeddings included for RAG

---

## Document Analysis Summary

### Source Files
- **ib.md** (144KB) - Mixed API reference + examples
- **ib_insync_complete_guide.md** (52KB) - Tutorial guide
- **ib_insync_futures_update.md** (18KB) - Futures guide
- **index.md** (66KB) - API index

### Content Identified
- ~78 Python code blocks
- ~500+ code patterns
- 100-150 API methods
- High duplication in connection/data request examples
- Complex variations in event handling

See `dedup/ANALYSIS.md` for detailed breakdown.

---

## Implementation Roadmap

### Phase 0: Setup ✓ COMPLETE
- [x] Folder structure
- [x] README, TODO, ANALYSIS docs
- [x] Pydantic models
- [x] Configuration files
- [x] Script templates
- [ ] Install dependencies
- [ ] Test local LLM
- [ ] Test Claude API (optional)

### Phase 1: Extraction (Next)
- [ ] Implement markdown parser
- [ ] Extract code examples
- [ ] Identify API methods
- [ ] Track sources
- [ ] Validate completeness

### Phase 2-5: See dedup/TODO.md

Each phase has detailed tasks in `dedup/TODO.md`.

---

## How to Get Started

### 1. Install Dependencies

```bash
cd dedup
pip install -r requirements.txt
```

### 2. Install Ollama (for local LLM)

```bash
# Install Ollama (see https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull qwen2.5:7b
```

### 3. Configure (Optional)

```bash
# Edit config.yaml if needed
vim config.yaml

# Set Claude API key if using hybrid/claude_only mode
export ANTHROPIC_API_KEY="your-key-here"
```

### 4. Run Pipeline (when implemented)

```bash
# Run complete pipeline
python scripts/run_all.py

# Or run step by step
python scripts/01_extract.py
python scripts/02_embed.py
# ... etc
```

### 5. Development Mode

```bash
# Enable debug mode with limited processing
python scripts/run_all.py --debug

# Use local LLM only (no API costs)
python scripts/run_all.py --local-only
```

---

## Cost Estimates

### Development (Iterating)
- Local LLM only: **$0**
- Perfect for testing, tuning thresholds

### Production Run
- Local-only: **$0** (slightly lower quality)
- Hybrid: **$1-2** (recommended)
- Claude-only: **$3-5** (highest quality)

### Ongoing
- Re-running pipeline: Same as production
- Incremental updates: Minimal cost (only new content)

---

## Success Criteria

### Must Have
- ✓ 60-70% reduction in example count
- ✓ 100% information preservation
- ✓ 100% API coverage
- ✓ All sources tracked
- ✓ Valid JSON output

### Should Have
- ✓ 90%+ example executability
- ✓ Clear canonical/variant hierarchy
- ✓ Comprehensive gotcha extraction
- ✓ Pattern identification

### Nice to Have
- Visualization of clusters
- Interactive browser UI
- ChromaDB integration for RAG
- Synthetic example generation

---

## Next Steps

1. **Review** this summary and other docs
2. **Install** dependencies (`pip install -r requirements.txt`)
3. **Test** local LLM setup (Ollama + qwen2.5:7b)
4. **Implement** Phase 1: Extraction (see `dedup/TODO.md`)
5. **Iterate** through remaining phases

---

## Questions to Address

### Before Starting Implementation

1. ✓ **Architecture finalized?** Yes - Hybrid AI with local LLM + Claude
2. ✓ **Technology stack chosen?** Yes - See architecture decisions
3. ✓ **Data models defined?** Yes - Complete Pydantic models in models.py
4. ✓ **Configuration ready?** Yes - config.yaml with three modes

### During Implementation

1. **Similarity thresholds?** Start with 0.85, tune empirically
2. **Handle outliers?** Keep as standalone examples
3. **Code validation?** Parse AST, ensure executable
4. **Conflict resolution?** Flag for human review

See `dedup/TODO.md` "Questions for Review" section for more.

---

## Files Reference

### Essential Reading
1. `dedup/README.md` - Project overview and usage
2. `dedup/TODO.md` - Implementation roadmap
3. `dedup/ANALYSIS.md` - Strategy deep dive

### Configuration
1. `dedup/config.yaml` - Active config
2. `dedup/config.yaml.example` - Template with all options

### Code
1. `dedup/src/models.py` - Complete data models ✓
2. `dedup/scripts/run_all.py` - Main pipeline (template)
3. `dedup/scripts/01_extract.py` - Stage 1 (template)

### Future
1. `agent/README.md` - Testing agent placeholder

---

## Architecture Highlights

### Why This Architecture?

✓ **Cost-Effective**
- Local embeddings (free)
- Hybrid AI ($1-2 vs $3-5)
- Can run completely free with local-only mode

✓ **High Quality**
- sentence-transformers for semantic understanding
- Claude API for complex merges
- Pydantic for data validation

✓ **Flexible**
- Three modes: local, hybrid, claude-only
- Tunable thresholds
- Debug mode for development

✓ **Maintainable**
- Clear separation of concerns
- Type-safe with Pydantic
- Comprehensive logging
- Well-documented

✓ **Future-Proof**
- Embeddings ready for RAG
- ChromaDB integration path
- Agent training pipeline ready

---

## Conclusion

**Status:** Architecture planning is COMPLETE. All foundational documents, models, and structure are in place.

**Confidence:** High - Well-researched strategy with clear implementation path.

**Ready For:** Phase 1 implementation (extraction).

**Estimated Timeline:**
- Phase 1 (Extraction): 1-2 days
- Phase 2 (Embedding): 1 day
- Phase 3 (Clustering): 1 day
- Phase 4 (AI Merging): 2-3 days
- Phase 5 (Final Build): 1-2 days
- **Total: 6-9 days** for complete implementation

**Questions?** See respective documents:
- General: `dedup/README.md`
- Tasks: `dedup/TODO.md`
- Strategy: `dedup/ANALYSIS.md`
- This summary: `DEDUP_SUMMARY.md`

---

**Let's build it!** 🚀
