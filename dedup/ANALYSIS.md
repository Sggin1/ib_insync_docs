# Document Analysis & Hybrid AI Strategy

**Analysis Date:** 2025-11-15
**Analyst:** Claude Code

---

## Document Inventory

### Source Files Overview

| File | Size | Lines | Primary Content |
|------|------|-------|-----------------|
| `ib.md` | 144KB | 4,071 | Mixed API reference + extensive code examples |
| `ib_insync_complete_guide.md` | 52KB | 1,578 | Tutorial-style guide with explanations + examples |
| `ib_insync_futures_update.md` | 18KB | 522 | Futures-specific guide and patterns |
| `index.md` | 66KB | 892 | Alphabetical API reference index |
| **Total** | **280KB** | **7,063** | **Complete ib_insync documentation** |

### Content Breakdown

Based on pattern analysis:

- **Python Code Blocks:** ~78 blocks across markdown files
- **Code Patterns:** ~500+ instances of `from ib_insync import`, `def`, `class` patterns
- **API Methods Referenced:** Estimated 100-150 unique methods
- **Contract Types:** Stock, Forex, Future, Option, CFD, etc.

---

## Duplication Patterns Identified

### 1. Connection Examples (HIGH Duplication)

**Pattern:** Basic connection to TWS/Gateway

Found in multiple files with minor variations:
- `ib.md` line ~38: Basic connection
- `ib_insync_complete_guide.md`: Multiple async/sync variations
- `ib_insync_futures_update.md`: Connection with futures context

**Variations:**
```python
# Variant A (sync)
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Variant B (async)
ib = IB()
await ib.connectAsync('127.0.0.1', 7497, clientId=1)

# Variant C (with error handling)
try:
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
except ConnectionRefusedError:
    print("Connection failed")
```

**Dedup Strategy:**
- **Local LLM** ✓ - High similarity (>0.95)
- Canonical: Full example with both sync/async
- Preserve notes about when to use each

### 2. Market Data Requests (MEDIUM Duplication)

**Pattern:** `reqMktData()`, `reqHistoricalData()` examples

Different contract types but same structure:
- Forex examples
- Stock examples
- Futures examples

**Variations:**
```python
# Forex
contract = Forex('EURUSD')
ticker = ib.reqMktData(contract)

# Stock
contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract)

# Future
contract = Future('ES', '202412', 'CME')
ticker = ib.reqMktData(contract)
```

**Dedup Strategy:**
- **Local LLM** ✓ - Similar pattern, different contracts
- Group by operation (reqMktData, reqHistoricalData, etc.)
- Create canonical with notes on contract variations

### 3. Event Handling Patterns (LOW Duplication but Complex)

**Pattern:** Event subscription with `+=` operator

Multiple variations across files:
- Synchronous event handlers
- Asynchronous event handlers
- One-time handlers with `@event.once`
- Multiple event types (ticker updates, order status, etc.)

**Complexity Factors:**
- Different event types (tickerEvent, orderStatusEvent, etc.)
- Sync vs async handlers
- Context-specific logic within handlers

**Dedup Strategy:**
- **Claude API** ✓ - Complex logic, needs intelligent analysis
- Preserve unique handler implementations
- Extract common patterns
- Flag conflicts between approaches

### 4. API Reference Entries (NO Duplication Expected)

**Pattern:** Method signatures and descriptions

Found primarily in:
- `index.md` - Alphabetical listing
- `ib.md` - Detailed API docs section

**Strategy:**
- Direct extraction, no AI needed
- Cross-reference to link duplicates
- Validate completeness

---

## Expected Cluster Distribution

Based on analysis, estimated cluster breakdown:

### By Similarity Threshold

| Threshold | Cluster Type | Count Estimate | AI Strategy |
|-----------|--------------|----------------|-------------|
| >0.98 | Exact/Near-Exact Duplicates | ~50-80 | Automatic (hash matching) |
| 0.95-0.98 | Very Similar Variants | ~60-90 | Local LLM |
| 0.85-0.95 | Similar with Variations | ~40-60 | Hybrid (Local + Claude) |
| 0.75-0.85 | Related Examples | ~20-30 | Claude API |
| <0.75 | Standalone Examples | ~30-50 | Keep as-is |

