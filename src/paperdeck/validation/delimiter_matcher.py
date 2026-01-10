"""Delimiter matching for LaTeX validation.

This module provides delimiter (braces, brackets, parentheses) matching
using stack-based algorithms similar to environment matching.
"""

from dataclasses import dataclass
from typing import List, Tuple

from .delimiter_types import DelimiterType
from .utils import is_escaped, strip_comments


@dataclass
class UnmatchedDelimiter:
    """Represents an unmatched delimiter.

    Attributes:
        delimiter_type: Type of delimiter (BRACE, BRACKET, PAREN)
        tag_type: 'open' for opening delimiter, 'close' for closing
        line_number: Line number where delimiter found (1-indexed)
        column_number: Column position in line (1-indexed)
        line_content: Content of the line
    """

    delimiter_type: DelimiterType
    tag_type: str  # 'open' or 'close'
    line_number: int
    column_number: int
    line_content: str


class DelimiterMatcher:
    """Matches delimiters (braces, brackets, parentheses) in LaTeX.

    Uses stack-based algorithm to detect unmatched delimiters.
    Handles escaped delimiters and comments correctly.
    """

    def __init__(self):
        """Initialize delimiter matcher."""
        pass

    def find_unmatched_braces(self, lines: List[str]) -> List[UnmatchedDelimiter]:
        """Find unmatched curly braces in LaTeX content.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of UnmatchedDelimiter objects for unmatched braces
        """
        return self._find_unmatched_delimiters(lines, DelimiterType.BRACE)

    def find_unmatched_brackets(self, lines: List[str]) -> List[UnmatchedDelimiter]:
        """Find unmatched square brackets in LaTeX content.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of UnmatchedDelimiter objects for unmatched brackets
        """
        return self._find_unmatched_delimiters(lines, DelimiterType.BRACKET)

    def find_unmatched_parens(self, lines: List[str]) -> List[UnmatchedDelimiter]:
        """Find unmatched parentheses in LaTeX content.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of UnmatchedDelimiter objects for unmatched parentheses
        """
        return self._find_unmatched_delimiters(lines, DelimiterType.PAREN)

    def _find_unmatched_delimiters(
        self,
        lines: List[str],
        delimiter_type: DelimiterType
    ) -> List[UnmatchedDelimiter]:
        """Find unmatched delimiters using stack-based algorithm.

        Args:
            lines: List of LaTeX file lines
            delimiter_type: Type of delimiter to match

        Returns:
            List of UnmatchedDelimiter objects
        """
        unmatched = []
        # Stack: [(line_number, column_number, line_content)]
        stack: List[Tuple[int, int, str]] = []

        opening = delimiter_type.opening
        closing = delimiter_type.closing

        for line_num, raw_line in enumerate(lines, start=1):
            # Strip comments but keep track of original line
            line = strip_comments(raw_line)

            for col, char in enumerate(line):
                # Check if this delimiter is escaped
                if is_escaped(line, col):
                    continue

                if char == opening:
                    # Push opening delimiter onto stack
                    stack.append((line_num, col + 1, raw_line))  # col+1 for 1-indexed

                elif char == closing:
                    if stack:
                        # Matching opening found, pop it
                        stack.pop()
                    else:
                        # Unmatched closing delimiter
                        unmatched.append(UnmatchedDelimiter(
                            delimiter_type=delimiter_type,
                            tag_type='close',
                            line_number=line_num,
                            column_number=col + 1,  # 1-indexed
                            line_content=raw_line.strip()
                        ))

        # Remaining items on stack are unmatched opening delimiters
        for line_num, col_num, line_content in stack:
            unmatched.append(UnmatchedDelimiter(
                delimiter_type=delimiter_type,
                tag_type='open',
                line_number=line_num,
                column_number=col_num,
                line_content=line_content.strip()
            ))

        return unmatched
