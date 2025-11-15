# Pyramid Index Architecture

**Design Date:** 2025-11-15
**Purpose:** Ultra-fast hierarchical retrieval with tier-based cascading

---

## Overview

The pyramid index structure enables O(1) lookup to canonical examples and O(log n) traversal to variants through pointer-based navigation.

```
┌─────────────────────────────────────────────────────────┐
│                   apex_index.json                       │  ← APEX
│  Maps operations → canonical examples (a0 tier)         │
│  • connect → ex_abc123                                  │
│  • reqHistoricalData → ex_def456                        │
│  • placeOrder → ex_ghi789                               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Canonical Examples (a0 tier)               │  ← LEVEL 1
│  Most common versions (95-100% similarity)              │
│  • Highest occurrence counts                            │
│  • Each points to its variants                          │
│  • Fast retrieval path                                  │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────┼───────┐
                    ▼       ▼       ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Variants (a1)│  │ Variants (a1)│  │ Variants (a2)│  ← LEVEL 2
│ 85-95% sim   │  │ 85-95% sim   │  │ 75-85% sim   │
│ Minor changes│  │ Minor changes│  │ Significant  │
└──────────────┘  └──────────────┘  └──────┬───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │ Variants (a3)│  ← LEVEL 3
                                    │ 65-75% sim   │     (BASE)
                                    │ Rare/edge    │
                                    └──────────────┘
```

---

## File Structure

```
outputs/5_final/
├── apex_index.json              ← Master index (fast lookup)
├── canonical_examples.json      ← All a0 tier examples
├── variant_clusters.json        ← All a1-a3 variants
├── api_reference.json           ← API method documentation
└── dedup_database.json          ← Complete database
```

---

## Index Schema

### 1. Apex Index (apex_index.json)

**Purpose:** O(1) lookup from operation to canonical example

```json
{
  "version": "1.0.0",
  "created_at": "2025-11-15T12:00:00Z",
  "total_operations": 45,
  "total_examples": 287,
  "total_canonical": 102,

  "operations": {
    "connect": {
      "canonical_id": "ex_abc123",
      "total_occurrences": 14,
      "variant_count": 3,
      "confidence": 1.0,
      "tier_distribution": {
        "a0": 8,   // 8 exact matches
        "a1": 4,   // 4 minor variants
        "a2": 2    // 2 significant variants
      },
      "file_pointer": "canonical_examples.json#ex_abc123"
    },
    "reqHistoricalData": {
      "canonical_id": "ex_def456",
      "total_occurrences": 23,
      "variant_count": 6,
      "confidence": 1.0,
      "tier_distribution": {
        "a0": 12,
        "a1": 8,
        "a2": 2,
        "a3": 1
      },
      "file_pointer": "canonical_examples.json#ex_def456"
    }
    // ... more operations
  },

  "quick_stats": {
    "most_common": ["reqHistoricalData", "connect", "placeOrder"],
    "avg_variants_per_operation": 3.2,
    "deduplication_ratio": 0.64
  }
}
```

### 2. Canonical Examples (canonical_examples.json)

**Purpose:** All a0 tier examples with pointers to variants

```json
{
  "version": "1.0.0",
  "tier": "a0",
  "count": 102,

  "examples": {
    "ex_abc123": {
      "id": "ex_abc123",
      "operation": "connect",
      "code": "ib = IB()\nib.connect('127.0.0.1', 7497, clientId=1)",
      "language": "python",

      "occurrence_count": 8,
      "tier": "a0",
      "is_canonical": true,
      "similarity": 1.0,

      "sources": [
        {"file": "ib.md", "line": 45, "section": "Getting Started"},
        {"file": "ib.md", "line": 203, "section": "API Reference"},
        {"file": "guide.md", "line": 12, "section": "Quick Start"}
        // ... 5 more
      ],

      "variants": {
        "a1": ["ex_jkl345", "ex_mno678"],  // Minor variants
        "a2": ["ex_pqr901"],                // Significant variants
        "a3": []                             // Related patterns
      },

      "variant_count": 3,
      "total_occurrences": 14,

      "metadata": {
        "methods_used": ["IB.__init__", "IB.connect"],
        "contract_types": [],
        "complexity": "basic",
        "category": "connection"
      },

      "file_pointer": "variant_clusters.json#cluster_connect_001"
    }
    // ... more canonical examples
  }
}
```