**Total Clusters:** ~200-310
**Standalone Examples:** ~30-50

### By Content Type

| Content Type | Count Estimate | Typical AI Strategy |
|--------------|----------------|---------------------|
| Connection Examples | 15-25 | Local LLM |
| Data Request Examples | 40-60 | Local LLM + Claude for complex |
| Order Placement Examples | 30-50 | Claude API (critical logic) |
| Event Handler Examples | 20-30 | Claude API (async complexity) |
| Contract Qualification | 15-25 | Local LLM |
| API Reference Entries | 100-150 | Automatic extraction |

---

## Hybrid AI Strategy - Finalized

### Decision Matrix

Use **Local LLM (Ollama)** when:
- ✓ Cosine similarity >0.95 (very similar)
- ✓ Simple variations (parameter changes, contract types)
- ✓ Connection examples
- ✓ Basic data requests
- ✓ Well-documented patterns
- ✓ <5 variants in cluster

Use **Claude API** when:
- ✓ Cosine similarity 0.75-0.95 (meaningful differences)
- ✓ Complex logic variations
- ✓ Async/event handling patterns
- ✓ Order placement (critical business logic)
- ✓ Conflicting approaches
- ✓ >5 variants in cluster
- ✓ Manual review flags

### Cost-Benefit Analysis

**Scenario A: Claude-Only**
- Clusters to process: ~200-300
- Cost per cluster: ~$0.015
- **Total Cost: $3-5**
- Quality: Excellent
- Time: ~20-30 minutes

**Scenario B: Local-Only**
- Clusters to process: ~200-300
- Cost: $0
- Quality: Good (may miss nuances)
- Time: ~30-40 minutes (slower inference)

**Scenario C: Hybrid (RECOMMENDED)**
- Local LLM: ~140-210 clusters (70%)
- Claude API: ~60-90 clusters (30%)
- **Total Cost: $1-2**
- Quality: Excellent where it matters
- Time: ~25-35 minutes

### Hybrid Implementation Plan

```yaml
# Processing workflow
1. Extract all examples
2. Generate embeddings (local, fast, free)
3. Compute similarity matrix
4. Cluster by similarity

5. For each cluster:
   IF similarity >0.95 AND variants <5:
       → Local LLM merge (fast, free)
   ELSE IF content_type in ['order', 'event', 'pattern']:
       → Claude API merge (high quality)
   ELSE IF variants >5:
       → Claude API merge (complex)
   ELSE:
       → Local LLM merge, flag for review

6. Human review of flagged conflicts
```

### Local LLM Selection

**Recommended:** `qwen2.5:7b` via Ollama

**Rationale:**
- Excellent code understanding
- Fast inference on CPU (~2-5 sec per merge)
- Good at identifying differences
- Strong JSON output formatting

**Alternatives:**
- `llama3.2:3b` - Faster but less capable
- `codellama:7b` - Good for code but weaker at explanations
- `deepseek-coder:6.7b` - Strong at code, good alternative

### Claude API Configuration

**Model:** `claude-sonnet-4-5-20250929`

**Parameters:**
- `temperature: 0.3` - More deterministic
- `max_tokens: 2000` - Sufficient for merge analysis
- `system_prompt`: Include ib_insync context

**Estimated Usage:**
- 60-90 API calls
- ~1,500 input tokens per call (cluster context)
- ~500 output tokens per call (merge decision)
- **Cost: ~$1-2**

---

## Information Preservation Strategy

### What Must Be Preserved

1. **All unique code patterns**
   - Different approaches to same operation
   - Edge case handling
   - Error handling variations

2. **All context and explanations**
   - Why to use an approach
   - When to use sync vs async
   - Gotchas and warnings

3. **Source attribution**
   - Which file(s) example came from
   - Line numbers for reference
   - Section context

4. **Cross-references**
   - Links between related examples
   - Prerequisites
   - Related API methods

### What Can Be Merged

