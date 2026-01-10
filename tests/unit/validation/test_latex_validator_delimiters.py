"""Unit tests for LaTeX validator delimiter matching integration."""

import pytest
from paperdeck.validation.latex_validator import LaTeXValidator, ValidationConfig
from paperdeck.validation.error_types import ErrorType
from paperdeck.validation.fix_confidence import FixConfidence


class TestLaTeXValidatorDelimiterMatching:
    """Tests for LaTeXValidator._check_delimiter_matching() integration."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_braces_valid(self):
        """Test validation passes with matched braces."""
        validator = LaTeXValidator()
        content = r"""
\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{This is bold}
\end{frame}
\end{document}
"""
        result = validator.validate_content(content)

        # Should have no delimiter errors (may have other errors)
        delimiter_errors = [e for e in result.errors
                          if 'brace' in e.error_type.lower()]
        assert len(delimiter_errors) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_missing_closing_brace(self):
        """Test detection of missing closing brace."""
        validator = LaTeXValidator()
        content = r"""\textbf{This is bold"""

        result = validator.validate_content(content)

        # Should detect unmatched opening brace
        brace_errors = [e for e in result.errors
                       if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 1
        assert brace_errors[0].error_type == ErrorType.UNMATCHED_BRACE_OPEN.value
        assert brace_errors[0].line_number == 1
        assert brace_errors[0].column_number == 8  # Position of {

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_extra_closing_brace(self):
        """Test detection of extra closing brace."""
        validator = LaTeXValidator()
        content = r"""\textbf{This is bold}}"""

        result = validator.validate_content(content)

        # Should detect unmatched closing brace
        brace_errors = [e for e in result.errors
                       if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 1
        assert brace_errors[0].error_type == ErrorType.UNMATCHED_BRACE_CLOSE.value
        assert brace_errors[0].line_number == 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_with_config_disabled(self):
        """Test delimiter matching can be disabled via config."""
        config = ValidationConfig(validate_braces=False)
        validator = LaTeXValidator(config=config)
        content = r"""\textbf{missing brace"""

        result = validator.validate_content(content)

        # Should NOT detect brace errors when disabled
        brace_errors = [e for e in result.errors
                       if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_confidence_scores(self):
        """Test that delimiter errors have confidence scores."""
        validator = LaTeXValidator()
        content = r"""\textbf{This is bold"""

        result = validator.validate_content(content)

        brace_errors = [e for e in result.errors
                       if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 1

        # Should have high confidence (>= 0.85) for simple missing brace
        assert brace_errors[0].fix_confidence >= FixConfidence.HIGH.value
        assert brace_errors[0].auto_fixable is True

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_check_delimiter_matching_line_content(self):
        """Test that errors include line content and column info."""
        validator = LaTeXValidator()
        content = r"""\textbf{This is bold"""

        result = validator.validate_content(content)

        brace_errors = [e for e in result.errors
                       if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 1

        error = brace_errors[0]
        assert error.line_content is not None
        assert r'\textbf{This is bold' in error.line_content
        assert error.column_number is not None
        assert error.column_number > 0
