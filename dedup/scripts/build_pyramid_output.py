#!/usr/bin/env python3
"""
Quick pyramid output generator - creates 3-layer structure from MD files.
This is a working prototype to demonstrate the pyramid architecture.
"""

import json
import re
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Source docs directory
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "pyramid_index"

def extract_code_blocks(md_file):
    """Extract Python code blocks from markdown file."""
    content = md_file.read_text(encoding='utf-8')

    # Find all Python code blocks
    pattern = r'```python\n(.*?)```'
    blocks = re.findall(pattern, content, re.DOTALL)

    examples = []
    for i, code in enumerate(blocks):
        code = code.strip()
        if not code or len(code) < 10:  # Skip tiny examples
            continue

        # Determine operation from code
        operation = "unknown"
        if "connect" in code.lower():
            operation = "connect"
        elif "reqhistoricaldata" in code.lower() or "historical" in code.lower():
            operation = "reqHistoricalData"
        elif "placeorder" in code.lower() or "order" in code.lower():
            operation = "placeOrder"
        elif "contract" in code.lower():
            operation = "contract_creation"
        elif "qualify" in code.lower():
            operation = "qualifyContracts"
        elif "ticker" in code.lower():
            operation = "ticker_subscription"
        elif "bars" in code.lower():
            operation = "bars_request"
        elif "position" in code.lower():
            operation = "positions"

        # Create hash for deduplication
        normalized = re.sub(r'\s+', ' ', code.lower())
        code_hash = hashlib.md5(normalized.encode()).hexdigest()[:8]

        examples.append({
            'id': f'ex_{code_hash}',
            'operation': operation,
            'code': code,
            'source': str(md_file.name),
            'normalized': normalized
        })

    return examples

def cluster_examples(examples):
    """Group examples by operation and detect duplicates."""
    clusters = defaultdict(list)

    for ex in examples:
        clusters[ex['operation']].append(ex)

    # For each cluster, detect duplicates
    result = {}
    for operation, exs in clusters.items():
        # Group by normalized code hash
        hash_groups = defaultdict(list)
        for ex in exs:
            normalized = ex['normalized']
            hash_key = hashlib.md5(normalized.encode()).hexdigest()[:8]
            hash_groups[hash_key].append(ex)

        # Assign tiers based on occurrence count
        tiers = {'a0': [], 'a1': [], 'a2': [], 'a3': []}

        for hash_key, group in hash_groups.items():
            count = len(group)
            canonical = group[0]  # First one is canonical
            canonical['occurrences'] = count

            # Determine tier by occurrence
            if count >= 5:
                tier = 'a0'
                similarity = 1.0
            elif count >= 3:
                tier = 'a1'
                similarity = 0.95
            elif count >= 2:
                tier = 'a2'
                similarity = 0.87
            else:
                tier = 'a3'
                similarity = 0.75

            canonical['tier'] = tier
            canonical['similarity'] = similarity
            tiers[tier].append(canonical)

        result[operation] = tiers

    return result

def build_layer1_apex(clusters):
    """Build Layer 1: Apex indexes."""
    apex_popular = []
    apex_alpha = defaultdict(list)

    # Calculate total mentions per operation
    op_stats = []
    for operation, tiers in clusters.items():
        total_mentions = sum(ex['occurrences'] for tier in tiers.values() for ex in tier)
        num_examples = sum(len(tier) for tier in tiers.values())
        max_depth = max(int(tier[1]) for tier in tiers.keys() if tiers[tier])

        # Find canonical (a0 tier, highest occurrence)
        canonical_line = 0
        if tiers['a0']:
            canonical_line = hash(tiers['a0'][0]['id']) % 1000
        elif tiers['a1']:
            canonical_line = hash(tiers['a1'][0]['id']) % 1000
        else:
            canonical_line = hash(operation) % 1000

        entry = f"{operation}:{total_mentions}:{num_examples}:{max_depth}:{canonical_line}"
        op_stats.append((total_mentions, operation, entry))

        # Add to alphabetical index
        first_letter = operation[0].upper() if operation else 'U'
        apex_alpha[first_letter].append(entry)

    # Sort by mentions (popularity)
    op_stats.sort(reverse=True)
    apex_popular = [entry for _, _, entry in op_stats]

    return {
        'apex_popular': apex_popular,
        'apex_alpha': dict(apex_alpha)
    }

def build_layer2_index(clusters):
    """Build Layer 2: Tag index with metadata."""
    tag_idx = defaultdict(list)
    meta = {}
    tag_dict = {}

    # Build tag mappings
    tag_mappings = {
        'con': ('connect', 'connection,ib.connect,client'),
        'his': ('reqHistoricalData', 'historical,data,bars,history'),
        'ord': ('placeOrder', 'order,trade,buy,sell,limit'),
        'ctr': ('contract_creation', 'contract,stock,forex,future'),
        'qua': ('qualifyContracts', 'qualify,validation,contract'),
        'tic': ('ticker_subscription', 'ticker,market,data,streaming'),
        'bar': ('bars_request', 'bars,ohlc,candles'),
        'pos': ('positions', 'position,portfolio,holdings')
    }

    line_num = 40
    for operation, tiers in clusters.items():
        # Find matching tag
        tag = 'unk'
        for t, (op, terms) in tag_mappings.items():
            if operation == op:
                tag = t
                tag_dict[tag] = terms
                break

        # Add entries for each tier
        for tier_name, tier_examples in tiers.items():
            for ex in tier_examples:
                tag_idx[tag].append(line_num)

                # Metadata: tier|similarity%|occurrences|type
                sim_pct = int(ex['similarity'] * 100)
                occ = ex['occurrences']
                typ = 'base' if tier_name == 'a0' else 'var' if tier_name in ['a1', 'a2'] else 'edge'
                meta[str(line_num)] = f"{tier_name}|{sim_pct}|{occ}|{typ}"

                line_num += 10

    return {
        'v': '2.0',
        'idx': dict(tag_idx),
        'meta': meta,
        'dict': tag_dict
    }

