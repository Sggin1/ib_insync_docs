#!/usr/bin/env python3
"""Quick test to verify OpenRouter API key works."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("Testing OpenRouter API connection...")
print(f"Loading .env from: {env_file}")

try:
    from ai_client import OpenRouterClient

    # Initialize client
    client = OpenRouterClient(
        model="deepseek/deepseek-r1",
        max_tokens=100,
    )

    print(f"✓ Client initialized with model: {client.model}")

    # Test with a simple request
    print("\nTesting API call with simple request...")

    from models import CodeExample

    # Create a test example
    test_example = CodeExample(
        id="test_001",
        code="ib = IB()\nib.connect('127.0.0.1', 7497, clientId=1)",
        language="python",
        context="Test connection example",
        source_file="test.md",
        tags=["connection", "test"]
    )

    # Try to merge (with just one example, it should return quickly)
    merged = client.merge_examples([test_example], "test_cluster")

    print(f"✓ API call successful!")
    print(f"  Response ID: {merged.id}")
    print(f"  Description: {merged.description[:50]}...")

    # Show cost
    cost = client.get_cost_summary()
    print(f"\n✓ API test complete!")
    print(f"  Cost: ${cost['total_cost']:.6f}")
    print(f"  Tokens: {cost['total_tokens']}")

    print("\n✅ OpenRouter API key is working correctly!")
    print("Ready to run full deduplication with: python scripts/run_dedup.py")

except Exception as e:
    print(f"\n❌ API test failed: {e}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. Network connection problem")
    print("3. OpenRouter service issue")
    print("\nCheck your API key at: https://openrouter.ai/keys")
    sys.exit(1)
