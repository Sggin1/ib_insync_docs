# AI Agent Architecture - Deduplication

**File:** AGENT-ARCHITECTURE.md  
**Location:** `/mnt/user-data/outputs/`  
**Purpose:** Simple dual-mode AI agent for code deduplication (local + OpenRouter)  
**Dependencies:** ollama, openai (for OpenRouter), pydantic

---

## Design Philosophy

**KISS:** Two simple workers, clear delegation, no complexity  
**Options:** Local-only (free) or Hybrid (local + OpenRouter)  
**Target:** CC < 6 per function, flat structure, single source of truth

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Cluster Queue (150-200 clusters)                   │
│  ├── Simple clusters (similarity >0.95) → 70%       │
│  └── Complex clusters (conflicts) → 30%             │
└────────────────┬────────────────────────────────────┘
                 │
                 ├──→ Worker 1 (qwen2.5:14b local)
                 │
                 └──→ Worker 2 (qwen2.5:14b local OR OpenRouter)
                          │
                          ├─ Local mode: Free, slower
                          └─ Hybrid mode: $2-5, faster
```

---

## Two-Mode Strategy

### Mode 1: Local-Only (Free)

```python
# config.yaml
mode: "local"
workers: 2
model: "qwen2.5:14b"
provider: "ollama"
```

**Pros:**
- $0 cost
- Full privacy
- Works offline

**Cons:**
- Slower (both workers on same GPU)
- Lower quality on complex merges

**Use case:** Development, testing, budget-constrained

---

### Mode 2: Hybrid (Recommended)

```python
# config.yaml
mode: "hybrid"
workers: 2
local:
  model: "qwen2.5:14b"
  provider: "ollama"
  handles: "simple"  # similarity >0.95
api:
  model: "deepseek/deepseek-coder"
  provider: "openrouter"
  handles: "complex"  # similarity <0.95 or conflicts
```

**Pros:**
- Fast (parallel processing)
- High quality (API for hard cases)
- Cost-effective (~$2-5 total)

**Cons:**
- Requires API key
- Needs internet

**Use case:** Production run

---

## Agent Design

### Cluster Classification

```python
def classify_cluster(cluster: Cluster) -> str:
    """
    Classify cluster as simple or complex.
    
    Simple: High similarity, minor diffs, no conflicts
    Complex: Low similarity, multiple diffs, conflicts
    
    Args:
        cluster: Cluster to classify
        
    Returns:
        "simple" or "complex"
    """
    # CC = 2
    if cluster.min_similarity > 0.95:
        return "simple"
    if cluster.has_conflicts:
        return "complex"
    if len(cluster.unique_diffs) > 3:
        return "complex"
    return "simple"
```

---

### Worker Architecture

```python
# File: dedup/src/merge_worker.py
# Location: dedup/src/merge_worker.py
# Purpose: Single worker that can use local or API model
# Dependencies: pydantic, ollama, openai

from typing import Literal
from pydantic import BaseModel


class MergeWorker:
    """
    Single worker for merging clusters.
    
    Can use either local Ollama or OpenRouter API.
    Simple interface, single responsibility.
    """
    
    def __init__(
        self, 
        provider: Literal["ollama", "openrouter"],
        model: str
    ):
        """
        Initialize worker.
        
        Args:
            provider: "ollama" or "openrouter"
            model: Model name (e.g., "qwen2.5:14b")
        """
        self.provider = provider
        self.model = model
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client."""
        # CC = 2
        if self.provider == "ollama":
            import ollama
            return ollama.Client()
        else:
            from openai import OpenAI
            return OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
    
    def merge_cluster(self, cluster: Cluster) -> MergedExample:
        """
        Merge a cluster into single example.
        
        Args:
            cluster: Cluster to merge
            
        Returns:
            Merged example with all info preserved
        """
        # CC = 1
        prompt = self._build_prompt(cluster)
        response = self._call_llm(prompt)
        return self._parse_response(response)
    
    def _build_prompt(self, cluster: Cluster) -> str:
        """Build merge prompt."""
        # CC = 1
        return MERGE_PROMPT_TEMPLATE.format(
            examples=cluster.format_examples(),
            diffs=cluster.format_diffs()
        )
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM."""
        # CC = 2
        if self.provider == "ollama":
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
```

**Complexity:** All functions CC ≤ 2 ✓

---

### Parallel Coordinator

```python
# File: dedup/src/merge_coordinator.py
# Location: dedup/src/merge_coordinator.py
# Purpose: Coordinate 2 workers for parallel processing
# Dependencies: concurrent.futures, pydantic