def build_layer3_content(clusters):
    """Build Layer 3: Content by tier."""
    tier_files = {
        'a1': [],  # canonical (note: using a1 as canonical, a0 reserved for tested)
        'a2': [],  # variants
        'a3': []   # edge cases
    }

    for operation, tiers in clusters.items():
        for tier_name, tier_examples in tiers.items():
            if tier_name == 'a0':
                # a0 examples go to a1 (canonical) until tested
                target = 'a1'
            else:
                target = tier_name

            for ex in tier_examples:
                entry = {
                    'topic': operation,
                    'tier': target,
                    'confidence': ex['similarity'],
                    'tags': [operation.lower(), 'ib_insync', 'python'],
                    'content': {
                        'title': f"{operation} example",
                        'data': ex['code'],
                        'examples': [ex['source']],
                        'related': []
                    },
                    'stats': {
                        'mentions': ex['occurrences'],
                        'sources': [ex['source']]
                    }
                }
                tier_files[target].append(entry)

    return tier_files

def main():
    print("=" * 80)
    print("Pyramid Index Builder - 3-Layer Architecture")
    print("=" * 80)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Step 1: Extract code from markdown files
    print("Step 1: Extracting code examples from markdown files...")
    all_examples = []
    md_files = list(DOCS_DIR.glob("*.md"))

    for md_file in md_files[:5]:  # Process first 5 files for now
        print(f"  Processing {md_file.name}...")
        examples = extract_code_blocks(md_file)
        all_examples.extend(examples)

    print(f"  Extracted {len(all_examples)} code examples")
    print()

    # Step 2: Cluster and deduplicate
    print("Step 2: Clustering and deduplicating...")
    clusters = cluster_examples(all_examples)
    print(f"  Found {len(clusters)} operation clusters")
    for op, tiers in clusters.items():
        total = sum(len(t) for t in tiers.values())
        print(f"    {op}: {total} examples")
    print()

    # Step 3: Build Layer 1 (Apex)
    print("Step 3: Building Layer 1 (Apex indexes)...")
    layer1 = build_layer1_apex(clusters)

    apex_popular_file = OUTPUT_DIR / "apex_popular.json"
    apex_alpha_file = OUTPUT_DIR / "apex_alpha.json"

    with open(apex_popular_file, 'w') as f:
        json.dump(layer1['apex_popular'], f, indent=2)

    with open(apex_alpha_file, 'w') as f:
        json.dump(layer1['apex_alpha'], f, indent=2)

    print(f"  ✓ apex_popular.json ({apex_popular_file.stat().st_size} bytes)")
    print(f"  ✓ apex_alpha.json ({apex_alpha_file.stat().st_size} bytes)")
    print()

    # Step 4: Build Layer 2 (Index)
    print("Step 4: Building Layer 2 (Tag index)...")
    layer2 = build_layer2_index(clusters)

    tag_index_file = OUTPUT_DIR / "tag_index.json"
    with open(tag_index_file, 'w') as f:
        json.dump(layer2, f, indent=2)

    print(f"  ✓ tag_index.json ({tag_index_file.stat().st_size} bytes)")
    print()

    # Step 5: Build Layer 3 (Content)
    print("Step 5: Building Layer 3 (Content tiers)...")
    layer3 = build_layer3_content(clusters)

    tier_files = {
        'tier_a1_canonical.json': layer3['a1'],
        'tier_a2_variants.json': layer3['a2'],
        'tier_a3_edge.json': layer3['a3']
    }

    for filename, content in tier_files.items():
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(content, f, indent=2)
        print(f"  ✓ {filename} ({filepath.stat().st_size} bytes, {len(content)} entries)")

    print()

    # Generate summary
    print("=" * 80)
    print("PYRAMID INDEX GENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Output location: {OUTPUT_DIR}")
    print()
    print("Layer 1 (Apex):")
    print(f"  - apex_popular.json: {len(layer1['apex_popular'])} operations (sorted by popularity)")
    print(f"  - apex_alpha.json: {len(layer1['apex_alpha'])} letter groups (alphabetical)")
    print()
    print("Layer 2 (Index):")
    print(f"  - tag_index.json: {len(layer2['idx'])} tags, {len(layer2['meta'])} metadata entries")
    print()
    print("Layer 3 (Content):")
    print(f"  - tier_a1_canonical.json: {len(layer3['a1'])} canonical examples")
    print(f"  - tier_a2_variants.json: {len(layer3['a2'])} variant examples")
    print(f"  - tier_a3_edge.json: {len(layer3['a3'])} edge case examples")
    print()

    total_size = sum((OUTPUT_DIR / f).stat().st_size for f in
                     ['apex_popular.json', 'apex_alpha.json', 'tag_index.json',
                      'tier_a1_canonical.json', 'tier_a2_variants.json', 'tier_a3_edge.json'])
    print(f"Total output size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print()
    print("Next steps:")
    print("  1. Review the generated pyramid structure")
    print("  2. Test query performance on the index")
    print("  3. Expand to process all MD files")
    print("  4. Add testing phase for confidence scoring")
    print()

if __name__ == "__main__":
    main()
