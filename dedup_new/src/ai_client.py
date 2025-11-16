"""OpenRouter AI client for deduplication."""

import os
import time
from typing import List, Dict, Optional
from openai import OpenAI
from rich.console import Console

from models import CodeExample, MergedExample

console = Console()


class OpenRouterClient:
    """Client for OpenRouter API (DeepSeek or Claude)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek/deepseek-r1",
        base_url: str = "https://openrouter.ai/api/v1",
        max_tokens: int = 4000,
        temperature: float = 0.2,
        track_costs: bool = True,
    ):
        """Initialize OpenRouter client."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.track_costs = track_costs

        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 50ms between requests

        console.print(f"[cyan]✓ OpenRouter client initialized ({model})[/cyan]")

    def merge_examples(
        self, examples: List[CodeExample], cluster_id: str = "unknown"
    ) -> MergedExample:
        """Merge similar code examples using AI."""
        if not examples:
            raise ValueError("No examples to merge")

        if len(examples) == 1:
            # Single example, no merging needed
            ex = examples[0]
            return MergedExample(
                id=f"merged_{ex.id}",
                code=ex.code,
                language=ex.language,
                description=ex.context or "Code example",
                sources=[ex.id],
                tags=ex.tags,
                notes="Single example, no duplicates found",
                metadata={"confidence": 1.0, "variations": 0},
            )

        # Multiple examples - use AI to merge
        prompt = self._create_merge_prompt(examples)

        try:
            response = self._call_api(prompt)
            merged = self._parse_merge_response(response, examples, cluster_id)
            return merged

        except Exception as e:
            console.print(f"[red]Error merging cluster {cluster_id}: {e}[/red]")
            # Fallback: return first example
            ex = examples[0]
            return MergedExample(
                id=f"merged_{cluster_id}",
                code=ex.code,
                language=ex.language,
                description=f"Merge failed: {str(e)}",
                sources=[e.id for e in examples],
                tags=ex.tags,
                notes=f"AI merge failed, using first example. Error: {str(e)}",
                metadata={"confidence": 0.5, "variations": len(examples) - 1},
            )

    def _create_merge_prompt(self, examples: List[CodeExample]) -> str:
        """Create prompt for merging examples."""
        prompt = """You are an expert at analyzing and merging code documentation. You will be given several similar code examples from different documentation sources. Your task is to:

1. Identify the BEST canonical version (most complete, best practices)
2. Note any important variations or differences
3. Create a comprehensive description that covers all use cases
4. Identify relevant tags

Here are the examples to merge:

"""

        for i, ex in enumerate(examples, 1):
            prompt += f"\n--- Example {i} ---\n"
            prompt += f"Source: {ex.source_file}\n"
            if ex.heading:
                prompt += f"Section: {ex.heading}\n"
            if ex.context:
                prompt += f"Context: {ex.context}\n"
            prompt += f"\nCode:\n```{ex.language}\n{ex.code}\n```\n"
            if ex.tags:
                prompt += f"Tags: {', '.join(ex.tags)}\n"

        prompt += """

Please respond in the following JSON format:
{
  "canonical_code": "the best version of the code",
  "language": "python",
  "description": "comprehensive description covering all variations",
  "tags": ["tag1", "tag2", "tag3"],
  "notes": "important variations or differences between examples",
  "confidence": 0.95
}

Only return the JSON, no other text.
"""

        return prompt

    def _call_api(self, prompt: str) -> str:
        """Make API call with rate limiting."""
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            self.last_request_time = time.time()

            # Track usage
            if response.usage and self.track_costs:
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                self._update_cost(response.usage.prompt_tokens, response.usage.completion_tokens)

            return response.choices[0].message.content

        except Exception as e:
            console.print(f"[red]API Error: {e}[/red]")
            raise

    def _parse_merge_response(
        self, response: str, examples: List[CodeExample], cluster_id: str
    ) -> MergedExample:
        """Parse AI response into MergedExample."""
        import json

        try:
            # Extract JSON from response (in case there's extra text)
            json_match = response.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0].strip()
            elif "```" in json_match:
                json_match = json_match.split("```")[1].split("```")[0].strip()

            data = json.loads(json_match)

            return MergedExample(
                id=f"merged_{cluster_id}",
                code=data.get("canonical_code", examples[0].code),
                language=data.get("language", "python"),
                description=data.get("description", ""),
                sources=[ex.id for ex in examples],
                tags=data.get("tags", []),
                notes=data.get("notes", ""),
                metadata={
                    "confidence": data.get("confidence", 0.8),
                    "variations": len(examples) - 1,
                    "ai_model": self.model,
                },
            )

        except json.JSONDecodeError as e:
            console.print(f"[yellow]Warning: Failed to parse JSON response: {e}[/yellow]")
            console.print(f"[yellow]Response was: {response[:200]}...[/yellow]")

            # Fallback to first example
            ex = examples[0]
            return MergedExample(
                id=f"merged_{cluster_id}",
                code=ex.code,
                language=ex.language,
                description=ex.context or "Merge failed",
                sources=[e.id for e in examples],
                tags=ex.tags,
                notes=f"JSON parse failed. Raw response: {response[:100]}...",
                metadata={"confidence": 0.6, "variations": len(examples) - 1},
            )

    def _update_cost(self, input_tokens: int, output_tokens: int):
        """Update cost tracking based on model pricing."""
        # DeepSeek R1 pricing (as of 2025)
        pricing = {
            "deepseek/deepseek-r1": {"input": 0.55 / 1_000_000, "output": 2.19 / 1_000_000},
            "deepseek/deepseek-coder": {"input": 0.14 / 1_000_000, "output": 0.28 / 1_000_000},
            "anthropic/claude-3.5-sonnet": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
        }

        rates = pricing.get(self.model, {"input": 1.0 / 1_000_000, "output": 2.0 / 1_000_000})

        cost = (input_tokens * rates["input"]) + (output_tokens * rates["output"])
        self.total_cost += cost

    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary."""
        return {
            "total_cost": round(self.total_cost, 4),
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def print_cost_summary(self):
        """Print cost summary to console."""
        summary = self.get_cost_summary()
        console.print("\n[bold]API Cost Summary:[/bold]")
        console.print(f"  Model: {self.model}")
        console.print(f"  Input tokens: {summary['input_tokens']:,}")
        console.print(f"  Output tokens: {summary['output_tokens']:,}")
        console.print(f"  Total cost: ${summary['total_cost']:.4f}")
