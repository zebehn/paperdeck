"""
Unit tests for TextSanitizer.

Following TDD approach: These tests are written FIRST and should FAIL initially.
Tests define the expected behavior of text sanitization.
"""

import pytest
from src.paperdeck.extraction.text_sanitizer import TextSanitizer
from src.paperdeck.core.config import TextExtractionConfig


class TestTextSanitizerHeaderFooterRemoval:
    """Tests for header and footer removal functionality."""

    @pytest.fixture
    def sanitizer(self):
        """Create a text sanitizer instance."""
        return TextSanitizer()

    @pytest.fixture
    def default_config(self):
        """Create default extraction config."""
        return TextExtractionConfig()

    def test_sanitize_removes_page_numbers(self, sanitizer, default_config):
        """Test that sanitize() removes standalone page numbers."""
        # This test will FAIL initially (TextSanitizer doesn't exist yet)

        text_with_page_numbers = """Abstract: This paper presents a novel approach.

1

Introduction: Recent advances in machine learning.

2

Results: Our experiments show significant improvements.

3"""

        result = sanitizer.sanitize(text_with_page_numbers, default_config)

        # Page numbers (standalone digits) should be removed
        assert "\n1\n" not in result
        assert "\n2\n" not in result
        assert "\n3\n" not in result

        # But content should remain
        assert "Abstract" in result
        assert "Introduction" in result
        assert "Results" in result

    def test_sanitize_removes_doi_lines(self, sanitizer, default_config):
        """Test that sanitize() removes DOI identifier lines."""
        # This test will FAIL initially

        text_with_doi = """Abstract: This is the abstract.

DOI: 10.1234/example.2023.12345

Introduction: This is the introduction."""

        result = sanitizer.sanitize(text_with_doi, default_config)

        # DOI line should be removed
        assert "DOI:" not in result
        assert "10.1234" not in result

        # Content should remain
        assert "Abstract" in result
        assert "Introduction" in result

    def test_sanitize_removes_arxiv_identifiers(self, sanitizer, default_config):
        """Test that sanitize() removes arXiv identifier lines."""
        # This test will FAIL initially

        text_with_arxiv = """Abstract: Novel deep learning approach.

arXiv:2301.12345v2

Introduction: Recent work has shown..."""

        result = sanitizer.sanitize(text_with_arxiv, default_config)

        # arXiv identifier should be removed
        assert "arXiv:" not in result
        assert "2301.12345" not in result

        # Content should remain
        assert "Abstract" in result
        assert "Introduction" in result

    def test_sanitize_removes_page_x_of_y_patterns(self, sanitizer, default_config):
        """Test that sanitize() removes 'Page X of Y' patterns."""
        # This test will FAIL initially

        text_with_pagination = """Some content on this page.

Page 5 of 20

More content continues here."""

        result = sanitizer.sanitize(text_with_pagination, default_config)

        # Pagination should be removed
        assert "Page 5 of 20" not in result

        # Content should remain
        assert "Some content" in result
        assert "More content" in result

    def test_sanitize_removes_repeated_headers(self, sanitizer, default_config):
        """Test that sanitize() removes repeated header patterns."""
        # This test will FAIL initially

        text_with_headers = """Content from page 1.

Author et al. - Paper Title

Content from page 2.

Author et al. - Paper Title

Content from page 3."""

        result = sanitizer.sanitize(text_with_headers, default_config)

        # Repeated headers should be reduced or removed
        # (At minimum, should not have multiple identical header lines)
        header_count = result.count("Author et al. - Paper Title")
        assert header_count <= 1  # Should remove duplicates


class TestTextSanitizerPatternMatching:
    """Tests for pattern-based text cleaning."""

    @pytest.fixture
    def sanitizer(self):
        return TextSanitizer()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    def test_sanitize_removes_very_short_lines(self, sanitizer, default_config):
        """Test that sanitize() removes very short lines based on min_line_length."""
        # This test will FAIL initially

        text_with_short_lines = """This is a proper line of text.
a
b
This is another proper line.
x
More good content here."""

        result = sanitizer.sanitize(text_with_short_lines, default_config)

        # Single character lines should be removed (min_line_length=3)
        lines = result.split('\n')
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 0:
                assert len(stripped) >= 3, f"Found short line: '{stripped}'"

        # Good content should remain
        assert "proper line of text" in result
        assert "another proper line" in result

    def test_sanitize_preserves_content_with_numbers(self, sanitizer, default_config):
        """Test that sanitize() preserves content that happens to contain numbers."""
        # This test will FAIL initially

        text_with_content_numbers = """We tested with 2 different models.
The accuracy improved by 15 percent.
Table 1 shows the results.
Figure 3 illustrates the approach."""

        result = sanitizer.sanitize(text_with_content_numbers, default_config)

        # Content with numbers should be preserved (not treated as page numbers)
        assert "2 different models" in result
        assert "15 percent" in result
        assert "Table 1" in result
        assert "Figure 3" in result

    def test_sanitize_handles_empty_string(self, sanitizer, default_config):
        """Test that sanitize() handles empty string gracefully."""
        # This test will FAIL initially

        result = sanitizer.sanitize("", default_config)

        assert isinstance(result, str)
        assert len(result) == 0

    def test_sanitize_handles_whitespace_only(self, sanitizer, default_config):
        """Test that sanitize() handles whitespace-only text."""
        # This test will FAIL initially

        text_whitespace = "   \n  \n\t\n  "

        result = sanitizer.sanitize(text_whitespace, default_config)

        assert isinstance(result, str)
        # Should return empty or minimal whitespace
        assert len(result.strip()) == 0


