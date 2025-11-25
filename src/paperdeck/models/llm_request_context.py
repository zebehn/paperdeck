"""
LLM Request Context model for presentation generation.

This module defines the context sent to LLM services for presentation generation,
including paper metadata and full text content.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMRequestContext:
    """Context for LLM presentation generation request."""

    # Paper metadata (existing)
    paper_title: Optional[str]
    paper_authors: list[str]
    paper_abstract: Optional[str]

    # NEW: Full paper text content
    paper_text: Optional[str]           # Full extracted text (or truncated)
    paper_text_token_count: Optional[int]  # Token count of paper_text

    # Generation parameters
    prompt_template: str                # Template name (e.g., "technical")
    beamer_theme: str                   # LaTeX theme
    max_slides: Optional[int]           # Desired slide count

    # Figures/tables (existing)
    figure_count: int
    table_count: int
    equation_count: int

    # Context management
    max_context_tokens: int             # Model's context window size
    reserved_output_tokens: int         # Tokens reserved for output
    available_input_tokens: int         # Tokens available for input

    @property
    def includes_full_text(self) -> bool:
        """Whether request includes full paper text."""
        return self.paper_text is not None and len(self.paper_text) > 0

    @property
    def total_input_tokens(self) -> int:
        """Estimated total input tokens."""
        # Rough estimate: metadata + prompt + text
        metadata_tokens = 100  # Approximate
        prompt_tokens = 200    # Approximate
        text_tokens = self.paper_text_token_count or 0
        return metadata_tokens + prompt_tokens + text_tokens

    @property
    def is_within_context_limit(self) -> bool:
        """Whether context fits within model limits."""
        return self.total_input_tokens <= self.available_input_tokens


def validate_llm_request_context(context: LLMRequestContext) -> list[str]:
    """
    Validate LLM request context.

    Args:
        context: LLMRequestContext to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Context size validations
    if context.reserved_output_tokens <= 0:
        errors.append("reserved_output_tokens must be positive")

    if context.reserved_output_tokens >= context.max_context_tokens:
        errors.append("reserved_output_tokens cannot exceed max_context_tokens")

    expected_available = context.max_context_tokens - context.reserved_output_tokens
    if context.available_input_tokens != expected_available:
        errors.append(
            f"available_input_tokens mismatch: expected {expected_available}, "
            f"got {context.available_input_tokens}"
        )

    # Context limit check
    if not context.is_within_context_limit:
        errors.append(
            f"Input tokens ({context.total_input_tokens}) exceed available "
            f"({context.available_input_tokens})"
        )

    # At least one content source required
    if not context.paper_title and not context.paper_text:
        errors.append("Either paper_title or paper_text must be provided")

    return errors
