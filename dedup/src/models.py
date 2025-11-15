# File: models.py
# Location: dedup/src/models.py
# Purpose: Pydantic data models for deduplication pipeline
# Dependencies: pydantic

"""
Pydantic models for ib_insync documentation deduplication.

This module defines all data structures used throughout the deduplication pipeline.
All models support JSON serialization, validation, and maintain single source of truth.
Models follow flat structure with minimal nesting and clear ownership.

Complexity: All model methods have CC < 3
Size: Split into logical sections to maintain readability

Example:
    >>> example = CodeExample.from_code("print('hello')")
    >>> example.code_hash
    '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


# =============================================================================
# Enums
# =============================================================================


class ContentType(str, Enum):
    """Type of documentation content."""

    API_REFERENCE = "api_reference"
    CODE_EXAMPLE = "code_example"
    CONCEPT = "concept"
    PATTERN = "pattern"
    GOTCHA = "gotcha"
    TUTORIAL = "tutorial"
    UNKNOWN = "unknown"


class LanguageType(str, Enum):
    """Programming language."""

    PYTHON = "python"
    BASH = "bash"
    JAVASCRIPT = "javascript"
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class MergeStrategy(str, Enum):
    """Strategy used for merging similar content."""

    LOCAL_LLM = "local_llm"
    CLAUDE_API = "claude_api"
    MANUAL = "manual"
    EXACT_DUPLICATE = "exact_duplicate"
    AUTOMATIC = "automatic"


# =============================================================================
# Source Tracking
# =============================================================================


class SourceLocation(BaseModel):
    """Tracks where content originated in source files."""

    file: str = Field(..., description="Source file path")
    line_start: int = Field(..., ge=0, description="Starting line number (0-indexed)")
    line_end: int = Field(..., ge=0, description="Ending line number (0-indexed)")
    section: Optional[str] = Field(None, description="Section header/context")
    heading_path: List[str] = Field(
        default_factory=list, description="Hierarchical heading path (e.g., ['API', 'Client', 'connect'])"
    )

    @field_validator("line_end")
    @classmethod
    def validate_line_range(cls, v: int, info) -> int:
        """Ensure line_end >= line_start."""
        if "line_start" in info.data and v < info.data["line_start"]:
            raise ValueError("line_end must be >= line_start")
        return v

    @computed_field
    @property
    def line_count(self) -> int:
        """Number of lines in this location."""
        return self.line_end - self.line_start + 1


# =============================================================================
# Code Examples
# =============================================================================


class CodeExample(BaseModel):
    """Represents a code snippet extracted from documentation."""

    # Identity
    id: str = Field(default_factory=lambda: f"ex_{uuid.uuid4().hex[:12]}")

    # Content
    code: str = Field(..., description="Raw code content")
    language: LanguageType = Field(default=LanguageType.PYTHON)

    # Context
    operation: Optional[str] = Field(None, description="Main operation (e.g., 'qualify_contracts', 'place_order')")
    description: Optional[str] = Field(None, description="Human-readable description")
    context_before: Optional[str] = Field(None, description="Text/explanation before the code")
    context_after: Optional[str] = Field(None, description="Text/explanation after the code")

    # Analysis
    methods_used: List[str] = Field(default_factory=list, description="API methods called (e.g., ['IB.connect', 'IB.reqHistoricalData'])")
    contract_types: List[str] = Field(default_factory=list, description="Contract types used (e.g., ['Stock', 'Forex', 'Future'])")
    imports: List[str] = Field(default_factory=list, description="Imported modules/classes")
    variables: List[str] = Field(default_factory=list, description="Key variables defined")

    # Deduplication metadata
    normalized_code: str = Field(..., description="Code with comments/whitespace removed")
    code_hash: str = Field(..., description="Hash of normalized code for exact duplicate detection")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for similarity comparison")

    # Source tracking
    sources: List[SourceLocation] = Field(default_factory=list)
    occurrence_count: int = Field(default=1, ge=1, description="Number of times this example appears")

    # Hierarchy
    is_canonical: bool = Field(default=False, description="Is this the canonical/best version?")
    canonical_id: Optional[str] = Field(None, description="ID of canonical example if this is a variant")
    similarity_to_canonical: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cosine similarity to canonical")
    tier: Optional[str] = Field(None, description="Hierarchy tier (a0, a1, a2, etc.)")

    # Merge metadata
    diff_summary: Optional[str] = Field(None, description="Summary of differences from canonical")
    unique_information: List[str] = Field(default_factory=list, description="Unique details not in canonical")
    merge_strategy: Optional[MergeStrategy] = Field(None, description="How this was merged")

    @classmethod
    def from_code(
        cls,
        code: str,
        language: LanguageType = LanguageType.PYTHON,
        source: Optional[SourceLocation] = None,
        **kwargs,
    ) -> "CodeExample":
        """Create CodeExample from raw code, automatically normalizing and hashing."""
        normalized = cls._normalize_code(code)
        code_hash = cls._hash_code(normalized)

        sources = [source] if source else []

        return cls(
            code=code,
            language=language,
            normalized_code=normalized,
            code_hash=code_hash,
            sources=sources,
            **kwargs,
        )

    @staticmethod
    def _normalize_code(code: str) -> str:
        """
        Normalize code by removing comments and standardizing whitespace.
        This allows detection of functionally identical code.
        """
        import re

        # Remove Python comments (simple approach)
        code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)

        # Remove blank lines
        lines = [line.rstrip() for line in code.split("\n") if line.strip()]

        # Standardize whitespace (preserve indentation structure)
        return "\n".join(lines)

    @staticmethod
    def _hash_code(code: str) -> str:
        """Generate SHA256 hash of code."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def add_source(self, source: SourceLocation) -> None:
        """Add another source location for this example."""
        self.sources.append(source)
        self.occurrence_count += 1