class TestTextSanitizerConfiguration:
    """Tests for configuration-driven sanitization behavior."""

    @pytest.fixture
    def sanitizer(self):
        return TextSanitizer()

    def test_sanitize_respects_remove_page_numbers_setting(self, sanitizer):
        """Test that sanitize() respects remove_page_numbers config."""
        # This test will FAIL initially

        text = "Introduction\n1\nResults\n2\nConclusion"

        # With removal enabled
        config_enabled = TextExtractionConfig(remove_page_numbers=True)
        result_enabled = sanitizer.sanitize(text, config_enabled)

        # With removal disabled
        config_disabled = TextExtractionConfig(remove_page_numbers=False)
        result_disabled = sanitizer.sanitize(text, config_disabled)

        # Enabled should remove page numbers
        assert "\n1\n" not in result_enabled

        # Disabled should preserve them
        assert "1" in result_disabled

    def test_sanitize_respects_min_line_length_setting(self, sanitizer):
        """Test that sanitize() respects min_line_length config."""
        # This test will FAIL initially

        text = "Good content\na\nbb\nccc\nMore content"

        # With min_line_length=3
        config_3 = TextExtractionConfig(min_line_length=3)
        result_3 = sanitizer.sanitize(text, config_3)

        # With min_line_length=5
        config_5 = TextExtractionConfig(min_line_length=5)
        result_5 = sanitizer.sanitize(text, config_5)

        # config_3 should keep "ccc" (length 3)
        assert "ccc" in result_3

        # config_5 should remove "ccc" (length 3 < 5)
        assert "ccc" not in result_5

        # Both should keep longer content
        assert "Good content" in result_3
        assert "Good content" in result_5

    def test_sanitize_respects_remove_headers_footers_setting(self, sanitizer):
        """Test that sanitize() respects remove_headers_footers config."""
        # This test will FAIL initially

        text = "Content\nDOI: 10.1234/test\nMore content"

        # With removal enabled
        config_enabled = TextExtractionConfig(remove_headers_footers=True)
        result_enabled = sanitizer.sanitize(text, config_enabled)

        # With removal disabled
        config_disabled = TextExtractionConfig(remove_headers_footers=False)
        result_disabled = sanitizer.sanitize(text, config_disabled)

        # Enabled should remove DOI
        assert "DOI:" not in result_enabled

        # Disabled should preserve DOI
        assert "DOI:" in result_disabled


class TestTextSanitizerQuality:
    """Tests for sanitization quality and edge cases."""

    @pytest.fixture
    def sanitizer(self):
        return TextSanitizer()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    def test_sanitize_preserves_paragraph_structure(self, sanitizer, default_config):
        """Test that sanitize() preserves paragraph breaks."""
        # This test will FAIL initially

        text = """First paragraph with multiple sentences. This is important content.

Second paragraph starts here. It also has content.

Third paragraph concludes the section."""

        result = sanitizer.sanitize(text, default_config)

        # Should still have paragraph breaks (double newlines)
        assert "\n\n" in result or result.count('\n') >= 2

        # All paragraphs should be present
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "Third paragraph" in result

    def test_sanitize_returns_string_type(self, sanitizer, default_config):
        """Test that sanitize() always returns string."""
        # This test will FAIL initially

        test_inputs = [
            "Normal text",
            "",
            "Text with\nnewlines",
            "   Leading and trailing spaces   "
        ]

        for text in test_inputs:
            result = sanitizer.sanitize(text, default_config)
            assert isinstance(result, str)

    def test_sanitize_does_not_crash_on_special_characters(self, sanitizer, default_config):
        """Test that sanitize() handles special characters gracefully."""
        # This test will FAIL initially

        text_with_special = """Text with special chars: α β γ δ ε
Mathematical symbols: ∫ ∑ √ ∞
Unicode: 你好 مرحبا こんにちは"""

        result = sanitizer.sanitize(text_with_special, default_config)

        # Should not crash and should return valid string
        assert isinstance(result, str)
        # Should preserve most content
        assert len(result) > 0
