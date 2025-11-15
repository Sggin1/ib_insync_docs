# Deduplication Project TODO

**Current Phase:** Project Setup
**Last Updated:** 2025-11-15

## Phase 0: Project Setup ✓

- [x] Create folder structure
- [x] Write README.md
- [x] Create TODO.md
- [ ] Create requirements.txt
- [ ] Create config.yaml with examples
- [ ] Create .gitignore
- [ ] Define Pydantic models (models.py)
- [ ] Set up basic tests
- [ ] Document hybrid AI strategy decision

## Phase 1: Content Extraction

### 1.1 Markdown Parser
- [ ] Parse markdown structure (headers, code blocks, lists)
- [ ] Extract code examples with surrounding context
- [ ] Identify code language (Python, bash, etc.)
- [ ] Extract API method signatures
- [ ] Extract docstrings and descriptions
- [ ] Handle malformed markdown gracefully

### 1.2 Code Analysis
- [ ] Normalize code (remove comments, standardize whitespace)
- [ ] Generate code hashes for exact duplicates
- [ ] Parse Python AST to identify:
  - Imported modules (ib_insync, IB, Contract, etc.)
  - Method calls (reqHistoricalData, placeOrder, etc.)
  - Contract types (Stock, Forex, Future, etc.)
  - Operation patterns (connect, request data, place order, etc.)
- [ ] Extract variable names and context

### 1.3 Metadata Extraction
- [ ] Track source file and line numbers
- [ ] Identify section/context (header hierarchy)
- [ ] Detect content type (example, reference, tutorial, gotcha)
- [ ] Extract cross-references between sections

### 1.4 Output
- [ ] Save to `outputs/1_extracted/extracted_content.json`
- [ ] Generate summary statistics
- [ ] Create validation report
- [ ] Ensure all source content is represented

**Success Criteria:**
- All 4 MD files parsed successfully
- ~200-400 code examples extracted
- All API methods identified
- Source tracking 100% accurate

---

## Phase 2: Embedding Generation

### 2.1 Setup Embedding Model
- [ ] Install sentence-transformers
- [ ] Download `all-MiniLM-L6-v2` model
- [ ] Test embedding generation
- [ ] Benchmark performance

### 2.2 Generate Embeddings
- [ ] Embed normalized code
- [ ] Embed operation descriptions
- [ ] Embed API method signatures
- [ ] Embed conceptual text
- [ ] Store embeddings efficiently (numpy arrays)

### 2.3 Output
- [ ] Save to `outputs/2_embedded/embedded_content.json`
- [ ] Save embeddings separately (numpy/pickle)
- [ ] Generate embedding visualization (t-SNE/UMAP)
- [ ] Document embedding dimensions and model info

**Success Criteria:**
- All code examples have embeddings
- Embedding generation < 5 minutes total
- Similar examples have high cosine similarity (>0.85)

---

## Phase 3: Clustering

### 3.1 Similarity Analysis
- [ ] Compute pairwise similarity matrix
- [ ] Identify exact duplicates (hash matching)
- [ ] Identify near-duplicates (cosine similarity >0.95)
- [ ] Identify similar variants (cosine similarity >0.85)

### 3.2 Clustering Algorithm
- [ ] Implement DBSCAN clustering
- [ ] Tune epsilon and min_samples parameters
- [ ] Handle outliers (single examples)
- [ ] Create hierarchical clusters (a0, a1, a2 hierarchy)

### 3.3 Cluster Analysis
- [ ] For each cluster, identify:
  - Most representative example (canonical)
  - Key variations
  - Unique information per variant
  - Conflict resolution strategy
- [ ] Generate cluster visualization
- [ ] Create cluster summary report

### 3.4 Output
- [ ] Save to `outputs/3_clustered/clusters.json`
- [ ] Save similarity matrix
- [ ] Generate cluster statistics
- [ ] Create manual review report for edge cases

**Success Criteria:**
- ~200-300 clusters identified
- Clear canonical examples selected
- Outliers properly handled
- Cluster quality score >0.8

---

## Phase 4: AI-Assisted Merging

### 4.1 Setup AI Integration
- [ ] Configure Ollama with qwen2.5:7b or llama3.2
- [ ] Test local LLM merging
- [ ] Configure Claude API (optional)
- [ ] Create prompt templates for merging

### 4.2 Local LLM Merging (70% of cases)
- [ ] Identify simple clusters (high similarity, low variance)
- [ ] Use local LLM to merge
- [ ] Extract unique information
- [ ] Generate merge summaries

### 4.3 Claude API Merging (30% of cases)
- [ ] Identify complex clusters (conflicts, ambiguity)
- [ ] Use Claude API for intelligent merging
- [ ] Handle edge cases
- [ ] Review Claude suggestions

### 4.4 Merge Strategy
- [ ] Select best canonical version
- [ ] Preserve unique details from variants
- [ ] Create comprehensive notes
- [ ] Track diff summaries
- [ ] Flag conflicts for human review

### 4.5 Output
- [ ] Save to `outputs/4_merged/merged_clusters.json`
- [ ] Generate merge decisions log
- [ ] Create conflict report
- [ ] Calculate cost (API usage)

