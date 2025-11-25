"""
Unit tests for LLMRequestContext model.

Following TDD approach: These tests define expected behavior before implementation.
"""

import pytest
from paperdeck.models.llm_request_context import (
    LLMRequestContext,
    validate_llm_request_context,
)


class TestLLMRequestContext:
    """Tests for LLMRequestContext dataclass."""

    def test_create_context_with_text(self):
        """Test creating LLM request context with paper text."""
        context = LLMRequestContext(
            paper_title="Deep Learning for NLP",
            paper_authors=["Smith et al."],
            paper_abstract="This paper presents...",
            paper_text="Introduction: Recent advances...",
            paper_text_token_count=5000,
            prompt_template="technical",
            beamer_theme="Madrid",
            max_slides=20,
            figure_count=3,
            table_count=2,
            equation_count=5,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        assert context.paper_title == "Deep Learning for NLP"
        assert context.paper_text == "Introduction: Recent advances..."
        assert context.paper_text_token_count == 5000
        assert context.max_context_tokens == 8192

    def test_create_context_without_text(self):
        """Test creating context without paper text (backward compatibility)."""
        context = LLMRequestContext(
            paper_title="Test Paper",
            paper_authors=["Author A"],
            paper_abstract="Abstract.",
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        assert context.paper_text is None
        assert context.paper_text_token_count is None

    def test_includes_full_text_property_true(self):
        """Test includes_full_text property returns True when text present."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="Some text content",
            paper_text_token_count=100,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        assert context.includes_full_text is True

    def test_includes_full_text_property_false_none(self):
        """Test includes_full_text returns False when text is None."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        assert context.includes_full_text is False

    def test_includes_full_text_property_false_empty_string(self):
        """Test includes_full_text returns False when text is empty string."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="",
            paper_text_token_count=0,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        assert context.includes_full_text is False

    def test_total_input_tokens_with_text(self):
        """Test total_input_tokens calculation with paper text."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="text",
            paper_text_token_count=5000,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        # metadata (100) + prompt (200) + text (5000) = 5300
        assert context.total_input_tokens == 5300

    def test_total_input_tokens_without_text(self):
        """Test total_input_tokens calculation without paper text."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        # metadata (100) + prompt (200) + text (0) = 300
        assert context.total_input_tokens == 300

    def test_is_within_context_limit_true(self):
        """Test is_within_context_limit returns True when within limits."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="text",
            paper_text_token_count=5000,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        # total_input_tokens = 5300, available = 6144
        assert context.is_within_context_limit is True

    def test_is_within_context_limit_false(self):
        """Test is_within_context_limit returns False when exceeds limits."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="text",
            paper_text_token_count=10000,  # Way too much
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        # total_input_tokens = 10300, available = 6144
        assert context.is_within_context_limit is False


class TestValidateLLMRequestContext:
    """Tests for LLM request context validation."""

    def test_validation_passes_valid_context(self):
        """Test validation passes for valid context."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="text",
            paper_text_token_count=5000,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        errors = validate_llm_request_context(context)
        assert len(errors) == 0

    def test_validation_fails_non_positive_reserved_tokens(self):
        """Test validation fails for non-positive reserved_output_tokens."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=0,  # Invalid
            available_input_tokens=8192,
        )

        errors = validate_llm_request_context(context)
        assert len(errors) > 0
        assert any("reserved_output_tokens" in error and "positive" in error for error in errors)

    def test_validation_fails_reserved_exceeds_max(self):
        """Test validation fails when reserved >= max context tokens."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=9000,  # Exceeds max
            available_input_tokens=0,
        )

        errors = validate_llm_request_context(context)
        assert len(errors) > 0
        assert any("reserved_output_tokens" in error and "exceed" in error for error in errors)

    def test_validation_fails_available_input_mismatch(self):
        """Test validation fails when available_input_tokens doesn't match calculation."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=5000,  # Should be 6144
        )

        errors = validate_llm_request_context(context)
        assert len(errors) > 0
        assert any("available_input_tokens mismatch" in error for error in errors)

    def test_validation_fails_exceeds_context_limit(self):
        """Test validation fails when input exceeds available tokens."""
        context = LLMRequestContext(
            paper_title="Title",
            paper_authors=[],
            paper_abstract=None,
            paper_text="text",
            paper_text_token_count=20000,  # Way too much
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        errors = validate_llm_request_context(context)
        assert len(errors) > 0
        assert any("Input tokens" in error and "exceed available" in error for error in errors)

    def test_validation_fails_no_content(self):
        """Test validation fails when both title and text are None."""
        context = LLMRequestContext(
            paper_title=None,
            paper_authors=[],
            paper_abstract=None,
            paper_text=None,
            paper_text_token_count=None,
            prompt_template="default",
            beamer_theme="Madrid",
            max_slides=None,
            figure_count=0,
            table_count=0,
            equation_count=0,
            max_context_tokens=8192,
            reserved_output_tokens=2048,
            available_input_tokens=6144,
        )

        errors = validate_llm_request_context(context)
        assert len(errors) > 0
        assert any("paper_title or paper_text" in error for error in errors)
