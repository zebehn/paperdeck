"""Unit tests for EnvironmentMatcher."""

import pytest
from src.paperdeck.validation.environment_matcher import EnvironmentMatcher


class TestEnvironmentMatcher:
    """Test cases for EnvironmentMatcher class."""

    def test_find_unmatched_missing_end(self):
        """Test detection of missing \\end{...} tag."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",
            "  Content",
            r"\begin{itemize}",
            r"  \item Test",
            # Missing \end{itemize}
            # Missing \end{frame}
        ]

        unmatched = matcher.find_unmatched(lines)

        assert len(unmatched) == 2
        # Both should be 'begin' type (missing ends)
        assert all(um.tag_type == 'begin' for um in unmatched)
        # Should find both frame and itemize
        envs = {um.environment for um in unmatched}
        assert envs == {'frame', 'itemize'}

    def test_find_unmatched_extra_end(self):
        """Test detection of unmatched \\end{...} tag."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",
            "  Content",
            r"\end{frame}",
            r"\end{frame}",  # Extra end tag
        ]

        unmatched = matcher.find_unmatched(lines)

        assert len(unmatched) == 1
        assert unmatched[0].tag_type == 'end'
        assert unmatched[0].environment == 'frame'
        assert unmatched[0].line_number == 4

    def test_find_unmatched_properly_matched(self):
        """Test that properly matched environments return no errors."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",
            r"  \begin{itemize}",
            r"    \item Test",
            r"  \end{itemize}",
            r"\end{frame}",
        ]

        unmatched = matcher.find_unmatched(lines)

        assert len(unmatched) == 0

    def test_find_duplicates_consecutive_begins(self):
        """Test detection of consecutive \\begin{...} tags without closing."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{columns}",
            r"  \begin{column}{0.5\textwidth}",
            "    Content",
            # Missing \end{column} here - so next begin is duplicate
            r"  \begin{column}{0.5\textwidth}",  # Line 4: Duplicate begin!
            "    Content",
            r"  \end{column}",
            r"\end{columns}",
        ]

        duplicates = matcher.find_duplicates(lines)

        assert len(duplicates) == 1
        assert duplicates[0].environment == 'column'
        # Duplicate detected on line 4 (second begin before first closed)
        assert duplicates[0].line_number == 4

    def test_find_duplicates_no_duplicates(self):
        """Test that properly structured content returns no duplicates."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",
            r"  \begin{itemize}",
            r"    \item One",
            r"  \end{itemize}",
            r"  \begin{itemize}",  # Not duplicate, previous was closed
            r"    \item Two",
            r"  \end{itemize}",
            r"\end{frame}",
        ]

        duplicates = matcher.find_duplicates(lines)

        assert len(duplicates) == 0

    def test_get_environment_pairs(self):
        """Test retrieval of matched environment pairs."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",      # Line 1
            r"  \begin{itemize}",  # Line 2
            r"    \item Test",
            r"  \end{itemize}",    # Line 4
            r"\end{frame}",        # Line 5
        ]

        pairs = matcher.get_environment_pairs(lines)

        assert len(pairs) == 2
        assert ('itemize', 2, 4) in pairs
        assert ('frame', 1, 5) in pairs

    def test_custom_environments(self):
        """Test validation with custom environment list."""
        matcher = EnvironmentMatcher(environments=['custom', 'special'])
        lines = [
            r"\begin{custom}",
            r"\begin{frame}",  # Should be ignored (not in custom list)
            r"\end{frame}",
            r"\end{custom}",
        ]

        unmatched = matcher.find_unmatched(lines)

        # Only 'custom' should be tracked, 'frame' ignored
        assert len(unmatched) == 0

    def test_nested_environments(self):
        """Test handling of nested environments."""
        matcher = EnvironmentMatcher()
        lines = [
            r"\begin{frame}",
            r"  \begin{columns}",
            r"    \begin{column}{0.5\textwidth}",
            r"      \begin{itemize}",
            r"        \item Test",
            r"      \end{itemize}",
            r"    \end{column}",
            r"  \end{columns}",
            r"\end{frame}",
        ]

        unmatched = matcher.find_unmatched(lines)
        duplicates = matcher.find_duplicates(lines)

        assert len(unmatched) == 0
        assert len(duplicates) == 0
