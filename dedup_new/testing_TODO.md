# IB_insync Testing & Training TODO

**Purpose:** Test deduped examples on demo account, build confirmed dataset, train specialist agent  
**Current Phase:** Phase 7 - Live Testing Setup  
**Last Updated:** 2025-11-15

---

## Phase 7: Live Testing Setup

### 7.1 Test Environment
- [ ] Set up IB demo account (Paper Trading)
- [ ] Install IB Gateway or TWS
- [ ] Configure connection (port 7497 for paper)
- [ ] Test basic connection with ib_insync
- [ ] Document connection parameters

### 7.2 Test Harness
- [ ] Create `test_runner.py` script
- [ ] Implement timeout handling (30s per test)
- [ ] Add error capturing and logging
- [ ] Create test result schema (pass/fail/error/timeout)
- [ ] Add execution time tracking
- [ ] Implement retry logic (3 attempts)

### 7.3 Test Categories
- [ ] Define test categories:
  - `connection` - Basic connection tests
  - `market_data` - Data requests
  - `orders` - Order placement (demo safe)
  - `contracts` - Contract definitions
  - `portfolio` - Account/position queries
  - `async` - Async pattern tests
- [ ] Create category-specific validators
- [ ] Define pass/fail criteria per category

### 7.4 Safety Checks
- [ ] Verify demo account mode
- [ ] Prevent real money orders
- [ ] Add order size limits (< 10 shares)
- [ ] Implement kill switch
- [ ] Log all order attempts

### 7.5 Output
- [ ] `outputs/7_testing/test_harness.py`
- [ ] `outputs/7_testing/test_config.yaml`
- [ ] `outputs/7_testing/safety_checks.py`

**Success Criteria:**
- Demo account connected successfully
- Test harness runs without errors
- Safety checks prevent accidents
- All test categories defined

---

## Phase 8: Example Validation

### 8.1 Load Deduped Examples
- [ ] Load `outputs/5_final/dedup_database.json`
- [ ] Parse apex_popular and tag_index
- [ ] Load tier_a1_raw.json (unconfirmed examples)
- [ ] Count total examples to test (~150-200)

### 8.2 Automated Testing
- [ ] Run connection examples (expect 95%+ pass)
- [ ] Run market data examples (expect 90%+ pass)
- [ ] Run contract examples (expect 95%+ pass)
- [ ] Run portfolio examples (expect 85%+ pass)
- [ ] Run order examples (expect 80%+ pass, some may be complex)
- [ ] Run async examples (expect 75%+ pass)

### 8.3 Test Execution
```python
for example in examples:
    result = {
        "line": example['line'],
        "topic": example['topic'],
        "code": example['code'],
        "status": None,  # pass/fail/error/timeout
        "exec_time_ms": None,
        "error_msg": None,
        "retry_count": 0,
        "timestamp": None
    }
    # Run test with timeout
    # Log result
    # Continue to next
```

### 8.4 Result Analysis
- [ ] Calculate pass rate per category
- [ ] Identify common failure patterns
- [ ] Extract error messages
- [ ] Flag examples needing fixes
- [ ] Generate failure report

### 8.5 Manual Review
- [ ] Review all failed tests (expect 10-20%)
- [ ] Determine if code issue or environment issue
- [ ] Fix correctable examples
- [ ] Document unfixable issues (API limitations, etc.)
- [ ] Re-run fixed examples

### 8.6 Output
- [ ] `outputs/8_validated/test_results.json`
- [ ] `outputs/8_validated/execution_times.json`
- [ ] `outputs/8_validated/failed_examples.json`
- [ ] `outputs/8_validated/validation_report.md`

**Test Result Schema:**
```json
{
  "line": 40,
  "topic": "Connections",
  "tier": "a1",
  "code": "ib.connect('127.0.0.1', 7497, clientId=1)",
  "status": "pass",
  "exec_time_ms": 45,
  "error_msg": null,
  "retry_count": 0,
  "timestamp": "2025-11-15T10:30:00Z",
  "category": "connection"
}
```

**Success Criteria:**
- 150+ examples tested
- 80%+ overall pass rate
- All failures analyzed
- Execution times recorded
- Test results validated

---

## Phase 9: Confirmed Database Build

