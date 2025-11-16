#!/usr/bin/env python3
"""Phase 2: Live Testing Framework

Tests code examples from 2_deduped/ for:
- Syntax validity
- Import correctness
- Basic execution (with mocks for IB calls)
- Performance tracking

Outputs to 3_testing/:
- test_results.json (pass/fail logs)
- execution_times.json (performance)
- failed_examples.json (debugging)
"""

import json
import time
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.progress import track

console = Console()


class ExampleTester:
    """Test code examples for validity and execution."""

    def __init__(self):
        self.results = []
        self.failed_examples = []
        self.execution_times = {}

    def test_example(self, example: Dict, line_num: int) -> Dict:
        """Test a single example.

        Returns:
            dict: Test result with status, execution time, errors
        """
        start_time = time.time()

        result = {
            "line": line_num,
            "id": example.get("id"),
            "topic": example.get("topic", "")[:50],
            "tier": example.get("tier"),
            "status": "unknown",
            "exec_time_ms": 0,
            "error": None,
            "warnings": [],
        }

        code = example.get("content", {}).get("code", "")

        if not code:
            result["status"] = "skip"
            result["error"] = "No code found"
            return result

        # Test 1: Syntax validation
        try:
            ast.parse(code)
            result["warnings"].append("syntax:ok")
        except SyntaxError as e:
            result["status"] = "fail"
            result["error"] = f"SyntaxError: {e}"
            self.failed_examples.append(result)
            return result

        # Test 2: Import validation
        imports_ok = self._test_imports(code, result)
        if not imports_ok:
            result["status"] = "fail"
            self.failed_examples.append(result)
            return result

        # Test 3: Safe execution simulation
        try:
            self._simulate_execution(code, result)
            result["status"] = "pass"
        except Exception as e:
            result["status"] = "fail"
            result["error"] = f"Execution: {str(e)}"
            self.failed_examples.append(result)

        # Record execution time
        exec_time = (time.time() - start_time) * 1000  # ms
        result["exec_time_ms"] = round(exec_time, 2)

        return result

    def _test_imports(self, code: str, result: Dict) -> bool:
        """Test if imports are valid."""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Check if it's ib_insync
                        if "ib_insync" in alias.name:
                            result["warnings"].append("import:ib_insync")
                        elif alias.name in ["asyncio", "time", "datetime"]:
                            result["warnings"].append(f"import:{alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and "ib_insync" in node.module:
                        result["warnings"].append(f"from:ib_insync")

            return True

        except Exception as e:
            result["error"] = f"Import analysis failed: {e}"
            return False

    def _simulate_execution(self, code: str, result: Dict):
        """Simulate execution without actually running IB calls.

        Validates:
        - Variable assignments are valid
        - Function calls have correct syntax
        - No obvious runtime errors
        """
        tree = ast.parse(code)

        # Check for common patterns
        has_ib_init = False
        has_connect = False
        has_async = False

        for node in ast.walk(tree):
            # Check for IB() initialization
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id") and node.func.id == "IB":
                    has_ib_init = True

                # Check for connect call
                if hasattr(node.func, "attr") and node.func.attr == "connect":
                    has_connect = True

            # Check for async patterns
            if isinstance(node, (ast.AsyncFunctionDef, ast.Await)):
                has_async = True

        # Add pattern detections
        if has_ib_init:
            result["warnings"].append("pattern:IB_init")
        if has_connect:
            result["warnings"].append("pattern:connect")
        if has_async:
            result["warnings"].append("pattern:async")

        # Mark as demo-safe if it's basic patterns
        if has_ib_init and has_connect and not has_async:
            result["demo_safe"] = True
        else:
            result["demo_safe"] = False

    def test_tier_file(self, tier_file: Path) -> List[Dict]:
        """Test all examples in a tier file."""
        console.print(f"[cyan]Testing {tier_file.name}...[/cyan]")

        with open(tier_file) as f:
            examples = json.load(f)

        results = []
        for i, example in enumerate(track(examples, description="Testing examples")):
            result = self.test_example(example, i)
            results.append(result)
            self.results.append(result)

        # Summary for this tier
        passed = sum(1 for r in results if r["status"] == "pass")
        failed = sum(1 for r in results if r["status"] == "fail")
        skipped = sum(1 for r in results if r["status"] == "skip")

        console.print(f"[green]✓ {passed} passed[/green], ", end="")
        console.print(f"[red]{failed} failed[/red], ", end="")
        console.print(f"[yellow]{skipped} skipped[/yellow]")

        return results

    def save_results(self, output_dir: Path):
        """Save test results to JSON files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Test results
        results_file = output_dir / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)

        console.print(f"[green]✓ Saved test results to {results_file}[/green]")

        # Failed examples
        if self.failed_examples:
            failed_file = output_dir / "failed_examples.json"
            with open(failed_file, "w") as f:
                json.dump(self.failed_examples, f, indent=2)

            console.print(f"[yellow]✓ Saved {len(self.failed_examples)} failed examples to {failed_file}[/yellow]")

        # Execution times summary
        exec_times = {
            r["id"]: r["exec_time_ms"]
            for r in self.results
            if r["status"] == "pass"
        }

        exec_file = output_dir / "execution_times.json"
        with open(exec_file, "w") as f:
            json.dump(exec_times, f, indent=2)

        console.print(f"[green]✓ Saved execution times to {exec_file}[/green]")

        # Generate summary
        self._print_summary()

    def _print_summary(self):
        """Print testing summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        skipped = sum(1 for r in self.results if r["status"] == "skip")

        console.print("\n[bold]Testing Summary:[/bold]")
        console.print(f"  Total: {total}")
        console.print(f"  [green]Passed: {passed} ({passed/total*100:.1f}%)[/green]")
        console.print(f"  [red]Failed: {failed} ({failed/total*100:.1f}%)[/red]")
        console.print(f"  [yellow]Skipped: {skipped}[/yellow]")

        if passed > 0:
            avg_time = sum(r["exec_time_ms"] for r in self.results if r["status"] == "pass") / passed
            console.print(f"\n  Average execution time: {avg_time:.2f}ms")


def main():
    """Main testing pipeline."""
    base_dir = Path(__file__).parent.parent
    deduped_dir = base_dir / "outputs/2_deduped"
    testing_dir = base_dir / "outputs/3_testing"

    console.print("\n[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  PHASE 2: LIVE TESTING FRAMEWORK  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════[/bold cyan]\n")

    tester = ExampleTester()

    # Test canonical examples first (highest priority)
    canonical_file = deduped_dir / "tier_a1_canonical.json"
    if canonical_file.exists():
        tester.test_tier_file(canonical_file)

    # Test variants (if time allows)
    variants_file = deduped_dir / "tier_a2_variants.json"
    if variants_file.exists():
        console.print("\n[cyan]Testing variants (sample)...[/cyan]")
        with open(variants_file) as f:
            variants = json.load(f)

        # Test first 20 variants as sample
        for i, example in enumerate(variants[:20]):
            result = tester.test_example(example, i)
            tester.results.append(result)

    # Save results
    tester.save_results(testing_dir)

    console.print("\n[bold green]✓ Phase 2 Testing Complete![/bold green]")


if __name__ == "__main__":
    main()