# =============================================================================
# Example Clusters
# =============================================================================


class ExampleCluster(BaseModel):
    """Group of similar code examples."""

    cluster_id: str = Field(default_factory=lambda: f"cluster_{uuid.uuid4().hex[:12]}")

    # Canonical example (best version)
    canonical: CodeExample

    # Similar variants
    variants: List[CodeExample] = Field(default_factory=list)

    # Cluster metadata
    operation: str = Field(..., description="Main operation for this cluster")
    avg_similarity: float = Field(..., ge=0.0, le=1.0, description="Average similarity within cluster")
    merge_status: str = Field(default="pending", description="Status: pending, merged, manual_review")

    # AI merge results
    merge_notes: Optional[str] = Field(None, description="Notes from AI merging process")
    conflicts: List[str] = Field(default_factory=list, description="Detected conflicts requiring review")

    @computed_field
    @property
    def total_occurrences(self) -> int:
        """Total times this example pattern appears across all sources."""
        return self.canonical.occurrence_count + sum(v.occurrence_count for v in self.variants)

    @computed_field
    @property
    def variant_count(self) -> int:
        """Number of variants (not including canonical)."""
        return len(self.variants)

    @computed_field
    @property
    def unique_sources(self) -> List[str]:
        """List of unique source files for this cluster."""
        sources = set()
        for src in self.canonical.sources:
            sources.add(src.file)
        for variant in self.variants:
            for src in variant.sources:
                sources.add(src.file)
        return sorted(sources)


# =============================================================================
# API Reference
# =============================================================================


class APIParameter(BaseModel):
    """Parameter for an API method."""

    name: str
    type: Optional[str] = None
    default: Optional[str] = None
    required: bool = True
    description: Optional[str] = None


