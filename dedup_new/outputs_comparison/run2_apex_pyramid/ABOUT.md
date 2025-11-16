# Run 2: Apex Pyramid Structure

**Approach:** 4-tier pyramid with apex index
**Date:** 2025-11-16 (second iteration)
**Structure:** Based on PYRAMID_INDEX.md specification

## Structure
- Apex index (master pointer)
- Canonical examples (a0/a1)
- Variant clusters (a2)
- Full database (a3)

## Files
- apex_index.json (6 KB) - Master index pointing to canonicals
- canonical_examples.json (29 KB) - Top tier examples
- variant_clusters.json (321 KB) - Grouped variants
- dedup_database.json (366 KB) - Complete database

Total: 722 KB across 4 files

## Characteristics
- ✅ Hierarchical structure
- ✅ Apex index for quick lookups
- ✅ Tier-based organization (a0, a1, a2, a3)
- ✅ Separated canonical vs variants
- ⚠️ Still loads full content files
- ❌ No tag compression
- ❌ No metadata filtering
