"""Delimiter types for LaTeX validation."""

from enum import Enum
from typing import Tuple


class DelimiterType(Enum):
    """Types of delimiters to validate in LaTeX.

    Each delimiter has an opening character, closing character, and display name.
    """

    BRACE = ('{', '}', 'brace')
    BRACKET = ('[', ']', 'bracket')
    PAREN = ('(', ')', 'paren')

    def __init__(self, opening: str, closing: str, name: str):
        self.opening = opening
        self.closing = closing
        self.display_name = name

    @property
    def pair(self) -> Tuple[str, str]:
        """Get opening and closing as tuple."""
        return (self.opening, self.closing)

    def is_opening(self, char: str) -> bool:
        """Check if character is opening delimiter."""
        return char == self.opening

    def is_closing(self, char: str) -> bool:
        """Check if character is closing delimiter."""
        return char == self.closing