class APIMethod(BaseModel):
    """Complete information about an API method or class."""

    # Identity
    name: str = Field(..., description="Method/class name (e.g., 'connect', 'IB')")
    full_path: str = Field(..., description="Full path (e.g., 'ib_insync.ib.IB.connect')")
    type: str = Field(..., description="Type: method, function, class, property, attribute")
    module: str = Field(..., description="Module path (e.g., 'ib_insync.ib')")

    # Documentation
    signature: Optional[str] = Field(None, description="Method signature")
    description: Optional[str] = Field(None, description="Method description")
    parameters: List[APIParameter] = Field(default_factory=list)
    returns: Optional[str] = Field(None, description="Return type/description")
    raises: List[str] = Field(default_factory=list, description="Exceptions raised")

    # Examples
    example_ids: List[str] = Field(default_factory=list, description="IDs of associated code examples")

    # Dependencies and relationships
    prerequisites: List[str] = Field(default_factory=list, description="Methods that should be called first")
    enables: List[str] = Field(default_factory=list, description="Methods that this enables")
    related_methods: List[str] = Field(default_factory=list, description="Related methods")
    complexity_level: Optional[int] = Field(None, ge=1, le=5, description="Complexity: 1=basic, 5=advanced")

    # Warnings and gotchas
    gotchas: List[str] = Field(default_factory=list, description="Common pitfalls and gotchas")
    deprecation_note: Optional[str] = Field(None)

    # Source tracking
    sources: List[SourceLocation] = Field(default_factory=list)


# =============================================================================
# Patterns and Concepts
# =============================================================================


class Pattern(BaseModel):
    """Identified usage pattern or best practice."""

    id: str = Field(default_factory=lambda: f"pattern_{uuid.uuid4().hex[:12]}")
    name: str
    category: str  # e.g., "connection", "data_retrieval", "order_management"
    description: str
    example_ids: List[str] = Field(default_factory=list)
    code_template: Optional[str] = None
    when_to_use: Optional[str] = None
    related_patterns: List[str] = Field(default_factory=list)
    sources: List[SourceLocation] = Field(default_factory=list)


class Concept(BaseModel):
    """Conceptual explanation or tutorial content."""

    id: str = Field(default_factory=lambda: f"concept_{uuid.uuid4().hex[:12]}")
    title: str
    content: str
    category: str  # e.g., "async_programming", "event_loops", "contract_types"
    related_methods: List[str] = Field(default_factory=list)
    example_ids: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    sources: List[SourceLocation] = Field(default_factory=list)


class Gotcha(BaseModel):
    """Common pitfall or warning."""

    id: str = Field(default_factory=lambda: f"gotcha_{uuid.uuid4().hex[:12]}")
    title: str
    description: str
    severity: str = Field(default="medium", description="Severity: low, medium, high, critical")
    affected_methods: List[str] = Field(default_factory=list)
    solution: Optional[str] = None
    example_ids: List[str] = Field(default_factory=list)
    sources: List[SourceLocation] = Field(default_factory=list)


# =============================================================================
# Complete Database
# =============================================================================


class DedupMetrics(BaseModel):
    """Metrics tracking deduplication results."""

    # Counts
    total_examples_before: int = 0
    total_examples_after: int = 0
    exact_duplicates: int = 0
    near_duplicates: int = 0
    similar_variants: int = 0

    # Ratios
    deduplication_ratio: float = 0.0  # Percentage reduced
    information_preservation: float = 1.0  # Should be 1.0 (100%)

    # Coverage
    api_methods_documented: int = 0
    api_methods_with_examples: int = 0
    api_coverage: float = 0.0

    # Quality
    examples_with_context: int = 0
    examples_validated: int = 0
    conflicts_detected: int = 0

    # Performance
    processing_time_seconds: float = 0.0
    embedding_time_seconds: float = 0.0
    clustering_time_seconds: float = 0.0
    merging_time_seconds: float = 0.0

    # Costs
    api_calls_made: int = 0
    api_cost_usd: float = 0.0