### 9.1 Filter Passing Examples
- [ ] Extract all `status: "pass"` examples
- [ ] Verify execution times reasonable
- [ ] Check for consistent results (3+ passes)
- [ ] Calculate success rate per example

### 9.2 Update Metadata
- [ ] Add `tested: true` flag
- [ ] Add `test_status: "pass"`
- [ ] Add `exec_time_ms: <value>`
- [ ] Add `test_runs: <count>`
- [ ] Add `success_rate: "100%"`
- [ ] Add `last_tested: <timestamp>`
- [ ] Boost confidence to 1.0 (was 0.9)

### 9.3 Reorganize Tiers
- [ ] Confirmed examples → tier_a1_confirmed.json
- [ ] Failed examples → tier_a2_unconfirmed.json
- [ ] Update apex_popular with test status
- [ ] Update tag_index with tested flags

### 9.4 Add Test Context
```json
{
  "topic": "Connections",
  "tier": "a1",
  "confidence": 1.0,
  "tested": {
    "status": "pass",
    "runs": 15,
    "success_rate": "100%",
    "avg_exec_time_ms": 45,
    "last_tested": "2025-11-15T10:30:00Z",
    "demo_safe": true,
    "category": "connection"
  },
  "code": "ib.connect('127.0.0.1', 7497, clientId=1)",
  "tags": ["connection", "basic", "setup"]
}
```

### 9.5 Generate Confidence Report
- [ ] Count confirmed examples per topic
- [ ] Calculate confidence distribution
- [ ] Identify gaps (topics with no confirmed examples)
- [ ] Create coverage heatmap

### 9.6 Output
- [ ] `outputs/9_confirmed/apex_popular.json` (updated)
- [ ] `outputs/9_confirmed/tag_index.json` (updated)
- [ ] `outputs/9_confirmed/tier_a1_confirmed.json` (golden set)
- [ ] `outputs/9_confirmed/tier_a2_unconfirmed.json` (failed/untested)
- [ ] `outputs/9_confirmed/confidence_report.md`

**Success Criteria:**
- 120+ confirmed examples (80% pass rate)
- All confirmed examples have test metadata
- Confidence scores updated
- Coverage report complete
- Database validates

---

## Phase 10: Real-World Expansion

### 10.1 CLI Examples
- [ ] Create `examples/cli/` folder
- [ ] Build CLI wrapper for common operations:
  - Connect to IB
  - Get market data
  - Place order (interactive)
  - Check positions
  - Monitor account
- [ ] Add argparse for user input
- [ ] Test CLI examples on demo
- [ ] Document CLI usage

### 10.2 Tkinter GUI Examples
- [ ] Create `examples/gui/` folder
- [ ] Build simple GUI apps:
  - Connection manager
  - Market data viewer
  - Order entry form
  - Position monitor
  - Account dashboard
- [ ] Handle threading (GUI + ib_insync)
- [ ] Test GUI examples on demo
- [ ] Document GUI patterns

### 10.3 Test New Examples
- [ ] Run CLI examples through test harness
- [ ] Run GUI examples (manual testing)
- [ ] Capture edge cases and bugs
- [ ] Document workarounds
- [ ] Add to confirmed DB if passing

### 10.4 Bug Pattern Extraction
- [ ] Log all bugs encountered
- [ ] Categorize bug types:
  - Threading issues
  - Event loop conflicts
  - Timeout problems
  - Data type mismatches
  - API quirks
- [ ] Create bug pattern database
- [ ] Link bugs to gotchas

### 10.5 Update Database
- [ ] Add CLI examples to tier_a2_cli.json
- [ ] Add GUI examples to tier_a2_gui.json
- [ ] Update tag_index with new tags (cli, gui, threading)
- [ ] Link to canonical examples
- [ ] Add "variant_type" metadata

### 10.6 Output
- [ ] `examples/cli/*.py` (5-10 CLI scripts)
- [ ] `examples/gui/*.py` (5-10 GUI apps)
- [ ] `outputs/10_expanded/tier_a2_cli.json`
- [ ] `outputs/10_expanded/tier_a2_gui.json`
- [ ] `outputs/10_expanded/bug_patterns.json`
- [ ] `outputs/10_expanded/expansion_report.md`

**Success Criteria:**
- 10-20 new working examples
- CLI and GUI patterns documented
- Bug patterns cataloged
- All new examples tested
- Database expanded successfully

---

## Phase 11: Vectorization