**Success Criteria:**
- All clusters processed
- No information loss
- Conflicts clearly flagged
- API cost < $5
- Merge quality validated

---

## Phase 5: Final Build

### 5.1 API Reference
- [ ] Build complete API method index
- [ ] Link examples to methods
- [ ] Add parameter documentation
- [ ] Include gotchas per method

### 5.2 Example Database
- [ ] Create hierarchical example structure
- [ ] Link canonical → variants
- [ ] Preserve source tracking
- [ ] Add operation metadata

### 5.3 Pattern Extraction
- [ ] Identify common patterns (connect, request, parse)
- [ ] Extract best practices
- [ ] Document anti-patterns
- [ ] Create pattern catalog

### 5.4 Gotchas & Warnings
- [ ] Extract all warnings
- [ ] Categorize gotchas
- [ ] Link to relevant examples
- [ ] Create severity levels

### 5.5 Final Database
- [ ] Build unified `dedup_database.json`
- [ ] Validate schema
- [ ] Ensure completeness
- [ ] Generate statistics

### 5.6 Output
- [ ] `outputs/5_final/api_reference.json`
- [ ] `outputs/5_final/examples.json`
- [ ] `outputs/5_final/patterns.json`
- [ ] `outputs/5_final/gotchas.json`
- [ ] `outputs/5_final/dedup_database.json`
- [ ] Generate final report with metrics

**Success Criteria:**
- 60-70% reduction in example count
- 100% information preservation
- All APIs documented
- Database validates successfully
- Ready for agent training

---

## Phase 6: Validation & Testing

### 6.1 Validation
- [ ] Verify no information lost
- [ ] Check all source files represented
- [ ] Validate JSON schemas
- [ ] Test database queries

### 6.2 Quality Assurance
- [ ] Manual review of sample clusters
- [ ] Verify code examples are executable
- [ ] Check cross-references
- [ ] Review conflict resolutions

### 6.3 Documentation
- [ ] Document pipeline process
- [ ] Create usage examples
- [ ] Write troubleshooting guide
- [ ] Document future improvements

**Success Criteria:**
- All validations pass
- Sample testing confirms quality
- Documentation complete

---

## Future Enhancements

- [ ] Add interactive web UI for browsing
- [ ] Implement incremental updates
- [ ] Add more embedding models for comparison
- [ ] Create visualization dashboard
- [ ] Build RAG system for Q&A
- [ ] Generate synthetic training examples
- [ ] Create test case generator

---

## Metrics to Track

### Deduplication Metrics
- **Total examples before:** ~? (TBD after extraction)
- **Total examples after:** ~? (Target 30-40% of original)
- **Deduplication ratio:** Target 60-70%
- **Exact duplicates:** ?
- **Near duplicates:** ?
- **Similar variants:** ?

### Quality Metrics
- **Information preservation:** 100% target
- **Source tracking accuracy:** 100% target
- **API coverage:** 100% of documented methods
- **Example executability:** >90%

### Performance Metrics
- **Extraction time:** < 2 minutes
- **Embedding time:** < 5 minutes
- **Clustering time:** < 1 minute
- **AI merging time:** < 30 minutes
- **Total pipeline time:** < 45 minutes

### Cost Metrics
- **Claude API cost:** Target < $5
- **Actual cost:** $? (track in config)

---

## Notes & Decisions

### Hybrid AI Strategy Decision
**Decision:** Use hybrid approach with local LLM + Claude API

**Rationale:**
1. **Local LLM (Ollama) for simple merges:**
   - High-similarity clusters (>0.95)
   - Minor variations only
   - ~70% of clusters
   - Cost: $0

2. **Claude API for complex merges:**
   - Multiple significant variations
   - Conflicting information
   - Ambiguous best version
   - ~30% of clusters (~60-90 clusters)
   - Cost: ~$1-2

3. **Benefits:**
   - Cost-effective (~$2 vs ~$5)
   - Faster (local LLM is faster)
   - Best quality where it matters
   - Can iterate locally during dev

### Configuration Strategy
- Store API keys in `config.yaml` (gitignored)
- Support three modes: `claude_only`, `local_only`, `hybrid`
- Default to `local_only` for development
- Switch to `hybrid` for production run

### Data Model Strategy
- Use Pydantic for all data structures
- Serialize to JSON for portability
- Store embeddings separately (binary format)
- Version the schema for future updates

---

## Questions for Review

1. ~~Should we use ChromaDB from the start or add later?~~
   - **Decision:** Add in Phase 5 for final database, optional for now

2. ~~Exact similarity thresholds for clustering?~~
   - **Decision:** Start with 0.85, tune based on results

3. ~~How to handle outliers (single examples with no duplicates)?~~
   - **Decision:** Keep them, mark as canonical, no variants

4. ~~Should we process the PDF file too?~~
   - **Decision:** No, focus on MD files first. PDF is source material.

5. **How deep should code parsing go?**
   - **Decision:** AST for Python code, regex for patterns, extract key method calls

6. **Should we generate embeddings for explanatory text too?**
   - **Decision:** Yes, for concepts and gotchas, helps with semantic clustering

---

## Current Focus

**Next up:** Create requirements.txt and config.yaml, then start implementing models.py