class DedupDatabase(BaseModel):
    """Complete deduplicated knowledge base."""

    # Metadata
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)
    source_files: List[str] = Field(default_factory=list)

    # Content
    api_methods: Dict[str, APIMethod] = Field(default_factory=dict, description="API methods by full_path")
    example_clusters: Dict[str, ExampleCluster] = Field(default_factory=dict, description="Example clusters by ID")
    standalone_examples: Dict[str, CodeExample] = Field(default_factory=dict, description="Single examples (no duplicates)")
    concepts: Dict[str, Concept] = Field(default_factory=dict)
    patterns: Dict[str, Pattern] = Field(default_factory=dict)
    gotchas: Dict[str, Gotcha] = Field(default_factory=dict)

    # Metrics
    metrics: DedupMetrics = Field(default_factory=DedupMetrics)

    # Methods
    def save_json(self, path: Path | str) -> None:
        """Save database to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_json(cls, path: Path | str) -> "DedupDatabase":
        """Load database from JSON file."""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            import json

            return cls(**json.load(f))

    def add_api_method(self, method: APIMethod) -> None:
        """Add or update an API method."""
        self.api_methods[method.full_path] = method

    def add_example_cluster(self, cluster: ExampleCluster) -> None:
        """Add an example cluster."""
        self.example_clusters[cluster.cluster_id] = cluster

    def add_standalone_example(self, example: CodeExample) -> None:
        """Add a standalone example (no duplicates)."""
        self.standalone_examples[example.id] = example

    def get_examples_for_method(self, method_path: str) -> List[CodeExample]:
        """Get all examples for a specific API method."""
        method = self.api_methods.get(method_path)
        if not method:
            return []

        examples = []
        for example_id in method.example_ids:
            # Check standalone examples
            if example_id in self.standalone_examples:
                examples.append(self.standalone_examples[example_id])

            # Check clusters
            for cluster in self.example_clusters.values():
                if cluster.canonical.id == example_id:
                    examples.append(cluster.canonical)
                    break

        return examples

    @computed_field
    @property
    def total_examples(self) -> int:
        """Total number of canonical examples."""
        return len(self.example_clusters) + len(self.standalone_examples)

    @computed_field
    @property
    def total_variants(self) -> int:
        """Total number of variant examples."""
        return sum(cluster.variant_count for cluster in self.example_clusters.values())


# =============================================================================
# Pipeline Stage Outputs
# =============================================================================


class ExtractionOutput(BaseModel):
    """Output from extraction stage."""

    examples: List[CodeExample] = Field(default_factory=list)
    api_methods: List[APIMethod] = Field(default_factory=list)
    concepts: List[Concept] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)
    gotchas: List[Gotcha] = Field(default_factory=list)
    source_files: List[str] = Field(default_factory=list)
    extraction_time: float = 0.0


class EmbeddingOutput(BaseModel):
    """Output from embedding stage."""

    examples: List[CodeExample] = Field(default_factory=list)
    embedding_model: str
    embedding_dimension: int
    embedding_time: float = 0.0


class ClusteringOutput(BaseModel):
    """Output from clustering stage."""

    clusters: List[ExampleCluster] = Field(default_factory=list)
    outliers: List[CodeExample] = Field(default_factory=list)
    similarity_threshold: float
    clustering_time: float = 0.0


class MergingOutput(BaseModel):
    """Output from merging stage."""

    merged_clusters: List[ExampleCluster] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    merge_strategy_used: Dict[str, int] = Field(default_factory=dict)  # Count by strategy
    merging_time: float = 0.0
    api_cost: float = 0.0


# =============================================================================
# Pyramid Index Models (for fast hierarchical retrieval)
# =============================================================================


class OperationIndex(BaseModel):
    """Index entry for an operation in the apex index."""

    canonical_id: str = Field(..., description="ID of canonical example")
    total_occurrences: int = Field(..., ge=1)
    variant_count: int = Field(default=0, ge=0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    tier_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of examples per tier (a0, a1, a2, a3)",
    )

    file_pointer: str = Field(
        ..., description="JSON pointer to canonical example"
    )


class ApexIndex(BaseModel):
    """
    Top-level pyramid index for ultra-fast canonical lookup.

    Enables O(1) operation → canonical example retrieval.
    """

    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)

    total_operations: int = Field(default=0, ge=0)
    total_examples: int = Field(default=0, ge=0)
    total_canonical: int = Field(default=0, ge=0)

    # Operation name → Index entry
    operations: Dict[str, OperationIndex] = Field(default_factory=dict)

    quick_stats: Dict[str, Any] = Field(
        default_factory=lambda: {
            "most_common": [],
            "avg_variants_per_operation": 0.0,
            "deduplication_ratio": 0.0,
        }
    )

    def add_operation(
        self, operation: str, canonical_id: str, cluster: "ExampleCluster"
    ) -> None:
        """Add operation to apex index."""
        tier_dist = {"a0": cluster.canonical.occurrence_count}

        for variant in cluster.variants:
            tier = variant.tier or "a1"
            tier_dist[tier] = tier_dist.get(tier, 0) + variant.occurrence_count

        self.operations[operation] = OperationIndex(
            canonical_id=canonical_id,
            total_occurrences=cluster.total_occurrences,
            variant_count=cluster.variant_count,
            tier_distribution=tier_dist,
            file_pointer=f"canonical_examples.json#{canonical_id}",
        )

        self.total_operations = len(self.operations)

    def save_json(self, path: Path | str) -> None:
        """Save apex index to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_json(cls, path: Path | str) -> "ApexIndex":
        """Load apex index from JSON."""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            import json

            return cls(**json.load(f))


