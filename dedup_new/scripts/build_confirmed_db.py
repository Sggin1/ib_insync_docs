#!/usr/bin/env python3
"""Phase 3: Build Confirmed Database

Takes passing examples from testing and creates golden dataset with:
- Enhanced metadata (tested:pass|exec:Xms)
- Confidence boost to 1.0
- Only validated, working code
"""

import json
from pathlib import Path
from rich.console import Console

console = Console()


def build_confirmed_database():
    """Build confirmed database from test results."""
    base_dir = Path(__file__).parent.parent

    # Load test results
    test_results_file = base_dir / "outputs/3_testing/test_results.json"
    with open(test_results_file) as f:
        test_results = json.load(f)

    # Load original deduped data
    tag_index_file = base_dir / "outputs/2_deduped/tag_index.json"
    tier_a1_file = base_dir / "outputs/2_deduped/tier_a1_canonical.json"

    with open(tag_index_file) as f:
        tag_index = json.load(f)

    with open(tier_a1_file) as f:
        tier_a1 = json.load(f)

    console.print("[cyan]Building confirmed database...[/cyan]")

    # Filter passing examples
    passing_tests = {r["id"]: r for r in test_results if r["status"] == "pass"}

    confirmed_examples = []
    confirmed_metadata = {}

    for i, example in enumerate(tier_a1):
        example_id = example["id"]

        if example_id in passing_tests:
            test_result = passing_tests[example_id]

            # Enhance example with test data
            enhanced = example.copy()
            enhanced["confidence"] = 1.0  # Boost confidence
            enhanced["tested"] = {
                "status": "pass",
                "runs": 1,
                "success_rate": "100%",
                "avg_exec_time_ms": test_result["exec_time_ms"],
                "last_tested": "2025-11-16",
                "demo_safe": test_result.get("demo_safe", False),
                "warnings": test_result.get("warnings", []),
            }

            confirmed_examples.append(enhanced)

            # Update metadata with test results
            if str(i) in tag_index["meta"]:
                old_meta = tag_index["meta"][str(i)]
                tier, sim, occs, typ = old_meta.split("|")

                # Enhanced format: tier|similarity|occurrences|type|tested:status|exec:Xms
                new_meta = f"{tier}|100|{occs}|base|tested:pass|exec:{test_result['exec_time_ms']:.2f}ms"
                confirmed_metadata[str(i)] = new_meta

    # Create confirmed tag index
    confirmed_tag_index = {
        "v": "3.0",  # Version bump
        "idx": tag_index["idx"],
        "meta": confirmed_metadata,
        "dict": tag_index["dict"],
        "tested": {
            "total_tests": len(test_results),
            "passed": len(passing_tests),
            "failed": len(test_results) - len(passing_tests),
            "pass_rate": f"{len(passing_tests)/len(test_results)*100:.1f}%",
        },
    }

    # Save confirmed database
    confirmed_dir = base_dir / "outputs/4_confirmed"
    confirmed_dir.mkdir(parents=True, exist_ok=True)

    # Save enhanced examples
    confirmed_examples_file = confirmed_dir / "tier_a1_confirmed.json"
    with open(confirmed_examples_file, "w") as f:
        json.dump(confirmed_examples, f, indent=2)

    console.print(f"[green]✓ Saved {len(confirmed_examples)} confirmed examples[/green]")

    # Save enhanced tag index
    confirmed_index_file = confirmed_dir / "tag_index.json"
    with open(confirmed_index_file, "w") as f:
        json.dump(confirmed_tag_index, f, indent=2)

    console.print(f"[green]✓ Saved confirmed tag index[/green]")

    # Copy apex files (unchanged)
    for apex_file in ["apex_popular.json", "apex_alpha.json"]:
        src = base_dir / "outputs/2_deduped" / apex_file
        dst = confirmed_dir / apex_file
        if src.exists():
            import shutil

            shutil.copy(src, dst)
            console.print(f"[green]✓ Copied {apex_file}[/green]")

    # Print summary
    console.print("\n[bold]Confirmed Database Summary:[/bold]")
    console.print(f"  Total examples tested: {len(test_results)}")
    console.print(f"  Passed: {len(passing_tests)}")
    console.print(f"  Confirmed (a1): {len(confirmed_examples)}")
    console.print(f"  Pass rate: {len(passing_tests)/len(test_results)*100:.1f}%")

    avg_exec = sum(e["tested"]["avg_exec_time_ms"] for e in confirmed_examples) / len(
        confirmed_examples
    )
    console.print(f"  Average exec time: {avg_exec:.2f}ms")


def main():
    console.print("\n[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  PHASE 3: CONFIRMED DATABASE BUILDER  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════[/bold cyan]\n")

    build_confirmed_database()

    console.print("\n[bold green]✓ Phase 3 Complete![/bold green]")


if __name__ == "__main__":
    main()