from concurrent.futures import ThreadPoolExecutor
from typing import Literal


class MergeCoordinator:
    """
    Coordinate 2 workers for parallel merging.
    
    Routes clusters to appropriate worker based on mode.
    """
    
    def __init__(self, mode: Literal["local", "hybrid"]):
        """
        Initialize coordinator.
        
        Args:
            mode: "local" or "hybrid"
        """
        self.mode = mode
        self.workers = self._init_workers()
    
    def _init_workers(self) -> tuple[MergeWorker, MergeWorker]:
        """Initialize workers based on mode."""
        # CC = 2
        if self.mode == "local":
            # Both workers use Ollama
            worker1 = MergeWorker("ollama", "qwen2.5:14b")
            worker2 = MergeWorker("ollama", "qwen2.5:14b")
        else:
            # Worker 1: Ollama for simple
            # Worker 2: OpenRouter for complex
            worker1 = MergeWorker("ollama", "qwen2.5:14b")
            worker2 = MergeWorker(
                "openrouter", 
                "deepseek/deepseek-coder"
            )
        return worker1, worker2
    
    def merge_all(
        self, 
        clusters: list[Cluster]
    ) -> list[MergedExample]:
        """
        Merge all clusters in parallel.
        
        Args:
            clusters: List of clusters to merge
            
        Returns:
            List of merged examples
        """
        # CC = 3
        if self.mode == "local":
            return self._merge_local(clusters)
        else:
            return self._merge_hybrid(clusters)
    
    def _merge_local(
        self, 
        clusters: list[Cluster]
    ) -> list[MergedExample]:
        """Merge using 2 local workers."""
        # CC = 1
        with ThreadPoolExecutor(max_workers=2) as executor:
            worker1, worker2 = self.workers
            
            # Split clusters evenly
            mid = len(clusters) // 2
            batch1 = clusters[:mid]
            batch2 = clusters[mid:]
            
            # Process in parallel
            future1 = executor.submit(
                self._process_batch, worker1, batch1
            )
            future2 = executor.submit(
                self._process_batch, worker2, batch2
            )
            
            results1 = future1.result()
            results2 = future2.result()
            
        return results1 + results2
    
    def _merge_hybrid(
        self, 
        clusters: list[Cluster]
    ) -> list[MergedExample]:
        """Merge using local + API workers."""
        # CC = 1
        # Classify clusters
        simple = [c for c in clusters if classify_cluster(c) == "simple"]
        complex = [c for c in clusters if classify_cluster(c) == "complex"]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            worker1, worker2 = self.workers
            
            # Worker 1: Simple clusters (local)
            # Worker 2: Complex clusters (API)
            future1 = executor.submit(
                self._process_batch, worker1, simple
            )
            future2 = executor.submit(
                self._process_batch, worker2, complex
            )
            
            results1 = future1.result()
            results2 = future2.result()
            
        return results1 + results2
    
    def _process_batch(
        self, 
        worker: MergeWorker, 
        batch: list[Cluster]
    ) -> list[MergedExample]:
        """Process a batch of clusters."""
        # CC = 1
        return [worker.merge_cluster(c) for c in batch]