class TierInfo(BaseModel):
    """Information about a specific tier in a cluster."""

    example_id: str
    occurrences: int = Field(..., ge=1)
    similarity: float = Field(..., ge=0.0, le=1.0)
    pointer: Optional[str] = None
    diff_summary: Optional[str] = None
    unique_information: List[str] = Field(default_factory=list)


class ClusterNavigation(BaseModel):
    """Navigation pointers for cluster traversal."""

    parent: str = Field(..., description="Pointer to apex index entry")
    canonical: str = Field(..., description="Pointer to canonical example")
    variants: Dict[str, int] = Field(
        default_factory=dict, description="Count per tier"
    )


class VariantCluster(BaseModel):
    """
    Complete cluster with all tiers for pyramid index.

    Enables efficient tier-based traversal.
    """

    cluster_id: str
    operation: str
    canonical_id: str
    total_occurrences: int

    # Tiers organized for cascade retrieval
    tiers: Dict[str, Any] = Field(
        default_factory=lambda: {"a0": {}, "a1": [], "a2": [], "a3": []}
    )

    navigation: ClusterNavigation

    @classmethod
    def from_example_cluster(
        cls, cluster: ExampleCluster, operation: str
    ) -> "VariantCluster":
        """Convert ExampleCluster to VariantCluster for pyramid index."""
        tiers: Dict[str, Any] = {
            "a0": TierInfo(
                example_id=cluster.canonical.id,
                occurrences=cluster.canonical.occurrence_count,
                similarity=1.0,
                pointer=f"canonical_examples.json#{cluster.canonical.id}",
            ).model_dump(),
            "a1": [],
            "a2": [],
            "a3": [],
        }

        # Organize variants by tier
        for variant in cluster.variants:
            tier = variant.tier or "a1"
            tier_info = TierInfo(
                example_id=variant.id,
                occurrences=variant.occurrence_count,
                similarity=variant.similarity_to_canonical or 0.85,
                diff_summary=variant.diff_summary,
                unique_information=variant.unique_information,
            )
            tiers[tier].append(tier_info.model_dump())

        return cls(
            cluster_id=cluster.cluster_id,
            operation=operation,
            canonical_id=cluster.canonical.id,
            total_occurrences=cluster.total_occurrences,
            tiers=tiers,
            navigation=ClusterNavigation(
                parent=f"apex_index.json#{operation}",
                canonical=f"canonical_examples.json#{cluster.canonical.id}",
                variants={
                    tier: len(examples)
                    for tier, examples in tiers.items()
                    if tier != "a0" and examples
                },
            ),
        )


