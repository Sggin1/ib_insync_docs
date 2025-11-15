# Agent Architecture Recommendation

**Date:** 2025-11-15
**Hardware:** 16GB GPU
**Goal:** Fast, cost-effective, high-quality deduplication

---

## Recommended: Hybrid Parallel Approach

### Architecture

```
Stage 4: Merging (AI-Assisted)
│
├─ Worker Pool (2-4 parallel agents)
│  ├─ Worker 1: Qwen 7B (local, fast)
│  ├─ Worker 2: Qwen 7B (local, fast)
│  ├─ Worker 3: Qwen 7B (local, fast)
│  └─ Worker 4: Qwen 7B (local, fast)
│
└─ Smart Router
   ├─ Simple clusters (70%) → Local workers
   ├─ Complex clusters (20%) → OpenRouter DeepSeek ($0.14/M)
   └─ Critical clusters (10%) → OpenRouter Claude ($3/M)
```

### Implementation

```python
# dedup/src/ai_merger.py

class MergeWorker:
    """Single merge worker with local LLM."""

    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = Ollama(model)

    def merge_cluster(self, cluster: ExampleCluster) -> dict:
        """Merge a cluster using local LLM."""
        prompt = self._build_prompt(cluster)
        response = self.model.generate(prompt)
        return self._parse_response(response)


class SmartRouter:
    """Routes clusters to appropriate merge strategy."""

    def __init__(self, api_client=None):
        self.api = api_client

    def should_use_api(self, cluster: ExampleCluster) -> bool:
        """Determine if cluster needs API (high quality)."""
        return (
            cluster.avg_similarity < 0.9 or
            cluster.variant_count > 5 or
            len(cluster.conflicts) > 0 or
            cluster.operation in ['placeOrder', 'createOrder']  # Critical ops
        )


class ParallelMerger:
    """Manages parallel merge workers."""

    def __init__(self, num_workers: int = 4):
        self.workers = [
            MergeWorker("qwen2.5:7b")
            for _ in range(num_workers)
        ]
        self.router = SmartRouter(api_client=OpenRouter())

    def merge_all(self, clusters: List[ExampleCluster]) -> List[dict]:
        """Merge all clusters using parallel workers."""

        # Separate by routing decision
        local_clusters = []
        api_clusters = []

        for cluster in clusters:
            if self.router.should_use_api(cluster):
                api_clusters.append(cluster)
            else:
                local_clusters.append(cluster)

        # Process local clusters in parallel
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            local_results = list(executor.map(
                self._merge_with_worker,
                local_clusters
            ))

        # Process API clusters (sequential, but few of them)
        api_results = [
            self.router.api.merge(cluster)
            for cluster in api_clusters
        ]

        return local_results + api_results

    def _merge_with_worker(self, cluster: ExampleCluster) -> dict:
        """Merge using available worker."""
        worker = self._get_available_worker()
        return worker.merge_cluster(cluster)
```

---

## Performance Analysis

### Single Sequential Agent
```
Configuration: 1 × Qwen 14B
Processing: 200 clusters sequential
Time per cluster: 25 sec
Total time: 200 × 25 = 83 minutes
GPU usage: 40%
VRAM: 12 GB
Cost: $0
```

### Parallel Workers (2x)
```
Configuration: 2 × Qwen 7B
Processing: 200 clusters, 2 at a time
Time per cluster: 15 sec (faster model)
Total time: (200 ÷ 2) × 15 = 25 minutes
GPU usage: 70-80%
VRAM: 12 GB (2 × 6GB)
Cost: $0
Speedup: 3.3x faster! ⭐
```

### Parallel Workers (4x) - NOT RECOMMENDED
```
Configuration: 4 × Qwen 7B
VRAM needed: 4 × 6GB = 24 GB
Result: Exceeds 16GB GPU ❌
```

