"""Unit tests for DelimiterMatcher class."""

import pytest
from paperdeck.validation.delimiter_matcher import DelimiterMatcher
from paperdeck.validation.delimiter_types import DelimiterType


class TestDelimiterMatcherBraces:
    """Tests for brace matching in DelimiterMatcher."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_matched_braces(self):
        """Test correctly matched braces."""
        matcher = DelimiterMatcher()
        lines = [r"\textbf{bold text}"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_missing_closing_brace(self):
        """Test detection of missing closing brace."""
        matcher = DelimiterMatcher()
        lines = [r"\textbf{bold text"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 1
        assert unmatched[0].delimiter_type == DelimiterType.BRACE
        assert unmatched[0].tag_type == 'open'
        assert unmatched[0].line_number == 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_extra_closing_brace(self):
        """Test detection of extra closing brace."""
        matcher = DelimiterMatcher()
        lines = [r"\textbf{bold text}}"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 1
        assert unmatched[0].delimiter_type == DelimiterType.BRACE
        assert unmatched[0].tag_type == 'close'
        assert unmatched[0].line_number == 1

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_nested_braces(self):
        """Test nested braces are matched correctly."""
        matcher = DelimiterMatcher()
        lines = [r"\textbf{\textit{nested}}"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_escaped_braces_ignored(self):
        """Test escaped braces are ignored."""
        matcher = DelimiterMatcher()
        lines = [r"\{escaped\}"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 0

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_multiple_lines(self):
        """Test brace matching across multiple lines."""
        matcher = DelimiterMatcher()
        lines = [
            r"\begin{frame}",
            r"  \textbf{text",  # Missing }
            r"\end{frame}"
        ]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 1
        assert unmatched[0].line_number == 2

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.delimiter
    @pytest.mark.us1
    def test_comments_ignored(self):
        """Test braces in comments are ignored."""
        matcher = DelimiterMatcher()
        lines = [r"\textbf{text} % { unmatched in comment"]
        unmatched = matcher.find_unmatched_braces(lines)
        assert len(unmatched) == 0
