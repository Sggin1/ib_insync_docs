"""Extract code examples from markdown files."""

import re
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console

from models import CodeExample, ExtractionResult

console = Console()


class MarkdownExtractor:
    """Extract code examples from markdown files."""

    def __init__(self, min_code_length: int = 20):
        self.min_code_length = min_code_length
        self.example_counter = 0

    def extract_from_file(self, file_path: Path) -> List[CodeExample]:
        """Extract all code examples from a markdown file."""
        console.print(f"[cyan]Extracting from {file_path.name}...[/cyan]")

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Error reading {file_path}: {e}[/red]")
            return []

        examples = []
        current_heading = None

        # Track line numbers
        lines = content.split("\n")

        for i, line in enumerate(lines, start=1):
            # Track current section heading
            if line.startswith("#"):
                current_heading = line.lstrip("#").strip()

        # Extract fenced code blocks with regex
        # Pattern: ```language\ncode\n```
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or "python"
            code = match.group(2).strip()

            # Skip short snippets
            if len(code) < self.min_code_length:
                continue

            # Find line number of this code block
            line_number = content[: match.start()].count("\n") + 1

            # Find the heading for this code block
            heading = self._find_heading_for_line(lines, line_number)

            # Extract context (text before code block)
            context = self._extract_context(content, match.start())

            # Generate unique ID
            example_id = self._generate_id(code, file_path.name)

            # Auto-detect tags
            tags = self._detect_tags(code, context, heading)

            example = CodeExample(
                id=example_id,
                code=code,
                language=language,
                context=context,
                source_file=str(file_path.name),
                line_number=line_number,
                heading=heading,
                tags=tags,
            )

            examples.append(example)

        console.print(f"[green]  ✓ Found {len(examples)} examples[/green]")
        return examples

    def extract_from_directory(
        self, dir_path: Path, patterns: List[str] = None, exclude: List[str] = None
    ) -> ExtractionResult:
        """Extract from all markdown files in directory."""
        patterns = patterns or ["*.md"]
        exclude = exclude or []

        all_examples = []
        files_processed = []

        # Find all matching files
        md_files = []
        for pattern in patterns:
            md_files.extend(dir_path.glob(pattern))

        # Filter excluded files
        md_files = [f for f in md_files if f.name not in exclude]

        console.print(f"\n[bold]Processing {len(md_files)} markdown files...[/bold]\n")

        for md_file in md_files:
            examples = self.extract_from_file(md_file)
            all_examples.extend(examples)
            files_processed.append(str(md_file.name))

        result = ExtractionResult(
            examples=all_examples,
            total_files=len(files_processed),
            total_examples=len(all_examples),
            files_processed=files_processed,
            extraction_stats={
                "avg_examples_per_file": (
                    len(all_examples) / len(files_processed) if files_processed else 0
                ),
                "languages": self._count_languages(all_examples),
            },
        )

        console.print(f"\n[bold green]✓ Extraction complete![/bold green]")
        console.print(f"  Files: {result.total_files}")
        console.print(f"  Examples: {result.total_examples}")

        return result

    def _find_heading_for_line(self, lines: List[str], line_number: int) -> Optional[str]:
        """Find the most recent heading before a line."""
        for i in range(line_number - 1, -1, -1):
            if lines[i].startswith("#"):
                return lines[i].lstrip("#").strip()
        return None

    def _extract_context(self, content: str, code_start: int, max_length: int = 200) -> Optional[str]:
        """Extract text context before code block."""
        # Look backwards from code block
        before_code = content[:code_start].strip()

        # Find last paragraph
        paragraphs = before_code.split("\n\n")
        if not paragraphs:
            return None

        last_para = paragraphs[-1].strip()

        # Remove markdown formatting
        last_para = re.sub(r"[#*`_]", "", last_para)
        last_para = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", last_para)  # Remove links

        # Truncate if too long
        if len(last_para) > max_length:
            last_para = last_para[:max_length] + "..."

        return last_para if last_para else None

    def _generate_id(self, code: str, filename: str) -> str:
        """Generate unique ID for code example."""
        self.example_counter += 1
        # Use hash of code + counter for uniqueness
        hash_part = hashlib.md5(code.encode()).hexdigest()[:8]
        return f"ex_{self.example_counter:04d}_{hash_part}"

    def _detect_tags(self, code: str, context: Optional[str], heading: Optional[str]) -> List[str]:
        """Auto-detect tags from code, context, and heading."""
        tags = set()

        # Keywords to look for
        keywords = {
            "connect": ["connect", "connection", "IB()"],
            "order": ["placeOrder", "Order", "LimitOrder", "MarketOrder"],
            "contract": ["Contract", "Stock", "Option", "Future"],
            "data": ["reqMktData", "reqHistoricalData", "BarData"],
            "async": ["async", "await", "asyncio"],
            "event": ["event", "pendingTickersEvent", "orderStatusEvent"],
            "portfolio": ["portfolio", "positions", "accountValues"],
            "error": ["error", "exception", "try", "except"],
        }

        # Check code
        code_lower = code.lower()
        for tag, patterns in keywords.items():
            if any(pattern.lower() in code_lower for pattern in patterns):
                tags.add(tag)

        # Check context
        if context:
            context_lower = context.lower()
            for tag, patterns in keywords.items():
                if any(pattern.lower() in context_lower for pattern in patterns):
                    tags.add(tag)

        # Check heading
        if heading:
            heading_lower = heading.lower()
            for tag, patterns in keywords.items():
                if any(pattern.lower() in heading_lower for pattern in patterns):
                    tags.add(tag)

        return sorted(list(tags))

    def _count_languages(self, examples: List[CodeExample]) -> dict:
        """Count examples by language."""
        counts = {}
        for ex in examples:
            counts[ex.language] = counts.get(ex.language, 0) + 1
        return counts
