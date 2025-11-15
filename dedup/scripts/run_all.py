#!/usr/bin/env python3
"""
Main pipeline script for running the complete deduplication process.

Usage:
    python scripts/run_all.py [--local-only] [--debug]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """Run the complete deduplication pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the ib_insync documentation deduplication pipeline"
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Use only local LLM (no Claude API)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with limited processing",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=["extract", "embed", "cluster", "merge", "build"],
        help="Skip specific stages",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("ib_insync Documentation Deduplication Pipeline")
    print("=" * 80)
    print()

    # TODO: Implement pipeline stages
    # 1. Load configuration
    # 2. Run extraction (01_extract.py)
    # 3. Run embedding (02_embed.py)
    # 4. Run clustering (03_cluster.py)
    # 5. Run merging (04_merge.py)
    # 6. Run building (05_build.py)
    # 7. Generate final reports

    print("Pipeline not yet implemented. See dedup/TODO.md for implementation plan.")
    print()
    print("Next steps:")
    print("  1. Implement extraction in scripts/01_extract.py")
    print("  2. Implement embedding in scripts/02_embed.py")
    print("  3. Continue with remaining stages...")
    print()
    print("For now, you can run stages individually as they're implemented.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