1. **Exact duplicates** - Keep one, track occurrences
2. **Minor variations** - Merge into canonical with notes
3. **Redundant explanations** - Consolidate into best version
4. **Overlapping gotchas** - Combine into comprehensive warning

### Validation Checkpoints

After each pipeline stage:

1. **Extraction:** Validate all source lines accounted for
2. **Clustering:** Check no examples lost or duplicated
3. **Merging:** Verify total information preserved
4. **Final Build:** Ensure all APIs covered, all examples present

---

## Expected Outcomes

### Quantitative Metrics

| Metric | Before | After (Target) | Reduction |
|--------|--------|----------------|-----------|
| **Total Examples** | 250-300 | 90-120 | 60-65% |
| **Exact Duplicates** | 50-80 | 0 | 100% |
| **Similar Variants** | 100-150 | 30-50 | 70% |
| **Standalone Examples** | 30-50 | 30-50 | 0% |
| **API Methods** | 100-150 | 100-150 | 0% (preserved) |
| **Unique Information** | 100% | 100% | 0% (preserved) |

### Qualitative Outcomes

**After Deduplication:**

✓ **Single Source of Truth**
- One canonical example per operation
- Clear hierarchy of variants
- All edge cases documented

✓ **Better Organization**
- Grouped by operation
- Linked to API methods
- Clear prerequisites

✓ **Enhanced Context**
- AI-generated notes on differences
- When to use each variant
- Common pitfalls highlighted

✓ **Training-Ready**
- Structured JSON format
- Embeddings included
- Ready for RAG/agent training

---

## Risks & Mitigations

### Risk 1: Information Loss

**Mitigation:**
- Preserve all variants, mark as non-canonical
- Store diff summaries
- Validation checks at each stage
- Human review of conflicts

### Risk 2: Poor Clustering

**Mitigation:**
- Tune similarity thresholds empirically
- Visualize clusters (t-SNE plots)
- Manual review of outliers
- Iterative threshold adjustment

### Risk 3: AI Merge Errors

**Mitigation:**
- Use Claude for complex cases (higher quality)
- Flag conflicts for human review
- Validate merged code is parseable
- Keep original variants for reference

### Risk 4: Cost Overruns

**Mitigation:**
- Set hard budget limit ($5)
- Monitor API usage in real-time
- Use local LLM as primary
- Can pause and review if approaching limit

---

## Next Steps

### Immediate (Setup Phase)

1. ✅ Create folder structure
2. ✅ Define Pydantic models
3. ✅ Create configuration files
4. ⏳ Install dependencies
5. ⏳ Test local LLM (Ollama)
6. ⏳ Test Claude API (optional)

### Phase 1 (Extraction)

1. Implement markdown parser
2. Extract code blocks with context
3. Identify API methods
4. Track source locations
5. Validate extraction completeness

### Phase 2 (Embedding)

1. Install sentence-transformers
2. Generate embeddings for all examples
3. Validate embedding quality
4. Save embeddings efficiently

### Phase 3 (Clustering)

1. Compute similarity matrix
2. Implement DBSCAN clustering
3. Visualize clusters
4. Tune thresholds
5. Flag outliers

### Phase 4 (AI Merging)

1. Implement local LLM integration
2. Implement Claude API integration
3. Build hybrid decision logic
4. Process all clusters
5. Human review of conflicts

### Phase 5 (Final Build)

1. Build API reference
2. Build example database
3. Extract patterns and gotchas
4. Validate completeness
5. Generate final reports

---

## Conclusion

The hybrid AI approach offers the best balance of:
- **Cost-effectiveness:** ~$1-2 vs $3-5
- **Quality:** Excellent AI decisions where needed
- **Speed:** Local LLM for bulk processing
- **Reliability:** Human review for conflicts

The ib_insync documentation corpus is well-suited for this approach due to:
- Clear duplication patterns (connection, data requests)
- Mix of simple and complex examples
- Good structural organization
- Manageable size (~300 examples)

**Recommendation:** Proceed with hybrid strategy as outlined, starting with local-only mode for development and testing, then switching to hybrid for production run.

---

**Status:** Ready to proceed with implementation
**Confidence:** High
**Next Action:** Install dependencies and test local LLM setup
