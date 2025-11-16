"""Build pyramid index structure from merged examples."""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from rich.console import Console

console = Console()


class PyramidBuilder:
    """Build pyramid index structure with a0-a3 tiers."""

    def __init__(self):
        self.examples = []
        self.operations = defaultdict(list)

    def load_merged_examples(self, json_path: Path):
        """Load merged examples from JSON."""
        console.print(f"[cyan]Loading merged examples from {json_path}...[/cyan]")

        with open(json_path) as f:
            data = json.load(f)

        self.examples = data.get("merged_examples", [])
        console.print(f"[green]✓ Loaded {len(self.examples)} examples[/green]")

    def build_pyramid(self, output_dir: Path):
        """Build complete pyramid structure."""
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print("\n[bold]Building Pyramid Index Structure...[/bold]\n")

        # Step 1: Organize by operation
        console.print("[cyan]Step 1: Organizing examples by operation...[/cyan]")
        self._organize_by_operation()

        # Step 2: Assign tiers within each operation
        console.print("[cyan]Step 2: Assigning similarity tiers...[/cyan]")
        clusters = self._create_clusters()

        # Step 3: Build apex index
        console.print("[cyan]Step 3: Building apex index...[/cyan]")
        apex_index = self._build_apex_index(clusters)
        self._save_json(apex_index, output_dir / "apex_index.json")

        # Step 4: Build canonical examples (a0 tier)
        console.print("[cyan]Step 4: Extracting canonical examples (a0 tier)...[/cyan]")
        canonical = self._build_canonical_examples(clusters)
        self._save_json(canonical, output_dir / "canonical_examples.json")

        # Step 5: Build variant clusters (a1-a3 tiers)
        console.print("[cyan]Step 5: Organizing variant clusters...[/cyan]")
        variants = self._build_variant_clusters(clusters)
        self._save_json(variants, output_dir / "variant_clusters.json")

        # Step 6: Build complete database
        console.print("[cyan]Step 6: Building complete database...[/cyan]")
        database = self._build_complete_database(apex_index, canonical, variants)
        self._save_json(database, output_dir / "dedup_database.json")

        console.print("\n[bold green]✓ Pyramid structure complete![/bold green]\n")

        # Print summary
        self._print_summary(apex_index, canonical, variants)

    def _organize_by_operation(self):
        """Group examples by operation/function."""
        for ex in self.examples:
            # Extract operation from tags or code
            operation = self._extract_operation(ex)
            self.operations[operation].append(ex)

        console.print(f"[green]✓ Found {len(self.operations)} unique operations[/green]")

    def _extract_operation(self, example: Dict) -> str:
        """Extract main operation from example."""
        code = example.get("code", "")
        tags = example.get("tags", [])

        # Try to find operation in code
        operations = {
            "connect": ["ib.connect", "IB().connect", "connectAsync"],
            "reqHistoricalData": ["reqHistoricalData", "reqHistoricalDataAsync"],
            "reqMktData": ["reqMktData", "reqMktDataAsync"],
            "placeOrder": ["placeOrder", "placeOrderAsync"],
            "cancelOrder": ["cancelOrder"],
            "reqPositions": ["reqPositions", "positions()"],
            "reqAccountSummary": ["reqAccountSummary"],
            "reqContractDetails": ["reqContractDetails"],
            "contract": ["Contract(", "Stock(", "Option(", "Future("],
            "order": ["Order(", "MarketOrder", "LimitOrder", "StopOrder"],
            "bracket": ["BracketOrder"],
            "ib_init": ["IB()", "ib = IB()"],
        }

        for op, patterns in operations.items():
            if any(pattern in code for pattern in patterns):
                return op

        # Fallback to first tag
        if tags:
            return tags[0]

        return "misc"

    def _create_clusters(self) -> Dict[str, Dict]:
        """Create clusters with tier assignments."""
        clusters = {}

        for operation, examples in self.operations.items():
            if not examples:
                continue

            # For now, treat first example as canonical (a0)
            # In a full implementation, would use similarity scores
            canonical = examples[0]
            variants = examples[1:] if len(examples) > 1 else []

            cluster = {
                "cluster_id": f"cluster_{operation}",
                "operation": operation,
                "canonical_id": canonical["id"],
                "total_occurrences": len(examples),
                "tiers": {
                    "a0": canonical,  # Canonical (most common)
                    "a1": [],  # Minor variants (85-95% similar)
                    "a2": [],  # Significant variants (75-85% similar)
                    "a3": [],  # Rare/edge cases (65-75% similar)
                },
            }

            # Assign variants to tiers based on source count
            # (In full implementation, would use actual similarity scores)
            for variant in variants:
                source_count = len(variant.get("sources", []))
                if source_count >= 2:
                    cluster["tiers"]["a1"].append(variant)
                elif source_count == 1:
                    cluster["tiers"]["a2"].append(variant)
                else:
                    cluster["tiers"]["a3"].append(variant)

            clusters[operation] = cluster

        return clusters

    def _build_apex_index(self, clusters: Dict) -> Dict:
        """Build apex index for O(1) operation lookup."""
        operations = {}

        for op, cluster in clusters.items():
            tier_dist = {
                "a0": 1,  # Always 1 canonical
                "a1": len(cluster["tiers"]["a1"]),
                "a2": len(cluster["tiers"]["a2"]),
                "a3": len(cluster["tiers"]["a3"]),
            }

            operations[op] = {
                "canonical_id": cluster["canonical_id"],
                "total_occurrences": cluster["total_occurrences"],
                "variant_count": sum(tier_dist.values()) - 1,  # Exclude a0
                "confidence": 1.0,
                "tier_distribution": tier_dist,
                "file_pointer": f"canonical_examples.json#{cluster['canonical_id']}",
            }

        # Calculate stats
        total_examples = sum(c["total_occurrences"] for c in clusters.values())
        total_canonical = len(clusters)

        # Find most common operations
        most_common = sorted(
            operations.keys(), key=lambda k: operations[k]["total_occurrences"], reverse=True
        )[:10]

        return {
            "version": "1.0.0",
            "created_at": "2025-11-16",
            "total_operations": len(operations),
            "total_examples": total_examples,
            "total_canonical": total_canonical,
            "operations": operations,
            "quick_stats": {
                "most_common": most_common,
                "avg_variants_per_operation": (
                    sum(op["variant_count"] for op in operations.values()) / len(operations)
                    if operations
                    else 0
                ),
                "deduplication_ratio": (
                    (total_examples - total_canonical) / total_examples if total_examples > 0 else 0
                ),
            },
        }

    def _build_canonical_examples(self, clusters: Dict) -> Dict:
        """Build canonical examples file (a0 tier only)."""
        examples = {}

        for op, cluster in clusters.items():
            canonical = cluster["tiers"]["a0"]
            canonical_id = canonical["id"]

            # Count variants
            variant_count = sum(
                len(cluster["tiers"][tier]) for tier in ["a1", "a2", "a3"]
            )

            examples[canonical_id] = {
                "id": canonical_id,
                "operation": op,
                "code": canonical.get("code", ""),
                "language": canonical.get("language", "python"),
                "description": canonical.get("description", ""),
                "occurrence_count": 1,  # Canonical count
                "tier": "a0",
                "is_canonical": True,
                "similarity": 1.0,
                "sources": [{"file": s, "line": None} for s in canonical.get("sources", [])],
                "variants": {
                    "a1": [v["id"] for v in cluster["tiers"]["a1"]],
                    "a2": [v["id"] for v in cluster["tiers"]["a2"]],
                    "a3": [v["id"] for v in cluster["tiers"]["a3"]],
                },
                "variant_count": variant_count,
                "total_occurrences": cluster["total_occurrences"],
                "metadata": {
                    "tags": canonical.get("tags", []),
                    "category": op,
                    "notes": canonical.get("notes", ""),
                },
                "file_pointer": f"variant_clusters.json#{cluster['cluster_id']}",
            }

        return {
            "version": "1.0.0",
            "tier": "a0",
            "count": len(examples),
            "examples": examples,
        }

    def _build_variant_clusters(self, clusters: Dict) -> Dict:
        """Build variant clusters file (complete clusters with all tiers)."""
        cluster_data = {}

        for op, cluster in clusters.items():
            canonical_id = cluster["canonical_id"]

            # Build tier structure
            tiers = {
                "a0": {
                    "example_id": canonical_id,
                    "occurrences": 1,
                    "similarity": 1.0,
                    "pointer": f"canonical_examples.json#{canonical_id}",
                },
                "a1": [],
                "a2": [],
                "a3": [],
            }

            # Add variants for each tier
            for tier_name in ["a1", "a2", "a3"]:
                for variant in cluster["tiers"][tier_name]:
                    tiers[tier_name].append({
                        "example_id": variant["id"],
                        "occurrences": len(variant.get("sources", [])),
                        "similarity": 0.85 if tier_name == "a1" else 0.75 if tier_name == "a2" else 0.65,
                        "diff_summary": variant.get("notes", ""),
                        "code": variant.get("code", ""),
                        "sources": [{"file": s} for s in variant.get("sources", [])],
                    })

            cluster_data[cluster["cluster_id"]] = {
                "cluster_id": cluster["cluster_id"],
                "operation": op,
                "canonical_id": canonical_id,
                "total_occurrences": cluster["total_occurrences"],
                "tiers": tiers,
                "navigation": {
                    "parent": f"apex_index.json#{op}",
                    "canonical": f"canonical_examples.json#{canonical_id}",
                    "variants": {
                        "a1": len(tiers["a1"]),
                        "a2": len(tiers["a2"]),
                        "a3": len(tiers["a3"]),
                    },
                },
            }

        return {
            "version": "1.0.0",
            "count": len(cluster_data),
            "clusters": cluster_data,
        }

    def _build_complete_database(
        self, apex: Dict, canonical: Dict, variants: Dict
    ) -> Dict:
        """Build complete database with all data."""
        return {
            "version": "1.0.0",
            "created_at": "2025-11-16",
            "description": "Complete deduplicated ib_insync documentation database",
            "structure": {
                "apex_index": "Master index for O(1) operation lookup",
                "canonical_examples": "All a0 tier canonical examples",
                "variant_clusters": "Complete clusters with a1-a3 variant tiers",
            },
            "stats": {
                "total_operations": apex["total_operations"],
                "total_examples": apex["total_examples"],
                "total_canonical": apex["total_canonical"],
                "deduplication_ratio": apex["quick_stats"]["deduplication_ratio"],
            },
            "apex_index": apex,
            "canonical_examples": canonical,
            "variant_clusters": variants,
        }

    def _save_json(self, data: Dict, path: Path):
        """Save JSON file with pretty formatting."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]✓ Saved {path.name}[/green]")

    def _print_summary(self, apex: Dict, canonical: Dict, variants: Dict):
        """Print pyramid structure summary."""
        console.print("[bold]Pyramid Structure Summary:[/bold]")
        console.print(f"  Operations: {apex['total_operations']}")
        console.print(f"  Canonical examples (a0): {canonical['count']}")

        # Count variants
        total_a1 = sum(
            len(c["tiers"]["a1"]) for c in variants["clusters"].values()
        )
        total_a2 = sum(
            len(c["tiers"]["a2"]) for c in variants["clusters"].values()
        )
        total_a3 = sum(
            len(c["tiers"]["a3"]) for c in variants["clusters"].values()
        )

        console.print(f"  Minor variants (a1): {total_a1}")
        console.print(f"  Significant variants (a2): {total_a2}")
        console.print(f"  Rare/edge cases (a3): {total_a3}")
        console.print(f"\n  Deduplication ratio: {apex['quick_stats']['deduplication_ratio']:.1%}")
        console.print(f"  Most common operations: {', '.join(apex['quick_stats']['most_common'][:5])}")


def main():
    """Main entry point."""
    from pathlib import Path

    # Paths
    base_dir = Path(__file__).parent.parent
    merged_json = base_dir / "outputs/2_merged/merged_examples.json"
    output_dir = base_dir / "outputs/5_final"

    # Build pyramid
    builder = PyramidBuilder()
    builder.load_merged_examples(merged_json)
    builder.build_pyramid(output_dir)

    console.print("\n[bold green]✓ Pyramid index structure complete![/bold green]")
    console.print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    main()
