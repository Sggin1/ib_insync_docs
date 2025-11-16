#!/usr/bin/env python3
"""Main script to run documentation deduplication."""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv
from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import ExtractionResult, DeduplicationResult
from extractor import MarkdownExtractor
from ai_client import OpenRouterClient
from deduplicator import Deduplicator

console = Console()


class DedupPipeline:
    """Main deduplication pipeline."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize pipeline with configuration."""
        # Load environment variables
        load_dotenv()

        # Load config
        config_file = Path(__file__).parent.parent / config_path
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file) as f:
            self.config = yaml.safe_load(f)

        # Setup paths
        self.root = Path(__file__).parent.parent
        self.docs_dir = self.root / self.config["extraction"]["source_dir"]
        self.output_dir = self.root / "outputs"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.extractor = MarkdownExtractor(
            min_code_length=self.config["extraction"]["code"]["min_length"]
        )

        self.ai_client = OpenRouterClient(
            model=self.config["ai"]["openrouter"]["model"],
            base_url=self.config["ai"]["openrouter"]["base_url"],
            max_tokens=self.config["ai"]["openrouter"]["max_tokens"],
            temperature=self.config["ai"]["openrouter"]["temperature"],
            track_costs=self.config["ai"]["openrouter"]["track_costs"],
        )

        self.deduplicator = Deduplicator(
            similarity_threshold=self.config["merging"]["similarity_threshold"],
            ai_client=self.ai_client,
        )

        # Development mode
        self.dev_mode = self.config.get("development", {}).get("enabled", False)

    def run(self):
        """Run complete pipeline."""
        start_time = time.time()

        console.print("\n[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]  IB_INSYNC DOCUMENTATION DEDUPLICATION  [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════[/bold cyan]\n")

        try:
            # Step 1: Extract examples
            console.rule("[bold]Step 1: Extract Code Examples[/bold]")
            extraction_result = self._extract()
            self._save_extraction(extraction_result)

            # Development mode limit
            if self.dev_mode:
                max_examples = self.config["development"]["max_examples"]
                console.print(
                    f"\n[yellow]Development mode: limiting to {max_examples} examples[/yellow]"
                )
                extraction_result.examples = extraction_result.examples[:max_examples]

            # Step 2: Deduplicate
            console.rule("\n[bold]Step 2: Deduplicate Examples[/bold]")
            dedup_result = self._deduplicate(extraction_result)
            self._save_deduplication(dedup_result)

            # Step 3: Generate reports
            console.rule("\n[bold]Step 3: Generate Reports[/bold]")
            self._generate_reports(extraction_result, dedup_result)

            # Summary
            elapsed = time.time() - start_time
            self._print_final_summary(extraction_result, dedup_result, elapsed)

            console.print("\n[bold green]✓ Pipeline completed successfully![/bold green]\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Pipeline interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[bold red]✗ Pipeline failed: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    def _extract(self) -> ExtractionResult:
        """Extract code examples from markdown files."""
        include_patterns = self.config["extraction"]["include_patterns"]
        exclude_patterns = self.config["extraction"]["exclude_patterns"]

        result = self.extractor.extract_from_directory(
            self.docs_dir, patterns=include_patterns, exclude=exclude_patterns
        )

        return result

    def _deduplicate(self, extraction_result: ExtractionResult) -> DeduplicationResult:
        """Deduplicate extracted examples."""
        result = self.deduplicator.deduplicate(extraction_result.examples)
        return result

    def _save_extraction(self, result: ExtractionResult):
        """Save extraction results."""
        output_path = self.output_dir / "1_extracted" / "examples.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = {
            "examples": [ex.model_dump() for ex in result.examples],
            "total_files": result.total_files,
            "total_examples": result.total_examples,
            "files_processed": result.files_processed,
            "extraction_stats": result.extraction_stats,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]✓ Saved extraction results to {output_path}[/green]")

    def _save_deduplication(self, result: DeduplicationResult):
        """Save deduplication results."""
        output_path = self.output_dir / "2_merged" / "merged_examples.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = {
            "merged_examples": [ex.model_dump() for ex in result.merged_examples],
            "original_count": result.original_count,
            "merged_count": result.merged_count,
            "deduplication_ratio": result.deduplication_ratio,
            "clusters": [c.model_dump() for c in result.clusters],
            "stats": result.stats,
            "cost_info": result.cost_info,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]✓ Saved deduplication results to {output_path}[/green]")

    def _generate_reports(self, extraction: ExtractionResult, dedup: DeduplicationResult):
        """Generate human-readable reports."""
        report_dir = self.output_dir / "3_final"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Generate markdown report
        report_path = report_dir / "DEDUPLICATION_REPORT.md"
        report = self._create_markdown_report(extraction, dedup)

        with open(report_path, "w") as f:
            f.write(report)

        console.print(f"[green]✓ Generated report at {report_path}[/green]")

        # Generate deduplicated markdown file
        dedup_md_path = report_dir / "ib_insync_deduplicated.md"
        dedup_md = self._create_deduplicated_markdown(dedup)

        with open(dedup_md_path, "w") as f:
            f.write(dedup_md)

        console.print(f"[green]✓ Generated deduplicated docs at {dedup_md_path}[/green]")

    def _create_markdown_report(
        self, extraction: ExtractionResult, dedup: DeduplicationResult
    ) -> str:
        """Create markdown report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# IB_INSYNC Documentation Deduplication Report

Generated: {timestamp}

## Summary

- **Original examples:** {dedup.original_count}
- **Deduplicated examples:** {dedup.merged_count}
- **Deduplication ratio:** {dedup.deduplication_ratio:.1%} reduction
- **Files processed:** {extraction.total_files}

## Extraction Stats

- **Total files:** {extraction.total_files}
- **Files processed:** {', '.join(extraction.files_processed)}
- **Languages:** {', '.join(f"{lang}: {count}" for lang, count in extraction.extraction_stats['languages'].items())}
- **Avg examples per file:** {extraction.extraction_stats['avg_examples_per_file']:.1f}

## Deduplication Stats

- **Total clusters:** {dedup.stats['clusters']}
- **Singleton clusters:** {dedup.stats['singleton_clusters']} (no duplicates)
- **Multi-example clusters:** {dedup.stats['multi_example_clusters']} (had duplicates)
- **Largest cluster:** {dedup.stats['max_cluster_size']} examples

## Cost Information

"""

        if dedup.cost_info:
            report += f"""- **Total cost:** ${dedup.cost_info['total_cost']:.4f}
- **Input tokens:** {dedup.cost_info['input_tokens']:,}
- **Output tokens:** {dedup.cost_info['output_tokens']:,}
- **Total tokens:** {dedup.cost_info['total_tokens']:,}
"""
        else:
            report += "Cost tracking not enabled.\n"

        report += "\n## Top Merged Examples\n\n"

        # Show first 10 merged examples
        for i, ex in enumerate(dedup.merged_examples[:10], 1):
            report += f"### {i}. {ex.description}\n\n"
            report += f"**Tags:** {', '.join(ex.tags)}\n\n"
            report += f"**Sources:** {len(ex.sources)} original examples\n\n"
            report += f"```{ex.language}\n{ex.code}\n```\n\n"
            if ex.notes:
                report += f"**Notes:** {ex.notes}\n\n"
            report += "---\n\n"

        return report

    def _create_deduplicated_markdown(self, dedup: DeduplicationResult) -> str:
        """Create deduplicated markdown documentation."""
        md = """# IB_INSYNC Complete Reference (Deduplicated)

This documentation has been automatically deduplicated to remove redundant examples
while preserving all unique information.

"""

        # Group by tags
        by_tag = {}
        for ex in dedup.merged_examples:
            for tag in ex.tags or ["uncategorized"]:
                if tag not in by_tag:
                    by_tag[tag] = []
                by_tag[tag].append(ex)

        # Generate sections
        for tag in sorted(by_tag.keys()):
            md += f"\n## {tag.title()}\n\n"

            for ex in by_tag[tag]:
                md += f"### {ex.description}\n\n"
                md += f"```{ex.language}\n{ex.code}\n```\n\n"
                if ex.notes:
                    md += f"> **Note:** {ex.notes}\n\n"

        return md

    def _print_final_summary(
        self, extraction: ExtractionResult, dedup: DeduplicationResult, elapsed: float
    ):
        """Print final summary."""
        console.print("\n[bold]═══════════════════════════════════════════════[/bold]")
        console.print("[bold]              FINAL SUMMARY                    [/bold]")
        console.print("[bold]═══════════════════════════════════════════════[/bold]\n")

        console.print(f"[bold]Files processed:[/bold] {extraction.total_files}")
        console.print(f"[bold]Original examples:[/bold] {dedup.original_count}")
        console.print(f"[bold]Deduplicated examples:[/bold] {dedup.merged_count}")
        console.print(
            f"[bold]Reduction:[/bold] {dedup.deduplication_ratio:.1%} ({dedup.original_count - dedup.merged_count} examples removed)"
        )

        if dedup.cost_info:
            console.print(f"\n[bold]API Cost:[/bold] ${dedup.cost_info['total_cost']:.4f}")

        console.print(f"\n[bold]Time elapsed:[/bold] {elapsed:.1f} seconds")

        console.print("\n[bold]Output files:[/bold]")
        console.print("  • outputs/1_extracted/examples.json")
        console.print("  • outputs/2_merged/merged_examples.json")
        console.print("  • outputs/3_final/DEDUPLICATION_REPORT.md")
        console.print("  • outputs/3_final/ib_insync_deduplicated.md")


def main():
    """Main entry point."""
    pipeline = DedupPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