### 11.1 Prepare Embeddings
- [ ] Install sentence-transformers
- [ ] Download model: `all-MiniLM-L6-v2`
- [ ] Load confirmed database
- [ ] Extract text for embedding:
  - Code (normalized)
  - Description
  - Tags
  - Error messages
  - Gotchas

### 11.2 Generate Embeddings
- [ ] Embed code examples (384 dims)
- [ ] Embed descriptions (384 dims)
- [ ] Embed tags (384 dims)
- [ ] Concatenate: [code, desc, tags] → 1152 dims
- [ ] Save embeddings as numpy arrays

### 11.3 Build Vector Index
- [ ] Use FAISS for fast similarity search
- [ ] Create index for 1152-dim vectors
- [ ] Add all confirmed examples
- [ ] Test similarity queries
- [ ] Benchmark search speed (<5ms)

### 11.4 Semantic Search
- [ ] Implement query embedding
- [ ] Search by natural language:
  - "How do I connect to IB?"
  - "Place a limit order for AAPL"
  - "Get historical data"
- [ ] Return top-k results (k=5)
- [ ] Include similarity scores

### 11.5 Output
- [ ] `outputs/11_vectorized/embeddings.npy`
- [ ] `outputs/11_vectorized/metadata.json`
- [ ] `outputs/11_vectorized/faiss_index.bin`
- [ ] `outputs/11_vectorized/embedding_config.json`
- [ ] `outputs/11_vectorized/search_examples.md`

**Success Criteria:**
- All confirmed examples embedded
- FAISS index built successfully
- Semantic search works
- Search time <5ms
- Top results relevant

---

## Phase 12: Specialist Agent Training

### 12.1 Training Data Preparation
- [ ] Load vectorized database
- [ ] Create question-answer pairs:
  - Question: Natural language query
  - Answer: Best code example + explanation
  - Context: Related examples
- [ ] Generate synthetic Q&A (using LLM)
- [ ] Add metadata (difficulty, category, tags)

### 12.2 RAG System Setup
- [ ] Implement Retrieval-Augmented Generation
- [ ] Query → Embed → Search → Retrieve top-k
- [ ] Feed examples to LLM as context
- [ ] Generate response with code

### 12.3 Fine-Tuning (Optional)
- [ ] Prepare fine-tuning dataset (Q&A pairs)
- [ ] Format for LLM (Llama, Qwen, etc.)
- [ ] Fine-tune small model (1-7B params)
- [ ] Evaluate on test set
- [ ] Compare to RAG-only approach

### 12.4 Agent Configuration
```yaml
agent:
  name: "IB_insync Specialist"
  base_model: "qwen2.5:7b"
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
  response:
    include_code: true
    include_explanation: true
    include_gotchas: true
  testing:
    validate_code: true
    run_on_demo: false  # Optional
```

### 12.5 Testing & Evaluation
- [ ] Create test question set (50-100 questions)
- [ ] Query agent with test questions
- [ ] Evaluate responses:
  - Correctness (code works)
  - Relevance (matches question)
  - Completeness (includes gotchas)
  - Clarity (explanation quality)
- [ ] Calculate metrics (accuracy, relevance@5, etc.)
- [ ] Iterate on prompts

### 12.6 Output
- [ ] `outputs/12_specialist/training_data.json`
- [ ] `outputs/12_specialist/rag_config.yaml`
- [ ] `outputs/12_specialist/agent_prompts.txt`
- [ ] `outputs/12_specialist/evaluation_results.json`
- [ ] `outputs/12_specialist/specialist_agent.py`

**Success Criteria:**
- Agent answers 90%+ of questions correctly
- Code examples are working (from confirmed DB)
- Responses include relevant gotchas
- Search latency <100ms
- Agent ready for production use

---

## Metrics to Track

### Testing Metrics (Phase 8)
- **Total examples tested:** ~150-200
- **Pass rate:** Target 80%+
- **Average execution time:** <100ms
- **Retry rate:** <10%
- **Timeout rate:** <5%

### Confirmation Metrics (Phase 9)
- **Confirmed examples:** Target 120+ (80% of tested)
- **Confidence 1.0 examples:** 100%
- **Coverage per topic:** 80%+ topics have confirmed examples
- **Test runs per example:** 3+ for reliability

