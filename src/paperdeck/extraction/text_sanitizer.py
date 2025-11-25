"""
Text sanitization for academic PDFs.

Removes common artifacts like page numbers, DOIs, headers, and footers
from extracted PDF text.
"""

import re
from typing import List
from src.paperdeck.core.config import TextExtractionConfig


class TextSanitizer:
    """
    Sanitizes extracted text by removing common PDF artifacts.

    Handles:
    - Page numbers (standalone digits)
    - DOI identifiers
    - arXiv identifiers
    - "Page X of Y" patterns
    - Repeated headers/footers
    - Very short lines (noise)
    """

    def __init__(self):
        """Initialize the text sanitizer."""
        # Patterns for artifact detection
        self._doi_pattern = re.compile(r"^DOI:\s*[\d.\/\w-]+\s*$", re.IGNORECASE | re.MULTILINE)
        self._arxiv_pattern = re.compile(r"^arXiv:\s*[\d.]+v?\d*\s*$", re.IGNORECASE | re.MULTILINE)
        self._page_x_of_y_pattern = re.compile(r"^Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE | re.MULTILINE)
        self._standalone_number_pattern = re.compile(r"^\d+$")

    def sanitize(self, text: str, config: TextExtractionConfig) -> str:
        """
        Sanitize extracted text by removing artifacts.

        Args:
            text: Raw extracted text from PDF
            config: Configuration for sanitization behavior

        Returns:
            Cleaned text with artifacts removed
        """
        if not text:
            return ""

        # Split into lines for processing
        lines = text.split("\n")

        # Apply sanitization filters
        if config.remove_headers_footers:
            lines = self._remove_doi_lines(lines)
            lines = self._remove_arxiv_lines(lines)
            lines = self._remove_page_x_of_y(lines)

        if config.remove_page_numbers:
            lines = self._remove_standalone_page_numbers(lines)
            # Remove short lines (noise) only after page numbers are removed
            lines = self._remove_short_lines(lines, config.min_line_length)
        else:
            # When page numbers are preserved, don't remove short lines that are just numbers
            lines = self._remove_short_lines_preserve_numbers(lines, config.min_line_length)

        # Remove repeated headers
        if config.remove_headers_footers:
            lines = self._remove_repeated_lines(lines)

        # Rejoin with newlines, preserving paragraph structure
        result = "\n".join(lines)

        # Clean up excessive whitespace while preserving paragraph breaks
        result = self._normalize_whitespace(result)

        return result

    def _remove_doi_lines(self, lines: List[str]) -> List[str]:
        """Remove lines containing DOI identifiers."""
        return [
            line for line in lines
            if not self._doi_pattern.match(line.strip())
        ]

    def _remove_arxiv_lines(self, lines: List[str]) -> List[str]:
        """Remove lines containing arXiv identifiers."""
        return [
            line for line in lines
            if not self._arxiv_pattern.match(line.strip())
        ]

    def _remove_page_x_of_y(self, lines: List[str]) -> List[str]:
        """Remove 'Page X of Y' pagination lines."""
        return [
            line for line in lines
            if not self._page_x_of_y_pattern.match(line.strip())
        ]

    def _remove_standalone_page_numbers(self, lines: List[str]) -> List[str]:
        """
        Remove standalone page numbers (lines with only a digit).

        Preserves lines where numbers are part of content.
        """
        result = []
        for line in lines:
            stripped = line.strip()
            # Only remove if it's JUST a number
            if not self._standalone_number_pattern.match(stripped):
                result.append(line)
        return result

    def _remove_short_lines(self, lines: List[str], min_length: int) -> List[str]:
        """Remove lines shorter than min_length (after stripping)."""
        return [
            line for line in lines
            if len(line.strip()) >= min_length or len(line.strip()) == 0
        ]

    def _remove_short_lines_preserve_numbers(self, lines: List[str], min_length: int) -> List[str]:
        """
        Remove lines shorter than min_length, but preserve standalone numbers.

        Used when remove_page_numbers=False to keep page numbers.
        """
        result = []
        for line in lines:
            stripped = line.strip()
            # Keep empty lines, numbers, or lines meeting min_length
            if len(stripped) == 0 or self._standalone_number_pattern.match(stripped) or len(stripped) >= min_length:
                result.append(line)
        return result

    def _remove_repeated_lines(self, lines: List[str]) -> List[str]:
        """
        Remove repeated lines that appear multiple times (headers/footers).

        Keeps first occurrence of any repeated line.
        """
        # Count occurrences
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if stripped:  # Ignore empty lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        # Find lines that repeat 2+ times (likely headers/footers)
        repeated_lines = {line for line, count in line_counts.items() if count >= 2}

        # Keep only first occurrence of repeated lines
        seen = set()
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Keep empty lines for paragraph structure
                result.append(line)
            elif stripped in repeated_lines:
                if stripped not in seen:
                    result.append(line)
                    seen.add(stripped)
                # Skip subsequent occurrences
            else:
                result.append(line)

        return result

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving paragraph breaks.

        - Multiple spaces become single space
        - 3+ newlines become 2 newlines (paragraph break)
        - Trailing/leading whitespace removed
        """
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)

        # Replace 3+ newlines with 2 newlines (paragraph break)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove spaces at start/end of lines
        lines = text.split("\n")
        lines = [line.strip() for line in lines]
        text = "\n".join(lines)

        # Remove leading/trailing whitespace from entire text
        return text.strip()
