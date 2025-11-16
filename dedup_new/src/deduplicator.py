"""Deduplication logic for code examples."""

import re
from typing import List, Dict, Set
from rapidfuzz import fuzz
from rich.console import Console
from rich.progress import track

from models import CodeExample, DuplicateCluster, MergedExample, DeduplicationResult
from ai_client import OpenRouterClient

console = Console()


class Deduplicator:
    """Find and merge duplicate code examples."""

    def __init__(self, similarity_threshold: float = 0.85, ai_client: OpenRouterClient = None):
        """Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity (0-1) to consider duplicates
            ai_client: OpenRouter client for AI-based merging
        """
        self.similarity_threshold = similarity_threshold
        self.ai_client = ai_client

    def deduplicate(self, examples: List[CodeExample]) -> DeduplicationResult:
        """Find duplicates and merge them."""
        console.print(f"\n[bold]Starting deduplication...[/bold]")
        console.print(f"  Similarity threshold: {self.similarity_threshold}")
        console.print(f"  Total examples: {len(examples)}\n")

        # Step 1: Find duplicate clusters
        clusters = self._find_clusters(examples)
        console.print(f"[green]✓ Found {len(clusters)} clusters[/green]\n")

        # Step 2: Merge each cluster using AI
        merged_examples = []
        console.print("[bold]Merging clusters with AI...[/bold]")

        for cluster in track(clusters, description="Merging..."):
            merged = self.ai_client.merge_examples(cluster.examples, cluster.cluster_id)
            merged_examples.append(merged)

        # Step 3: Create result
        original_count = len(examples)
        merged_count = len(merged_examples)
        dedup_ratio = (original_count - merged_count) / original_count if original_count > 0 else 0

        result = DeduplicationResult(
            merged_examples=merged_examples,
            original_count=original_count,
            merged_count=merged_count,
            deduplication_ratio=dedup_ratio,
            clusters=clusters,
            stats={
                "clusters": len(clusters),
                "singleton_clusters": sum(1 for c in clusters if len(c.examples) == 1),
                "multi_example_clusters": sum(1 for c in clusters if len(c.examples) > 1),
                "max_cluster_size": max((len(c.examples) for c in clusters), default=0),
            },
            cost_info=self.ai_client.get_cost_summary() if self.ai_client else None,
        )

        # Print summary
        self._print_summary(result)

        return result

    def _find_clusters(self, examples: List[CodeExample]) -> List[DuplicateCluster]:
        """Find clusters of similar examples using string similarity."""
        clusters = []
        processed: Set[str] = set()

        console.print("[cyan]Finding duplicate clusters...[/cyan]")

        for i, example in enumerate(track(examples, description="Clustering")):
            if example.id in processed:
                continue

            # Start new cluster with this example
            cluster_examples = [example]
            processed.add(example.id)

            # Find similar examples
            for j, other in enumerate(examples):
                if i == j or other.id in processed:
                    continue

                similarity = self._calculate_similarity(example.code, other.code)

                if similarity >= self.similarity_threshold:
                    cluster_examples.append(other)
                    processed.add(other.id)

            # Calculate average similarity within cluster
            avg_similarity = self._cluster_similarity(cluster_examples)

            cluster = DuplicateCluster(
                cluster_id=f"cluster_{len(clusters):04d}",
                examples=cluster_examples,
                similarity_score=avg_similarity,
                canonical=cluster_examples[0].id,  # Will be updated by AI
            )

            clusters.append(cluster)

        return clusters

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code snippets.

        Uses a combination of:
        - Ratio similarity (overall)
        - Token sort ratio (order-independent)
        - Normalized code comparison
        """
        # Normalize code first
        norm1 = self._normalize_code(code1)
        norm2 = self._normalize_code(code2)

        # Calculate multiple similarity metrics
        ratio = fuzz.ratio(norm1, norm2) / 100.0
        token_sort = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        token_set = fuzz.token_set_ratio(norm1, norm2) / 100.0

        # Weighted average (favor exact matches)
        similarity = (ratio * 0.5) + (token_sort * 0.3) + (token_set * 0.2)

        return similarity

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison.

        Removes:
        - Extra whitespace
        - Comments
        - Variable name differences (optional)
        """
        # Remove comments
        code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)

        # Normalize whitespace
        code = re.sub(r"\s+", " ", code)

        # Remove leading/trailing whitespace
        code = code.strip()

        # Lowercase for case-insensitive comparison
        code = code.lower()

        return code

    def _cluster_similarity(self, examples: List[CodeExample]) -> float:
        """Calculate average similarity within a cluster."""
        if len(examples) <= 1:
            return 1.0

        similarities = []
        for i in range(len(examples)):
            for j in range(i + 1, len(examples)):
                sim = self._calculate_similarity(examples[i].code, examples[j].code)
                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 1.0

    def _print_summary(self, result: DeduplicationResult):
        """Print deduplication summary."""
        console.print("\n[bold green]✓ Deduplication Complete![/bold green]\n")

        console.print("[bold]Results:[/bold]")
        console.print(f"  Original examples: {result.original_count}")
        console.print(f"  Merged examples: {result.merged_count}")
        console.print(
            f"  Deduplication ratio: {result.deduplication_ratio:.1%} reduction"
        )

        console.print(f"\n[bold]Cluster Stats:[/bold]")
        console.print(f"  Total clusters: {result.stats['clusters']}")
        console.print(f"  Singleton clusters: {result.stats['singleton_clusters']}")
        console.print(f"  Multi-example clusters: {result.stats['multi_example_clusters']}")
        console.print(f"  Largest cluster: {result.stats['max_cluster_size']} examples")

        if result.cost_info:
            console.print(f"\n[bold]API Costs:[/bold]")
            console.print(f"  Total cost: ${result.cost_info['total_cost']:.4f}")
            console.print(f"  Input tokens: {result.cost_info['input_tokens']:,}")
            console.print(f"  Output tokens: {result.cost_info['output_tokens']:,}")