### Hybrid (2 workers + API)
```
Configuration: 2 × Qwen 7B + OpenRouter
Local clusters (70%): 140 clusters
  Time: (140 ÷ 2) × 15 = 18 minutes

API clusters (30%): 60 clusters
  Time: 60 × 5 = 5 minutes (parallel API calls)
  Cost: ~$0.20 (DeepSeek) or ~$0.60 (Qwen 72B)

Total time: ~23 minutes
Total cost: ~$0.20
Speedup: 3.6x faster
Quality: Best (API for complex cases)
```

---

## Recommendation for 16GB GPU

**Use: Parallel Workers (2x) with Optional API Fallback**

### Configuration

```yaml
# config.yaml

ai:
  mode: hybrid  # or local_only to start

  local:
    provider: ollama
    model: qwen2.5:7b  # Smaller for parallel execution
    parallel_workers: 2

  openrouter:
    model: deepseek/deepseek-coder  # Cheap fallback
    max_budget: 1.00

merging:
  parallel:
    enabled: true
    num_workers: 2       # 2 parallel workers
    batch_size: 10       # Process 10 at a time per worker

  routing:
    use_api_for_complex: true
    complexity_threshold: 0.9
    api_percentage_max: 30  # At most 30% to API
```

### Why This Works

**16GB GPU Capacity:**
- Qwen 7B: ~6GB VRAM each
- 2 workers: 2 × 6GB = 12GB
- Headroom: 4GB for OS/embeddings
- **Perfect fit!** ✅

**Speed:**
- 2x parallelization = ~2x faster
- Faster model (7B vs 14B) = ~1.5x faster
- **Total speedup: ~3.3x** (83 min → 25 min)

**Quality:**
- 70% local (fast, free, good quality)
- 30% API (complex cases, best quality)
- **Best of both worlds**

**Cost:**
- Local: $0
- API: ~$0.20 (if using DeepSeek)
- **Total: ~$0.20** vs $0 local-only

---

## Alternative: Start Simple, Scale Up

### Phase 1: Single Agent (Development)
```python
# Start with simplest approach
agent = MergeWorker("qwen2.5:14b")

for cluster in clusters[:10]:  # Test with 10 clusters
    result = agent.merge_cluster(cluster)
    validate_result(result)

# Time: ~4 minutes for 10 clusters
# Cost: $0
```

### Phase 2: Add Parallelization (Production)
```python
# Once validated, add parallel workers
merger = ParallelMerger(num_workers=2)
results = merger.merge_all(clusters)

# Time: ~25 minutes for 200 clusters
# Cost: $0
```

### Phase 3: Add API Fallback (If Needed)
```python
# If quality issues with complex clusters
merger = ParallelMerger(num_workers=2)
merger.enable_api_fallback(
    provider="openrouter",
    model="deepseek/deepseek-coder"
)
results = merger.merge_all(clusters)

# Time: ~23 minutes
# Cost: ~$0.20
```

---

## Summary

| Approach | Workers | Time | Cost | Quality | Complexity |
|----------|---------|------|------|---------|------------|
| **Single Sequential** | 1 | 83 min | $0 | Good | Simple ⭐ |
| **Parallel (2x)** | 2 | 25 min | $0 | Good | Medium ⭐⭐ |
| **Hybrid (2x + API)** | 2 | 23 min | $0.20 | Excellent | Medium ⭐⭐ |
| Parallel (4x) | 4 | 13 min | $0 | Good | ❌ Exceeds VRAM |
| Specialized Swarm | Many | ? | $$$ | ? | Complex ❌ |

**Recommendation:**
1. **Start:** Single sequential (simple, validate pipeline)
2. **Production:** Parallel 2x workers (3x faster, same quality)
3. **Optional:** Add API fallback for complex cases (+$0.20, better quality)

**Don't need:** Multiple specialized agents - overkill for this use case

---

## Implementation Priority

**Phase 1 (Now):**
- Implement single sequential agent
- Get pipeline working end-to-end
- Validate merge quality

**Phase 2 (After validation):**
- Add parallel worker pool (2 workers)
- Implement smart routing
- Benchmark performance

**Phase 3 (If needed):**
- Add API fallback for complex cases
- Fine-tune routing logic
- Optimize for cost/quality

Start simple, add complexity only when needed! ⭐