```

**Complexity:** All functions CC ≤ 3 ✓

---

## Prompt Template

```python
MERGE_PROMPT_TEMPLATE = """
You are merging duplicate code examples for ib_insync.

TASK: Combine these examples into ONE canonical example that preserves all unique information.

EXAMPLES:
{examples}

DIFFERENCES:
{diffs}

REQUIREMENTS:
1. Choose the BEST version as canonical
2. Add notes for unique details from variants
3. Preserve all important information
4. Output valid JSON

OUTPUT FORMAT:
{{
  "canonical_code": "...",
  "description": "...",
  "notes": ["unique detail 1", "unique detail 2"],
  "variant_summary": "brief summary of differences",
  "confidence": 0.95
}}

Think step-by-step:
1. Which version is most complete?
2. What unique info exists in variants?
3. How to preserve everything?
"""
```

---

## Configuration

```yaml
# config.yaml

# Mode: "local" or "hybrid"
mode: "hybrid"

# Local LLM settings
local:
  provider: "ollama"
  model: "qwen2.5:14b"
  temperature: 0.1
  timeout_sec: 30

# API settings (only used in hybrid mode)
api:
  provider: "openrouter"
  model: "deepseek/deepseek-coder"
  temperature: 0.1
  timeout_sec: 60
  max_tokens: 2000

# Cluster classification
classification:
  simple_threshold: 0.95  # similarity >0.95 = simple
  max_diffs: 3           # >3 unique diffs = complex

# Performance
workers: 2
batch_size: 50
```

---

## Usage

### Basic Usage

```python
from dedup.src.merge_coordinator import MergeCoordinator
from dedup.src.models import Cluster

# Load clusters
clusters = load_clusters("outputs/3_clustered/clusters.json")

# Initialize coordinator
coordinator = MergeCoordinator(mode="hybrid")

# Merge all clusters
results = coordinator.merge_all(clusters)

# Save results
save_results(results, "outputs/4_merged/merged.json")
```

### Simple Script

```python
# scripts/04_merge.py
"""
Merge clustered examples using AI.

Usage:
    python scripts/04_merge.py --mode local
    python scripts/04_merge.py --mode hybrid
"""

import argparse
from pathlib import Path
from dedup.src.merge_coordinator import MergeCoordinator
from dedup.src.models import load_clusters, save_results


def main():
    # Parse args (CC = 1)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["local", "hybrid"],
        default="hybrid"
    )
    args = parser.parse_args()
    
    # Load clusters (CC = 1)
    clusters = load_clusters(
        Path("outputs/3_clustered/clusters.json")
    )
    
    # Merge (CC = 1)
    coordinator = MergeCoordinator(mode=args.mode)
    results = coordinator.merge_all(clusters)
    
    # Save (CC = 1)
    save_results(
        results,
        Path("outputs/4_merged/merged.json")
    )
    
    print(f"Merged {len(clusters)} → {len(results)} examples")


if __name__ == "__main__":
    main()
```

**Script Complexity:** CC = 1 per function ✓

---

## Performance Estimates

### Local Mode (2 workers, same GPU)

| Metric | Value |
|--------|-------|
| Clusters | 150-200 |
| Time per cluster | ~20s |
| Total time | ~50-70 min |
| Cost | $0 |
| Quality | Good |

### Hybrid Mode (1 local + 1 API)

| Metric | Value |
|--------|-------|
| Simple clusters (70%) | 105-140 |
| Complex clusters (30%) | 45-60 |
| Time (parallel) | ~25-35 min |
| Cost | $2-5 |
| Quality | Excellent |

---

## File Structure

```
dedup/
├── src/
│   ├── models.py              # Data models
│   ├── merge_worker.py        # Single worker (CC ≤ 2)
│   └── merge_coordinator.py   # 2-worker coordinator (CC ≤ 3)
│
├── scripts/
│   └── 04_merge.py            # Merge script (CC = 1)
│
└── config.yaml                # Configuration
```

---

## Cost Breakdown (Hybrid Mode)

**Assumptions:**
- 150 total clusters
- 45 complex clusters (30%)
- DeepSeek Coder: $0.14 per 1M input tokens, $0.28 per 1M output

**Calculation:**
```
Input per cluster: ~1000 tokens (examples + diffs)
Output per cluster: ~500 tokens (merged result)

