"""Unit tests for validation utility functions."""

import pytest
from paperdeck.validation.utils import is_escaped, strip_comments


class TestIsEscaped:
    """Tests for is_escaped() function."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_escaped_brace(self):
        """Test detection of escaped brace."""
        text = r"\{escaped\}"
        assert is_escaped(text, 1) is True  # {
        assert is_escaped(text, 10) is True  # }

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_double_backslash_not_escaped(self):
        """Test double backslash doesn't escape."""
        text = r"\\{not escaped}"
        assert is_escaped(text, 2) is False  # {

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_triple_backslash_escaped(self):
        """Test triple backslash does escape."""
        text = r"\\\{escaped}"
        assert is_escaped(text, 3) is True  # {

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_no_backslash_not_escaped(self):
        """Test character without backslash is not escaped."""
        text = "{not escaped}"
        assert is_escaped(text, 0) is False

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_position_zero_not_escaped(self):
        """Test position 0 is never escaped."""
        text = r"\test"
        assert is_escaped(text, 0) is False


class TestStripComments:
    """Tests for strip_comments() function."""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_full_line_comment(self):
        """Test full line comment is removed."""
        line = "% This is a comment"
        assert strip_comments(line) == ""

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_inline_comment(self):
        """Test inline comment is removed."""
        line = r"\begin{frame} % comment here"
        assert strip_comments(line) == r"\begin{frame} "

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_escaped_percent_preserved(self):
        """Test escaped percent sign is preserved."""
        line = r"50\% complete"
        assert strip_comments(line) == r"50\% complete"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_escaped_percent_with_comment(self):
        """Test escaped percent followed by comment."""
        line = r"50\% and % comment"
        assert strip_comments(line) == r"50\% and "

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_no_comment(self):
        """Test line without comment is unchanged."""
        line = r"\begin{frame}"
        assert strip_comments(line) == r"\begin{frame}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.us1
    def test_empty_line(self):
        """Test empty line remains empty."""
        line = ""
        assert strip_comments(line) == ""