### 3. Variant Clusters (variant_clusters.json)

**Purpose:** Complete clusters with all tiers

```json
{
  "version": "1.0.0",
  "count": 102,

  "clusters": {
    "cluster_connect_001": {
      "cluster_id": "cluster_connect_001",
      "operation": "connect",
      "canonical_id": "ex_abc123",
      "total_occurrences": 14,

      "tiers": {
        "a0": {
          "example_id": "ex_abc123",
          "occurrences": 8,
          "similarity": 1.0,
          "pointer": "canonical_examples.json#ex_abc123"
        },

        "a1": [
          {
            "example_id": "ex_jkl345",
            "occurrences": 3,
            "similarity": 0.95,
            "diff_summary": "Different clientId parameter",
            "code": "ib.connect('127.0.0.1', 7497, clientId=2)",
            "sources": [
              {"file": "ib.md", "line": 156},
              {"file": "guide.md", "line": 89}
            ]
          },
          {
            "example_id": "ex_mno678",
            "occurrences": 2,
            "similarity": 0.92,
            "diff_summary": "Uses 'localhost' instead of IP",
            "code": "ib.connect('localhost', 7497, clientId=1)",
            "sources": [
              {"file": "ib.md", "line": 301}
            ]
          }
        ],

        "a2": [
          {
            "example_id": "ex_pqr901",
            "occurrences": 1,
            "similarity": 0.87,
            "diff_summary": "Adds timeout parameter",
            "unique_information": ["Shows timeout parameter usage"],
            "code": "ib.connect('127.0.0.1', 7497, clientId=1, timeout=20)",
            "sources": [
              {"file": "guide.md", "line": 234}
            ]
          }
        ],

        "a3": []
      },

      "navigation": {
        "parent": "apex_index.json#connect",
        "canonical": "canonical_examples.json#ex_abc123",
        "variants": {
          "a1": 2,
          "a2": 1,
          "a3": 0
        }
      }
    }
    // ... more clusters
  }
}
```

---

## Retrieval Algorithm

### Fast Path (Canonical Only)

```python
def get_canonical_example(operation: str) -> CodeExample:
    """
    O(1) lookup to canonical example.

    Fast path for most common use case.
    """
    # 1. Load apex index (cached in memory)
    apex = load_apex_index()

    # 2. Direct lookup
    canonical_id = apex['operations'][operation]['canonical_id']

    # 3. Return canonical
    return load_canonical(canonical_id)
```

**Performance:**
- Apex lookup: O(1) - hash map
- Canonical load: O(1) - direct JSON pointer
- **Total: ~1-2ms**

### Tier Cascade (With Variants)

```python
def get_example_with_fallback(
    operation: str,
    requirements: List[str],
    min_confidence: float = 0.7
) -> dict:
    """
    Cascade through tiers until requirements met.

    Returns best matching example with tier info.
    """
    # 1. Start at apex
    apex = load_apex_index()
    op_info = apex['operations'][operation]

    # 2. Check canonical (a0)
    canonical = load_canonical(op_info['canonical_id'])
    if meets_requirements(canonical, requirements):
        return {
            'tier': 'a0',
            'example': canonical,
            'confidence': 1.0,
            'occurrences': canonical.occurrence_count
        }

    # 3. Load cluster for variants
    cluster = load_cluster(canonical.cluster_id)

    # 4. Check a1 tier
    for variant in cluster['tiers']['a1']:
        if meets_requirements(variant, requirements):
            return {
                'tier': 'a1',
                'example': variant,
                'confidence': 0.9,
                'similarity': variant.similarity,
                'diff': variant.diff_summary
            }

    # 5. Check a2 tier
    for variant in cluster['tiers']['a2']:
        if meets_requirements(variant, requirements):
            return {
                'tier': 'a2',
                'example': variant,
                'confidence': 0.75,
                'similarity': variant.similarity,
                'note': 'Significant variation from canonical'
            }

    # 6. Check a3 tier (rare/edge cases)
    for variant in cluster['tiers']['a3']:
        if meets_requirements(variant, requirements):
            return {
                'tier': 'a3',
                'example': variant,
                'confidence': 0.6,
                'similarity': variant.similarity,
                'warning': 'Uncommon pattern, verify applicability'
            }

    return None  # No match found
```

