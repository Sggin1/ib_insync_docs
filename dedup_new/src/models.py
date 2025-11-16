"""Data models for documentation deduplication."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CodeExample(BaseModel):
    """A code example extracted from documentation."""

    id: str = Field(..., description="Unique identifier")
    code: str = Field(..., description="The actual code")
    language: str = Field(default="python", description="Programming language")
    context: Optional[str] = Field(None, description="Surrounding text/explanation")
    source_file: str = Field(..., description="Source markdown file")
    line_number: Optional[int] = Field(None, description="Line number in source")
    heading: Optional[str] = Field(None, description="Section heading")
    tags: List[str] = Field(default_factory=list, description="Auto-detected tags")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "example_001",
                "code": "ib = IB()\\nib.connect('127.0.0.1', 7497, clientId=1)",
                "language": "python",
                "context": "Basic connection example",
                "source_file": "ib_insync_complete_guide.md",
                "line_number": 42,
                "heading": "Getting Started",
                "tags": ["connection", "basic"],
            }
        }


class DuplicateCluster(BaseModel):
    """A cluster of similar/duplicate code examples."""

    cluster_id: str = Field(..., description="Cluster identifier")
    examples: List[CodeExample] = Field(..., description="Examples in this cluster")
    similarity_score: float = Field(..., description="Average similarity within cluster")
    canonical: Optional[str] = Field(None, description="ID of canonical example")

    class Config:
        json_schema_extra = {
            "example": {
                "cluster_id": "cluster_001",
                "examples": [],  # List of CodeExample objects
                "similarity_score": 0.92,
                "canonical": "example_001",
            }
        }


class MergedExample(BaseModel):
    """A merged/deduplicated code example."""

    id: str = Field(..., description="Merged example ID")
    code: str = Field(..., description="Canonical code version")
    language: str = Field(default="python")
    description: str = Field(..., description="Comprehensive description")
    sources: List[str] = Field(..., description="Source file IDs that contributed")
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, description="Additional notes or variations")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "merged_001",
                "code": "ib = IB()\\nib.connect('127.0.0.1', 7497, clientId=1)",
                "language": "python",
                "description": "Basic IB connection setup",
                "sources": ["example_001", "example_042", "example_089"],
                "tags": ["connection", "basic", "setup"],
                "notes": "Some examples used different port numbers (4001, 7497)",
                "metadata": {"confidence": 0.95, "variations": 3},
            }
        }


class ExtractionResult(BaseModel):
    """Complete extraction results from all files."""

    examples: List[CodeExample] = Field(default_factory=list)
    total_files: int = Field(default=0)
    total_examples: int = Field(default=0)
    files_processed: List[str] = Field(default_factory=list)
    extraction_stats: Dict[str, Any] = Field(default_factory=dict)


class DeduplicationResult(BaseModel):
    """Final deduplication results."""

    merged_examples: List[MergedExample] = Field(default_factory=list)
    original_count: int = Field(..., description="Original example count")
    merged_count: int = Field(..., description="Deduplicated example count")
    deduplication_ratio: float = Field(..., description="Percentage reduced")
    clusters: List[DuplicateCluster] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
    cost_info: Optional[Dict[str, float]] = Field(None, description="API cost tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "merged_examples": [],
                "original_count": 450,
                "merged_count": 180,
                "deduplication_ratio": 0.60,
                "clusters": [],
                "stats": {"processing_time": 245.5, "api_calls": 85},
                "cost_info": {"total_cost": 0.04, "input_tokens": 45000, "output_tokens": 12000},
            }
        }