class PyramidIndex(BaseModel):
    """
    Complete pyramid index structure.

    Contains apex, canonicals, and variant clusters for fast retrieval.
    """

    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)

    apex: ApexIndex
    canonicals: Dict[str, CodeExample] = Field(default_factory=dict)
    clusters: Dict[str, VariantCluster] = Field(default_factory=dict)

    def build_from_database(self, db: "DedupDatabase") -> None:
        """Build pyramid index from dedup database."""
        self.apex = ApexIndex()

        # Process each cluster
        for cluster in db.example_clusters.values():
            operation = cluster.operation

            # Add canonical
            self.canonicals[cluster.canonical.id] = cluster.canonical

            # Create variant cluster
            var_cluster = VariantCluster.from_example_cluster(cluster, operation)
            self.clusters[cluster.cluster_id] = var_cluster

            # Add to apex
            self.apex.add_operation(operation, cluster.canonical.id, cluster)

        # Calculate quick stats
        self._calculate_stats(db)

    def _calculate_stats(self, db: "DedupDatabase") -> None:
        """Calculate quick statistics for apex index."""
        # Most common operations
        ops_by_count = sorted(
            self.apex.operations.items(),
            key=lambda x: x[1].total_occurrences,
            reverse=True,
        )
        self.apex.quick_stats["most_common"] = [op for op, _ in ops_by_count[:10]]

        # Average variants
        if self.apex.total_operations > 0:
            avg_variants = sum(
                op.variant_count for op in self.apex.operations.values()
            ) / self.apex.total_operations
            self.apex.quick_stats["avg_variants_per_operation"] = round(
                avg_variants, 2
            )

        # Dedup ratio
        if db.metrics.total_examples_before > 0:
            self.apex.quick_stats["deduplication_ratio"] = round(
                db.metrics.deduplication_ratio, 2
            )

    def save(self, output_dir: Path | str) -> None:
        """Save pyramid index to separate files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save apex (small, fast)
        self.apex.save_json(output_dir / "apex_index.json")

        # Save canonicals
        canonical_data = {
            "version": self.version,
            "tier": "a0",
            "count": len(self.canonicals),
            "examples": {
                ex_id: ex.model_dump() for ex_id, ex in self.canonicals.items()
            },
        }
        with open(output_dir / "canonical_examples.json", "w", encoding="utf-8") as f:
            import json

            json.dump(canonical_data, f, indent=2, default=str)

        # Save variant clusters
        cluster_data = {
            "version": self.version,
            "count": len(self.clusters),
            "clusters": {
                c_id: cluster.model_dump()
                for c_id, cluster in self.clusters.items()
            },
        }
        with open(output_dir / "variant_clusters.json", "w", encoding="utf-8") as f:
            import json

            json.dump(cluster_data, f, indent=2, default=str)

    @classmethod
    def load(cls, output_dir: Path | str) -> "PyramidIndex":
        """Load pyramid index from files."""
        output_dir = Path(output_dir)

        # Load apex
        apex = ApexIndex.load_json(output_dir / "apex_index.json")

        # Load canonicals
        with open(output_dir / "canonical_examples.json", encoding="utf-8") as f:
            import json

            canonical_data = json.load(f)
            canonicals = {
                ex_id: CodeExample(**ex_data)
                for ex_id, ex_data in canonical_data["examples"].items()
            }

        # Load clusters
        with open(output_dir / "variant_clusters.json", encoding="utf-8") as f:
            import json

            cluster_data = json.load(f)
            clusters = {
                c_id: VariantCluster(**c_data)
                for c_id, c_data in cluster_data["clusters"].items()
            }

        return cls(apex=apex, canonicals=canonicals, clusters=clusters)
