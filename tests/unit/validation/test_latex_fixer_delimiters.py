"""Unit tests for LaTeX fixer delimiter fixing methods."""

import pytest
from paperdeck.validation.latex_fixer import LaTeXFixer, FixerConfig
from paperdeck.validation.validation_errors import ValidationError, FixChange
from paperdeck.validation.error_types import ErrorType
from paperdeck.validation.fix_confidence import FixConfidence


class TestLaTeXFixerMissingClosingBrace:
    """Tests for LaTeXFixer._fix_missing_closing_brace() method."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_simple_missing_closing_brace(self):
        """Test fixing simple missing closing brace."""
        fixer = LaTeXFixer()
        content = r"\textbf{This is bold"

        # Create validation error for missing closing brace
        error = ValidationError(
            line_number=1,
            column_number=8,  # Position of opening brace
            error_type=ErrorType.UNMATCHED_BRACE_OPEN.value,
            environment='',
            message='Missing closing brace',
            suggested_fix='Add closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should add closing brace at end of line
        assert r"\textbf{This is bold}" in fixed_content
        assert len(changes) == 1
        assert changes[0].fix_type == 'fix_missing_closing_brace'

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_missing_brace_with_nested_content(self):
        """Test fixing missing brace with nested braces."""
        fixer = LaTeXFixer()
        content = r"\textbf{\textit{nested} text"

        error = ValidationError(
            line_number=1,
            column_number=8,
            error_type=ErrorType.UNMATCHED_BRACE_OPEN.value,
            environment='',
            message='Missing closing brace',
            suggested_fix='Add closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should add closing brace after nested content
        assert r"\textbf{\textit{nested} text}" in fixed_content
        assert len(changes) == 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_missing_brace_multiline(self):
        """Test fixing missing brace that spans multiple lines."""
        # Use lower confidence threshold to allow medium-confidence fixes
        config = FixerConfig(confidence_threshold=0.60)
        fixer = LaTeXFixer(config=config)
        content = r"""\textbf{This is bold
and continues on next line"""

        error = ValidationError(
            line_number=1,
            column_number=8,
            error_type=ErrorType.UNMATCHED_BRACE_OPEN.value,
            environment='',
            message='Missing closing brace',
            suggested_fix='Add closing brace',
            severity='error',
            line_content=r"\textbf{This is bold",
            fix_confidence=FixConfidence.MEDIUM.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should add closing brace
        assert '}' in fixed_content
        assert len(changes) == 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_missing_brace_disabled_by_config(self):
        """Test that fixing can be disabled via config."""
        config = FixerConfig(fix_missing_braces=False)
        fixer = LaTeXFixer(config=config)
        content = r"\textbf{This is bold"

        error = ValidationError(
            line_number=1,
            column_number=8,
            error_type=ErrorType.UNMATCHED_BRACE_OPEN.value,
            environment='',
            message='Missing closing brace',
            suggested_fix='Add closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should NOT fix when disabled
        assert fixed_content == content
        assert len(changes) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_missing_brace_confidence_threshold(self):
        """Test that low confidence fixes are skipped."""
        config = FixerConfig(confidence_threshold=0.90)
        fixer = LaTeXFixer(config=config)
        content = r"\textbf{This is bold"

        # Create error with low confidence
        error = ValidationError(
            line_number=1,
            column_number=8,
            error_type=ErrorType.UNMATCHED_BRACE_OPEN.value,
            environment='',
            message='Missing closing brace',
            suggested_fix='Add closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.MEDIUM.value,  # 0.70 < 0.90 threshold
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should NOT fix when confidence below threshold
        assert fixed_content == content
        assert len(changes) == 0


class TestLaTeXFixerExtraClosingBrace:
    """Tests for LaTeXFixer._fix_extra_closing_brace() method."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_simple_extra_closing_brace(self):
        """Test fixing simple extra closing brace."""
        fixer = LaTeXFixer()
        content = r"\textbf{This is bold}}"

        error = ValidationError(
            line_number=1,
            column_number=22,  # Position of extra brace
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should remove extra closing brace
        assert fixed_content == r"\textbf{This is bold}"
        assert len(changes) == 1
        assert changes[0].fix_type == 'fix_extra_closing_brace'

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_extra_brace_multiple(self):
        """Test fixing multiple extra closing braces."""
        fixer = LaTeXFixer()
        content = r"\textbf{bold}}\textit{italic}}}"

        error1 = ValidationError(
            line_number=1,
            column_number=13,
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        error2 = ValidationError(
            line_number=1,
            column_number=31,
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error1, error2])

        # Should remove both extra braces
        # Note: exact result depends on implementation strategy
        assert fixed_content.count('}') < content.count('}')
        assert len(changes) >= 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_extra_brace_disabled_by_config(self):
        """Test that fixing can be disabled via config."""
        config = FixerConfig(fix_extra_braces=False)
        fixer = LaTeXFixer(config=config)
        content = r"\textbf{This is bold}}"

        error = ValidationError(
            line_number=1,
            column_number=22,
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should NOT fix when disabled
        assert fixed_content == content
        assert len(changes) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_extra_brace_preserves_formatting(self):
        """Test that fixing preserves indentation and formatting."""
        fixer = LaTeXFixer()
        content = r"""  \textbf{This is bold}}
    next line"""

        error = ValidationError(
            line_number=1,
            column_number=24,
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content="  \\textbf{This is bold}}",
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Should preserve leading whitespace
        assert fixed_content.startswith('  \\textbf')
        assert 'next line' in fixed_content

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_fix_extra_brace_logs_change(self):
        """Test that changes are properly logged."""
        fixer = LaTeXFixer()
        content = r"\textbf{This is bold}}"

        error = ValidationError(
            line_number=1,
            column_number=22,
            error_type=ErrorType.UNMATCHED_BRACE_CLOSE.value,
            environment='',
            message='Extra closing brace',
            suggested_fix='Remove closing brace',
            severity='error',
            line_content=content,
            fix_confidence=FixConfidence.HIGH.value,
            auto_fixable=True
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        assert len(changes) == 1
        change = changes[0]
        assert change.line_number == 1
        assert change.fix_type == 'fix_extra_closing_brace'
        assert change.confidence >= FixConfidence.HIGH.value
        assert change.before is not None
        assert change.after is not None
