#!/usr/bin/env python3
"""Test script to verify setup is correct."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("Testing imports...")

try:
    from models import CodeExample, DuplicateCluster, MergedExample, ExtractionResult, DeduplicationResult
    print("✓ models.py imports OK")
except Exception as e:
    print(f"✗ models.py import failed: {e}")
    sys.exit(1)

try:
    from extractor import MarkdownExtractor
    print("✓ extractor.py imports OK")
except Exception as e:
    print(f"✗ extractor.py import failed: {e}")
    sys.exit(1)

try:
    from ai_client import OpenRouterClient
    print("✓ ai_client.py imports OK")
except Exception as e:
    print(f"✗ ai_client.py import failed: {e}")
    sys.exit(1)

try:
    from deduplicator import Deduplicator
    print("✓ deduplicator.py imports OK")
except Exception as e:
    print(f"✗ deduplicator.py import failed: {e}")
    sys.exit(1)

# Test config loading
try:
    import yaml
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        config = yaml.safe_load(f)
    print("✓ config.yaml loads OK")
except Exception as e:
    print(f"✗ config.yaml load failed: {e}")
    sys.exit(1)

# Test docs directory exists
try:
    docs_dir = Path(__file__).parent.parent / "../docs"
    if docs_dir.exists():
        md_files = list(docs_dir.glob("*.md"))
        print(f"✓ docs directory found ({len(md_files)} .md files)")
    else:
        print("✗ docs directory not found")
        sys.exit(1)
except Exception as e:
    print(f"✗ docs directory check failed: {e}")
    sys.exit(1)

print("\n✓ All tests passed! Setup is ready.")
print("\nTo run deduplication:")
print("1. Add your OpenRouter API key to .env file")
print("2. Run: python scripts/run_dedup.py")
