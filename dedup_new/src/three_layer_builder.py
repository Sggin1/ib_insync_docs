"""Build 3-layer optimized architecture per deduplication-architecture.md spec."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
from rich.console import Console

console = Console()


class TagCompressor:
    """Compress tags to 2-3 letter codes for size optimization."""

    def __init__(self):
        self.tag_map = {}  # short_tag -> full_terms
        self.reverse_map = {}  # full_term -> short_tag
        self.tag_counter = defaultdict(int)

    def analyze_tags(self, examples: List[Dict]):
        """Analyze all tags to build compression dictionary."""
        all_tags = set()
        for ex in examples:
            for tag in ex.get("tags", []):
                all_tags.add(tag.lower())
                self.tag_counter[tag.lower()] += 1

        # Build compression rules
        self._build_compression_rules(all_tags)

    def _build_compression_rules(self, tags: Set[str]):
        """Create 2-3 letter codes for tags."""
        # Common universal patterns (2 letters)
        common_patterns = {
            "error": "er",
            "async": "as",
            "connect": "co",
            "data": "da",
            "order": "or",
            "contract": "ct",
        }

        # Domain-specific (3 letters)
        for tag in sorted(tags, key=lambda t: self.tag_counter[t], reverse=True):
            if tag in common_patterns:
                short = common_patterns[tag]
            elif len(tag) <= 3:
                short = tag  # Already short
            else:
                # Take first 3 consonants or first 3 letters
                consonants = "".join(c for c in tag if c not in "aeiou")
                short = consonants[:3] if len(consonants) >= 3 else tag[:3]

            # Ensure uniqueness
            if short in self.tag_map:
                short = tag[:4]  # Fallback to 4 letters

            self.tag_map[short] = tag
            self.reverse_map[tag] = short

    def compress(self, tag: str) -> str:
        """Compress a tag to short form."""
        return self.reverse_map.get(tag.lower(), tag[:3])

    def get_dictionary(self) -> Dict[str, str]:
        """Get dictionary mapping short tags to full terms."""
        # Group related terms
        result = {}
        for short, full in self.tag_map.items():
            # Find related terms
            related = [full]
            # Add plurals, variations
            if full.endswith("s"):
                related.append(full[:-1])
            if full == "connect":
                related.extend(["connection", "connecting"])
            if full == "order":
                related.extend(["orders", "ordering", "trade"])

            result[short] = ",".join(related)

        return result


class ThreeLayerBuilder:
    """Build optimized 3-layer architecture."""

    def __init__(self):
        self.examples = []
        self.compressor = TagCompressor()
        self.line_counter = 0

    def load_merged_examples(self, json_path: Path):
        """Load merged examples."""
        console.print(f"[cyan]Loading from {json_path}...[/cyan]")
        with open(json_path) as f:
            data = json.load(f)
        self.examples = data.get("merged_examples", [])
        console.print(f"[green]✓ Loaded {len(self.examples)} examples[/green]")

    def build_layers(self, output_dir: Path):
        """Build all 3 layers."""
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print("\n[bold]Building 3-Layer Optimized Architecture...[/bold]\n")

        # Analyze tags for compression
        console.print("[cyan]Analyzing tags for compression...[/cyan]")
        self.compressor.analyze_tags(self.examples)

        # Layer 1: Apex (popular + alphabetical)
        console.print("[cyan]Layer 1: Building apex indexes...[/cyan]")
        apex_popular, apex_alpha = self._build_apex_layer()
        self._save_json(apex_popular, output_dir / "apex_popular.json")
        self._save_json(apex_alpha, output_dir / "apex_alpha.json")

        # Layer 2: Tag Index
        console.print("[cyan]Layer 2: Building tag index...[/cyan]")
        tag_index = self._build_tag_index()
        self._save_json(tag_index, output_dir / "tag_index.json")

        # Layer 3: Content (tiered)
        console.print("[cyan]Layer 3: Building content tiers...[/cyan]")
        self._build_content_tiers(output_dir)

        console.print("\n[bold green]✓ 3-layer architecture complete![/bold green]")
        self._print_summary(output_dir)

    def _build_apex_layer(self) -> tuple[List[str], Dict[str, List[str]]]:
        """Build apex indexes (popular + alphabetical)."""
        # Group by operation
        operations = defaultdict(list)
        for ex in self.examples:
            op = self._extract_operation(ex)
            operations[op].append(ex)

        # Build apex entries
        apex_entries = []
        for op, examples in operations.items():
            total_mentions = len(examples)
            num_examples = len(examples)
            depth = self._calculate_depth(examples)
            first_line = self.line_counter

            entry = f"{op}:{total_mentions}:{num_examples}:{depth}:{first_line}"
            apex_entries.append(entry)

            self.line_counter += num_examples

        # Sort by popularity (mentions)
        apex_popular = sorted(
            apex_entries, key=lambda e: int(e.split(":")[1]), reverse=True
        )

        # Sort alphabetically
        apex_alpha_dict = defaultdict(list)
        for entry in apex_entries:
            topic = entry.split(":")[0]
            first_letter = topic[0].upper()
            apex_alpha_dict[first_letter].append(entry)

        # Sort each letter group
        for letter in apex_alpha_dict:
            apex_alpha_dict[letter].sort()

        return apex_popular, dict(apex_alpha_dict)

    def _build_tag_index(self) -> Dict:
        """Build tag index with idx/meta/dict structure."""
        idx = defaultdict(list)  # tag -> [line_numbers]
        meta = {}  # line_number -> "tier|similarity|occurrences|type"

        line_num = 0
        for ex in self.examples:
            # Get compressed tags
            tags = ex.get("tags", [])
            for tag in tags:
                short_tag = self.compressor.compress(tag)
                idx[short_tag].append(line_num)

            # Build metadata
            tier = self._determine_tier(ex)
            similarity = int(ex.get("metadata", {}).get("confidence", 0.8) * 100)
            occurrences = len(ex.get("sources", []))
            typ = "base" if tier == "a1" else "var" if tier == "a2" else "edge"

            meta[str(line_num)] = f"{tier}|{similarity}|{occurrences}|{typ}"

            line_num += 1

        # Get dictionary
        dictionary = self.compressor.get_dictionary()

        return {"v": "2.0", "idx": dict(idx), "meta": meta, "dict": dictionary}

    def _build_content_tiers(self, output_dir: Path):
        """Build tier content files (a1, a2, a3)."""
        tiers = {"a1": [], "a2": [], "a3": []}

        for ex in self.examples:
            tier = self._determine_tier(ex)
            content = self._format_content(ex)
            tiers[tier].append(content)

        # Save tier files
        for tier_name, content in tiers.items():
            filename = output_dir / f"tier_{tier_name}_{'canonical' if tier_name == 'a1' else 'variants' if tier_name == 'a2' else 'edge'}.json"
            self._save_json(content, filename)

        console.print(
            f"[green]✓ Created {len(tiers['a1'])} canonical, {len(tiers['a2'])} variants, {len(tiers['a3'])} edge cases[/green]"
        )

    def _extract_operation(self, example: Dict) -> str:
        """Extract operation name from example."""
        # Use tags or description
        tags = example.get("tags", [])
        if tags:
            return tags[0].title()

        # Extract from description
        desc = example.get("description", "")
        words = desc.split()
        if words:
            return words[0].title()

        return "Misc"

    def _calculate_depth(self, examples: List[Dict]) -> int:
        """Calculate pyramid depth for operation."""
        # Count how many tiers are used
        tiers = set()
        for ex in examples:
            tier = self._determine_tier(ex)
            tiers.add(tier)

        return len(tiers)

    def _determine_tier(self, example: Dict) -> str:
        """Determine tier based on occurrences and confidence."""
        sources = len(example.get("sources", []))
        confidence = example.get("metadata", {}).get("confidence", 0.8)

        if sources >= 2 and confidence >= 0.9:
            return "a1"  # Canonical
        elif sources >= 1 or confidence >= 0.7:
            return "a2"  # Variant
        else:
            return "a3"  # Edge case

    def _format_content(self, example: Dict) -> Dict:
        """Format example for content tier."""
        return {
            "id": example.get("id"),
            "topic": example.get("description", "")[:50],
            "tier": self._determine_tier(example),
            "confidence": example.get("metadata", {}).get("confidence", 0.8),
            "tags": [
                self.compressor.compress(t) for t in example.get("tags", [])
            ],
            "content": {
                "code": example.get("code", ""),
                "language": example.get("language", "python"),
                "description": example.get("description", ""),
            },
            "stats": {
                "mentions": len(example.get("sources", [])),
                "sources": example.get("sources", []),
            },
        }

    def _save_json(self, data: Any, path: Path):
        """Save JSON with compact formatting."""
        with open(path, "w") as f:
            if isinstance(data, list) and len(data) > 0:
                # Compact list format
                json.dump(data, f, indent=None, separators=(",", ":"))
            else:
                # Pretty dict format
                json.dump(data, f, indent=2)

        size_kb = path.stat().st_size / 1024
        console.print(f"[green]✓ Saved {path.name} ({size_kb:.1f}KB)[/green]")

    def _print_summary(self, output_dir: Path):
        """Print summary of generated files."""
        console.print("\n[bold]3-Layer Architecture Summary:[/bold]\n")

        total_size = 0
        files = list(output_dir.glob("*.json"))

        console.print("[cyan]Layer 1: Apex Indexes[/cyan]")
        for f in ["apex_popular.json", "apex_alpha.json"]:
            path = output_dir / f
            if path.exists():
                size = path.stat().st_size / 1024
                total_size += size
                console.print(f"  {f}: {size:.1f}KB")

        console.print("\n[cyan]Layer 2: Tag Index[/cyan]")
        path = output_dir / "tag_index.json"
        if path.exists():
            size = path.stat().st_size / 1024
            total_size += size
            console.print(f"  tag_index.json: {size:.1f}KB")

        console.print("\n[cyan]Layer 3: Content Tiers[/cyan]")
        for f in output_dir.glob("tier_*.json"):
            size = f.stat().st_size / 1024
            total_size += size
            console.print(f"  {f.name}: {size:.1f}KB")

        console.print(f"\n[bold]Total Size: {total_size:.1f}KB[/bold]")
        console.print(f"[bold]RAM Footprint (Layers 1+2): {(total_size - sum((output_dir / f'tier_{t}.json').stat().st_size / 1024 for t in ['a1_canonical', 'a2_variants', 'a3_edge'] if (output_dir / f'tier_{t}.json').exists())):.1f}KB[/bold]")


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent
    merged_json = base_dir / "outputs/2_merged/merged_examples.json"
    output_dir = base_dir / "outputs/5_final_v2"

    builder = ThreeLayerBuilder()
    builder.load_merged_examples(merged_json)
    builder.build_layers(output_dir)

    console.print("\n[bold green]✓ 3-layer optimized architecture complete![/bold green]")
    console.print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
