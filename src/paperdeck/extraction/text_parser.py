"""
Text parsing for academic papers.

Parses extracted text into structured sections with titles and content.
"""

import re
from typing import List, Optional, Tuple
from ..core.models import PaperSection


class AcademicTextParser:
    """
    Parses academic paper text into structured sections.

    Identifies common section headings and splits text accordingly.
    """

    # Common section headings in academic papers
    SECTION_PATTERNS = [
        r'^#+\s*(abstract|introduction|related work|methodology|methods|approach|'
        r'model|architecture|experiments|evaluation|results|discussion|'
        r'conclusion|conclusions|references|acknowledgments?)',
        r'^\d+\.?\s+(Abstract|Introduction|Related Work|Methodology|Methods|Approach|'
        r'Model|Architecture|Experiments|Evaluation|Results|Discussion|'
        r'Conclusion|Conclusions|References|Acknowledgments?)',
        r'^(Abstract|Introduction|Related Work|Methodology|Methods|Approach|'
        r'Model|Architecture|Experiments|Evaluation|Results|Discussion|'
        r'Conclusion|Conclusions|References|Acknowledgments?)$',
    ]

    def __init__(self, min_section_length: int = 100):
        """
        Initialize text parser.

        Args:
            min_section_length: Minimum characters for a valid section
        """
        self.min_section_length = min_section_length
        self.section_regex = re.compile(
            '|'.join(self.SECTION_PATTERNS),
            re.MULTILINE | re.IGNORECASE
        )

    def parse(self, text: str) -> Tuple[Optional[str], List[str], List[PaperSection]]:
        """
        Parse text into title, authors, and sections.

        Args:
            text: Raw extracted text from PDF

        Returns:
            Tuple of (title, authors, sections):
                - title: Extracted paper title (or None)
                - authors: List of author names
                - sections: List of PaperSection objects
        """
        if not text or len(text) < 100:
            return None, [], []

        # Extract title and authors from first few lines
        title, authors, text_start = self._extract_metadata(text)

        # Parse sections
        sections = self._parse_sections(text[text_start:])

        return title, authors, sections

    def _extract_metadata(self, text: str) -> Tuple[Optional[str], List[str], int]:
        """
        Extract title and authors from beginning of text.

        Args:
            text: Raw text

        Returns:
            Tuple of (title, authors, text_start_index)
        """
        lines = text.split('\n')

        # Title is usually in first 5 non-empty lines
        title = None
        authors = []
        text_start_line = 0

        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line:
                continue

            # First substantial line is likely the title
            if title is None and len(line) > 20:
                title = line
                text_start_line = i + 1
                continue

            # Next substantial lines might be authors
            # Look for patterns like "Name1, Name2" or "Name1 and Name2"
            if title and not authors and len(line) > 10:
                # Simple heuristic: if line has commas or "and", likely authors
                if ',' in line or ' and ' in line.lower():
                    # Split by comma or "and"
                    author_parts = re.split(r',\s*|\s+and\s+', line, flags=re.IGNORECASE)
                    authors = [a.strip() for a in author_parts if a.strip()]
                    text_start_line = i + 1
                    break
                # Also check if line looks like author names (capital letters)
                elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', line):
                    authors.append(line)
                    text_start_line = i + 1

        # Calculate character position
        text_start_char = len('\n'.join(lines[:text_start_line]))

        return title, authors, text_start_char

    def _parse_sections(self, text: str) -> List[PaperSection]:
        """
        Parse text into sections based on headings.

        Args:
            text: Text to parse (after metadata)

        Returns:
            List of PaperSection objects
        """
        sections = []

        # Find all section matches
        matches = list(self.section_regex.finditer(text))

        if not matches:
            # No sections found - create one generic section
            if len(text) > self.min_section_length:
                section = PaperSection(
                    title="Content",
                    content=text[:5000],  # Limit to 5000 chars
                    level=1,
                    page_start=1,
                    page_end=1,
                )
                sections.append(section)
            return sections

        # Extract sections between matches
        for i, match in enumerate(matches):
            # Get section title
            section_title = match.group(0).strip()
            # Clean up title (remove numbering, markdown, etc.)
            section_title = re.sub(r'^#+\s*', '', section_title)  # Remove markdown
            section_title = re.sub(r'^\d+\.?\s*', '', section_title)  # Remove numbering
            section_title = section_title.strip()

            # Get section content (from this match to next match)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            # Skip if too short
            if len(content) < self.min_section_length:
                continue

            # Limit content length
            content = content[:5000]

            section = PaperSection(
                title=section_title,
                content=content,
                level=1,
                page_start=1,  # We don't track pages in text extraction
                page_end=1,
            )
            sections.append(section)

        return sections