**Performance:**
- Apex: 1-2ms
- Canonical: 1-2ms
- Per tier check: 5-10ms
- **Worst case (all tiers): ~30-50ms**

---

## Benefits

### 1. Ultra-Fast Canonical Lookup
```
Query: "How to connect?"
  ↓ (1ms)
apex_index["connect"] → ex_abc123
  ↓ (1ms)
canonical_examples[ex_abc123] → Result
TOTAL: 2ms
```

### 2. Efficient Tier Traversal
```
Query: "Connect with error handling?"
  ↓ (2ms)
Check a0 → Basic connect (no error handling)
  ↓ (5ms)
Check a1 → Still no error handling
  ↓ (5ms)
Check a2 → Found! Connection + try/except
TOTAL: 12ms
```

### 3. Smart Caching
```python
# Cache apex index in memory (small, ~50KB)
apex_cache = load_apex_index()  # Once at startup

# Cache hot canonicals (most accessed)
canonical_cache = LRU(maxsize=50)

# Load variants on demand
variants = load_cluster(cluster_id)  # Only when needed
```

### 4. Training Optimization
```python
# Agent training: Start with most common patterns
for op in apex['quick_stats']['most_common']:
    canonical = get_canonical_example(op)
    train_on(canonical)  # High confidence, high occurrence

# Then learn variants
for tier in ['a1', 'a2', 'a3']:
    variants = get_variants_in_tier(op, tier)
    train_on(variants)  # Lower priority, but important edge cases
```

---

## File Size Estimates

Based on ~300 examples → ~100 canonical (after dedup):

```
apex_index.json          ~50 KB    (operation map, fast)
canonical_examples.json  ~200 KB   (100 examples + metadata)
variant_clusters.json    ~400 KB   (200 variants + diffs)
api_reference.json       ~300 KB   (API docs)
dedup_database.json      ~1.2 MB   (everything combined)

TOTAL: ~2.2 MB (easily fits in memory)
```

---

## Access Patterns

### Pattern 1: Quick Answer (90% of queries)
```
User: "Show me connect example"
  ↓
apex → canonical
DONE (2ms)
```

### Pattern 2: Specific Requirements (8% of queries)
```
User: "Connect with timeout"
  ↓
apex → canonical (no timeout)
  ↓
check a1 variants → Found timeout variant
DONE (12ms)
```

### Pattern 3: Edge Cases (2% of queries)
```
User: "Connect with SSL and retry logic"
  ↓
apex → canonical
  ↓
a1 → no match
  ↓
a2 → partial match (SSL only)
  ↓
a3 → found (SSL + retry)
DONE (30ms)
```

---

## Implementation Priority

1. **Phase 5 (Final Build):** Generate pyramid index
2. **Agent Training:** Use apex for fast lookup
3. **Production:** Cache apex + hot canonicals
4. **Optimization:** Pre-load most common operations

---

## Configuration

```yaml
# config.yaml

output:
  # Pyramid index generation
  pyramid_index:
    enabled: true
    apex_file: apex_index.json
    canonical_file: canonical_examples.json
    clusters_file: variant_clusters.json

  # Caching strategy
  cache:
    apex_in_memory: true        # Always cache apex
    canonical_lru_size: 50      # Cache top 50 canonicals
    preload_common: true        # Preload most common ops

  # Index optimization
  optimization:
    compress_json: false        # Keep readable for now
    dedupe_sources: true        # Reduce source list size
    inline_small_variants: true # Inline variants < 3
```

---

This pyramid structure gives you:
✅ **O(1) canonical lookup** (apex → direct pointer)
✅ **Tier cascade** (a0 → a1 → a2 → a3)
✅ **Minimal redundancy** (pointers, not copies)
✅ **Fast training** (start at top, cascade down)
✅ **Memory efficient** (~2MB total, cache apex)
✅ **Clear hierarchy** (pyramid visualization)

Perfect for your retrieval strategy!
