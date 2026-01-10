"""Standardized error type identifiers for LaTeX validation."""

from enum import Enum


class ErrorType(Enum):
    """Standardized error type identifiers.

    Provides consistent naming for all validation error types.
    """

    # Environment errors (existing)
    MISSING_END = "missing_end"
    UNMATCHED_END = "unmatched_end"
    DUPLICATE_BLOCK = "duplicate_block"

    # Delimiter errors (new)
    UNMATCHED_BRACE_OPEN = "unmatched_brace_open"
    UNMATCHED_BRACE_CLOSE = "unmatched_brace_close"
    UNMATCHED_BRACKET_OPEN = "unmatched_bracket_open"
    UNMATCHED_BRACKET_CLOSE = "unmatched_bracket_close"
    UNMATCHED_PAREN_OPEN = "unmatched_paren_open"
    UNMATCHED_PAREN_CLOSE = "unmatched_paren_close"

    # Syntax errors (existing + new)
    HTML_CLOSING_TAG = "html_closing_tag"
    HTML_OPENING_TAG = "html_opening_tag"
    HTML_XML_TAG = "html_xml_tag"

    # Nesting errors (new)
    INVALID_NESTING = "invalid_nesting"

    @property
    def display_name(self) -> str:
        """Human-readable error type name."""
        return self.value.replace('_', ' ').title()