### Expansion Metrics (Phase 10)
- **New CLI examples:** 5-10
- **New GUI examples:** 5-10
- **Bugs found:** ~10-20
- **Bug patterns documented:** 5-10 categories

### Vectorization Metrics (Phase 11)
- **Embeddings generated:** ~150-200
- **Embedding time:** <5 minutes
- **Search speed:** <5ms per query
- **Index size:** ~50MB

### Agent Metrics (Phase 12)
- **Training examples:** ~150-200
- **Synthetic Q&A pairs:** 500-1000
- **Question accuracy:** Target 90%+
- **Response time:** <2 seconds
- **Code correctness:** 95%+

---

## Cost & Time Estimates

### Time Investment
| Phase | Estimated Time |
|-------|---------------|
| 7. Test Setup | 4-6 hours |
| 8. Validation | 8-12 hours (mostly automated) |
| 9. Confirmed DB | 2-4 hours |
| 10. Expansion | 10-15 hours |
| 11. Vectorization | 2-4 hours |
| 12. Agent Training | 6-10 hours |
| **Total** | **32-51 hours** |

### Cost Estimate
| Item | Cost |
|------|------|
| IB demo account | $0 (free) |
| Compute (local) | $0 |
| Claude API (if used) | $2-5 |
| **Total** | **$2-5** |

---

## File Structure

```
project/
├── examples/
│   ├── cli/
│   │   ├── connect.py
│   │   ├── market_data.py
│   │   ├── place_order.py
│   │   └── ...
│   └── gui/
│       ├── connection_manager.py
│       ├── market_viewer.py
│       └── ...
│
├── outputs/
│   ├── 7_testing/
│   │   ├── test_harness.py
│   │   └── test_config.yaml
│   │
│   ├── 8_validated/
│   │   ├── test_results.json
│   │   ├── execution_times.json
│   │   ├── failed_examples.json
│   │   └── validation_report.md
│   │
│   ├── 9_confirmed/
│   │   ├── apex_popular.json
│   │   ├── tag_index.json
│   │   ├── tier_a1_confirmed.json
│   │   ├── tier_a2_unconfirmed.json
│   │   └── confidence_report.md
│   │
│   ├── 10_expanded/
│   │   ├── tier_a2_cli.json
│   │   ├── tier_a2_gui.json
│   │   ├── bug_patterns.json
│   │   └── expansion_report.md
│   │
│   ├── 11_vectorized/
│   │   ├── embeddings.npy
│   │   ├── metadata.json
│   │   ├── faiss_index.bin
│   │   └── embedding_config.json
│   │
│   └── 12_specialist/
│       ├── training_data.json
│       ├── rag_config.yaml
│       ├── agent_prompts.txt
│       ├── evaluation_results.json
│       └── specialist_agent.py
│
└── tests/
    ├── test_connection.py
    ├── test_market_data.py
    └── ...
```

---

## Safety & Best Practices

### Demo Account Safety
- [ ] ALWAYS verify demo mode before ANY order
- [ ] Use paper account credentials only
- [ ] Limit order sizes (max 10 shares)
- [ ] Log all order attempts
- [ ] Implement kill switch

### Code Quality
- [ ] All code UTF-8 encoded
- [ ] Follow PEP 8
- [ ] Add type hints
- [ ] Keep complexity <6 (radon cc)
- [ ] Add error handling

### Testing Standards
- [ ] 3+ test runs for reliability
- [ ] 30s timeout per test
- [ ] 3 retry attempts max
- [ ] Log all errors
- [ ] Validate all results

---

## Questions for Review

1. **What pass rate threshold should trigger manual review?**
   - Recommendation: <80% overall or <60% for any category

2. **Should we test on multiple demo accounts?**
   - Recommendation: Start with one, add more if rate limiting issues

3. **How to handle examples requiring market hours?**
   - Recommendation: Tag them, test during market hours separately

4. **Should GUI examples be in confirmed DB?**
   - Recommendation: Yes, but mark as `gui_tested: manual`

5. **Fine-tune model or use RAG only?**
   - Recommendation: Start with RAG, fine-tune if needed

---

## Current Focus

**Next Steps:**
1. Complete Phase 0-6 (deduplication pipeline)
2. Set up IB demo account
3. Build test harness
4. Start automated testing

**Goal:** Production-ready IB_insync specialist agent with 100% tested, working examples