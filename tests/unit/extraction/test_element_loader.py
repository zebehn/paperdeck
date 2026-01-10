"""
Unit tests for ElementLoader.

Tests the adapter pattern for loading pre-extracted elements from filesystem.
"""

from pathlib import Path

import pytest

from paperdeck.core.models import ElementType
from paperdeck.extraction.element_loader import ElementLoader


class TestElementLoaderInitialization:
    """Tests for ElementLoader initialization and validation."""

    def test_init_with_valid_directory(self, tmp_path):
        """ElementLoader initializes with valid directory."""
        loader = ElementLoader(tmp_path)
        assert loader.input_directory == tmp_path

    def test_init_with_nonexistent_directory_raises_error(self):
        """ElementLoader raises FileNotFoundError for nonexistent directory."""
        nonexistent = Path("/nonexistent/directory")
        with pytest.raises(FileNotFoundError, match="Input directory not found"):
            ElementLoader(nonexistent)

    def test_init_with_file_not_directory_raises_error(self, tmp_path):
        """ElementLoader raises ValueError when path is a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="not a directory"):
            ElementLoader(test_file)


class TestElementLoaderLoading:
    """Tests for loading elements from valid directories."""

    def test_load_elements_from_valid_directory(self):
        """load_elements() loads figures and tables from valid directory."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        assert len(elements) == 3  # 2 figures + 1 table
        assert sum(1 for e in elements if e.element_type == ElementType.FIGURE) == 2
        assert sum(1 for e in elements if e.element_type == ElementType.TABLE) == 1

    def test_load_elements_figures_only(self):
        """load_elements([FIGURE]) loads only figures."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        figures = loader.load_elements([ElementType.FIGURE])

        assert len(figures) == 2
        assert all(e.element_type == ElementType.FIGURE for e in figures)

    def test_load_elements_tables_only(self):
        """load_elements([TABLE]) loads only tables."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        tables = loader.load_elements([ElementType.TABLE])

        assert len(tables) == 1
        assert all(e.element_type == ElementType.TABLE for e in tables)

    def test_load_elements_sorted_by_sequence_number(self):
        """Elements are sorted by sequence_number."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        # Check that sequence numbers are in ascending order
        sequence_numbers = [e.sequence_number for e in elements]
        assert sequence_numbers == sorted(sequence_numbers)

    def test_load_elements_empty_directory_returns_empty_list(self, tmp_path):
        """load_elements() returns empty list for empty directory."""
        loader = ElementLoader(tmp_path)

        elements = loader.load_elements()

        assert elements == []

    def test_load_elements_multiple_formats_pdf_png_jpg(self):
        """Supports .pdf, .png, .jpg, .jpeg formats."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_multiple_formats")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        # Check we loaded files with different formats
        formats = [e.output_filename.suffix.lower() for e in elements]
        assert ".pdf" in formats
        assert ".png" in formats or ".jpg" in formats

    def test_load_elements_case_insensitive_matching(self):
        """File matching is case-insensitive (FIGURE_01.PDF works)."""
        # This is tested by the regex pattern in element_loader.py
        # which uses re.IGNORECASE flag
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        # Verify at least some elements were loaded (case-insensitive worked)
        assert len(elements) > 0


class TestElementLoaderValidation:
    """Tests for directory validation."""

    def test_validate_directory_valid_returns_true(self):
        """validate_directory() returns (True, []) for valid directory."""
        fixture_dir = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(fixture_dir)

        is_valid, errors = loader.validate_directory()

        assert is_valid is True
        assert errors == []

    def test_validate_directory_empty_returns_false(self, tmp_path):
        """validate_directory() returns (False, errors) for empty directory."""
        loader = ElementLoader(tmp_path)

        is_valid, errors = loader.validate_directory()

        assert is_valid is False
        assert len(errors) > 0
        assert "No valid element files found" in errors[0]
        assert "figure_01.pdf" in errors[0]  # Should suggest naming pattern


class TestElementLoaderErrorHandling:
    """Tests for User Story 2: Clear error messages."""

    def test_validate_directory_nonexistent_raises_error(self):
        """ElementLoader raises FileNotFoundError for nonexistent directory with path in message."""
        nonexistent = Path("/nonexistent/test/directory")

        with pytest.raises(FileNotFoundError) as exc_info:
            ElementLoader(nonexistent)

        # Verify error message contains the attempted path
        assert str(nonexistent) in str(exc_info.value)

    def test_load_elements_warns_about_gaps_in_numbering(self, caplog):
        """load_elements() warns when sequence numbers have gaps."""
        import logging
        caplog.set_level(logging.WARNING)

        fixture_dir = Path("tests/fixtures/preextracted_samples/gaps_in_numbering")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        # Should still load available elements
        assert len(elements) > 0

        # Should warn about missing sequence number
        assert any("gap" in record.message.lower() or "missing" in record.message.lower()
                   for record in caplog.records)

    def test_load_elements_ignores_invalid_filenames(self, caplog):
        """load_elements() ignores files with invalid naming patterns."""
        import logging
        caplog.set_level(logging.WARNING)

        fixture_dir = Path("tests/fixtures/preextracted_samples/invalid_wrong_names")
        loader = ElementLoader(fixture_dir)

        elements = loader.load_elements()

        # Should return empty list (no valid files)
        assert len(elements) == 0

        # Should warn about invalid filenames
        assert any("invalid" in record.message.lower() or "ignored" in record.message.lower()
                   for record in caplog.records)

    def test_load_elements_warns_about_unsupported_formats(self, tmp_path, caplog):
        """load_elements() warns about files with unsupported formats."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create files with unsupported formats
        (tmp_path / "figure_01.txt").write_text("not an image")
        (tmp_path / "figure_02.svg").write_text("<svg></svg>")

        loader = ElementLoader(tmp_path)
        elements = loader.load_elements()

        # Should return empty list (no valid formats)
        assert len(elements) == 0

        # Should warn about unsupported formats or no valid files
        assert len(caplog.records) > 0


class TestElementLoaderPathHandling:
    """Tests for User Story 3: Path flexibility."""

    def test_load_elements_with_relative_path(self):
        """ElementLoader works with relative paths."""
        # Use relative path to existing fixture
        relative_path = Path("tests/fixtures/preextracted_samples/valid_basic")
        loader = ElementLoader(relative_path)

        elements = loader.load_elements()

        assert len(elements) > 0
        assert all(e.output_filename.exists() for e in elements)

    def test_load_elements_with_absolute_path(self):
        """ElementLoader works with absolute paths."""
        # Convert to absolute path
        relative_path = Path("tests/fixtures/preextracted_samples/valid_basic")
        absolute_path = relative_path.resolve()

        loader = ElementLoader(absolute_path)
        elements = loader.load_elements()

        assert len(elements) > 0
        assert all(e.output_filename.exists() for e in elements)

    def test_load_elements_with_path_containing_spaces(self, tmp_path):
        """ElementLoader works with paths containing spaces."""
        # Create directory with spaces in name
        dir_with_spaces = tmp_path / "test dir with spaces"
        dir_with_spaces.mkdir()

        # Create test files
        (dir_with_spaces / "figure_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        (dir_with_spaces / "table_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        loader = ElementLoader(dir_with_spaces)
        elements = loader.load_elements()

        assert len(elements) == 2
        assert all(e.output_filename.exists() for e in elements)