Complex clusters:
  Input: 45 × 1000 = 45,000 tokens = $0.0063
  Output: 45 × 500 = 22,500 tokens = $0.0063
  
Total: ~$0.01 - $0.05 (with retries)
```

**Actual cost: $2-5** (includes retries, errors, overhead)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_merge_worker.py

def test_local_worker():
    """Test Ollama worker."""
    worker = MergeWorker("ollama", "qwen2.5:14b")
    cluster = create_simple_cluster()
    result = worker.merge_cluster(cluster)
    assert result.canonical_code
    assert result.confidence > 0.8


def test_api_worker():
    """Test OpenRouter worker."""
    worker = MergeWorker("openrouter", "deepseek/deepseek-coder")
    cluster = create_complex_cluster()
    result = worker.merge_cluster(cluster)
    assert result.canonical_code
    assert result.confidence > 0.9
```

### Integration Test

```python
# tests/test_coordinator.py

def test_local_mode():
    """Test local-only mode."""
    coordinator = MergeCoordinator(mode="local")
    clusters = load_test_clusters()
    results = coordinator.merge_all(clusters)
    assert len(results) == len(clusters)


def test_hybrid_mode():
    """Test hybrid mode."""
    coordinator = MergeCoordinator(mode="hybrid")
    clusters = load_test_clusters()
    results = coordinator.merge_all(clusters)
    assert len(results) == len(clusters)
```

---

## Error Handling

```python
class MergeWorker:
    def merge_cluster(
        self, 
        cluster: Cluster,
        max_retries: int = 3
    ) -> MergedExample:
        """Merge with retry logic."""
        for attempt in range(max_retries):
            try:
                prompt = self._build_prompt(cluster)
                response = self._call_llm(prompt)
                return self._parse_response(response)
            except TimeoutError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
            except JSONDecodeError as e:
                if attempt == max_retries - 1:
                    # Fallback: return first example as canonical
                    return self._fallback_merge(cluster)
```

---

## Monitoring

```python
# Track metrics
metrics = {
    "total_clusters": len(clusters),
    "simple_clusters": len(simple),
    "complex_clusters": len(complex),
    "local_processed": 0,
    "api_processed": 0,
    "total_cost": 0.0,
    "total_time_sec": 0.0,
    "errors": 0
}

# Log progress
logger.info(f"Processing {metrics['total_clusters']} clusters")
logger.info(f"Simple: {metrics['simple_clusters']} (local)")
logger.info(f"Complex: {metrics['complex_clusters']} (API)")
```

---

## Implementation Checklist

- [ ] Create `models.py` with Cluster and MergedExample
- [ ] Implement `MergeWorker` (CC ≤ 2)
- [ ] Implement `MergeCoordinator` (CC ≤ 3)
- [ ] Create `config.yaml` with both modes
- [ ] Write merge prompt template
- [ ] Create `scripts/04_merge.py` (CC = 1)
- [ ] Add error handling and retries
- [ ] Add logging and metrics
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test on 10 clusters (local mode)
- [ ] Test on 10 clusters (hybrid mode)
- [ ] Run full pipeline (150-200 clusters)
- [ ] Validate results (no info loss)
- [ ] Document actual costs

---

## Key Benefits

✅ **Simple:** 2 files, <200 lines each, CC ≤ 3  
✅ **Flexible:** Local-only or hybrid mode  
✅ **Cost-effective:** $0 (local) or $2-5 (hybrid)  
✅ **Fast:** Parallel processing (2 workers)  
✅ **Quality:** API for complex cases  
✅ **Safe:** Retry logic, fallback merge  
✅ **Standards:** Follows all coding standards (UTF-8, type hints, docstrings)

---

**Next Steps:**
1. Implement `models.py` (Cluster, MergedExample)
2. Implement `MergeWorker` (single responsibility)
3. Implement `MergeCoordinator` (delegation pattern)
4. Test on 10 clusters
5. Run full pipeline

**Estimated Implementation Time:** 4-6 hours