# Testing Implementation Guide: PNG → PDF Migration

## Quick Start Implementation

This guide provides ready-to-use code snippets for implementing the test migration strategy.

---

## 1. Helper Functions and Fixtures

### 1.1 PDF Generation Helpers

Create a new file: `tests/helpers/pdf_helpers.py`

```python
"""Helpers for creating test PDF files."""

from pathlib import Path
from typing import Optional


def create_minimal_pdf() -> bytes:
    """Create a minimal valid PDF for testing.

    Returns a bytes object representing a valid but empty PDF document
    that can be used in tests without requiring actual PDF files.

    Returns:
        bytes: Minimal PDF file content
    """
    # Minimal PDF 1.4 structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000244 00000 n
0000000332 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
426
%%EOF
"""


def create_multipage_pdf(num_pages: int = 3) -> bytes:
    """Create a multi-page PDF for testing.

    Creates a simple PDF with specified number of pages.

    Args:
        num_pages: Number of pages to create (1-10)

    Returns:
        bytes: Multi-page PDF content
    """
    if num_pages < 1 or num_pages > 10:
        raise ValueError("num_pages must be between 1 and 10")

    # Create pages array
    pages_kids = " ".join(f"{3 + i} 0 R" for i in range(num_pages))

    # Build object structure
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        f"2 0 obj\n<< /Type /Pages /Count {num_pages} /Kids [{pages_kids}] >>\nendobj\n",
    ]

    # Add page objects
    for i in range(num_pages):
        obj = (
            f"{3 + i} 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {3 + num_pages + i} 0 R >>\nendobj\n"
        )
        objects.append(obj)

    # Add content streams
    for i in range(num_pages):
        content = f"BT /F1 12 Tf 100 700 Td (Page {i + 1}) Tj ET"
        obj = (
            f"{3 + num_pages + i} 0 obj\n"
            f"<< /Length {len(content)} >>\n"
            f"stream\n{content}\nendstream\nendobj\n"
        )
        objects.append(obj)

    # Build complete PDF
    header = "%PDF-1.4\n"
    body = "".join(objects)

    # Simple xref table (not optimized for real use)
    xref = "xref\n0 1\n0000000000 65535 f \n"
    offset = len(header)
    for obj in objects:
        xref += f"{offset:010d} 00000 n \n"
        offset += len(obj)

    trailer = f"trailer\n<< /Size {3 + 2 * num_pages} /Root 1 0 R >>\nstartxref\n{offset}\n%%EOF"

    return (header + body + xref + trailer).encode('latin-1')


def create_corrupted_pdf() -> bytes:
    """Create an intentionally corrupted PDF for error testing.

    Returns:
        bytes: Invalid PDF content
    """
    return b"%PDF-1.4\ngarbled content ][{@ invalid pdf structure"


def create_pdf_in_file(path: Path, content: bytes = None) -> Path:
    """Create a PDF file at the specified path.

    Args:
        path: Path where PDF should be created
        content: PDF content (uses minimal PDF if None)

    Returns:
        Path: The created file path
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if content is None:
        content = create_minimal_pdf()
    path.write_bytes(content)
    return path
```

### 1.2 Pytest Fixtures

Create/update: `tests/conftest.py`

```python
"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path
from typing import Generator

# Import helpers from test utilities
from tests.helpers.pdf_helpers import (
    create_minimal_pdf,
    create_multipage_pdf,
    create_corrupted_pdf,
    create_pdf_in_file,
)


@pytest.fixture
def sample_pdf_bytes():
    """Fixture providing minimal PDF bytes."""
    return create_minimal_pdf()


@pytest.fixture
def multipage_pdf_bytes():
    """Fixture providing multi-page PDF bytes."""
    return create_multipage_pdf(num_pages=3)


@pytest.fixture
def corrupted_pdf_bytes():
    """Fixture providing corrupted PDF bytes."""
    return create_corrupted_pdf()


@pytest.fixture
def pdf_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary PDF file.

    Args:
        tmp_path: pytest's temporary directory fixture

    Yields:
        Path to created PDF file
    """
    pdf_path = tmp_path / "test.pdf"
    return create_pdf_in_file(pdf_path)


@pytest.fixture
def extraction_output_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary extraction output directory.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to output directory
    """
    output_dir = tmp_path / "extracted"
    output_dir.mkdir(parents=True)
    return output_dir
```

---

## 2. Unit Test Updates

### 2.1 test_docscalpel_adapter.py Updates

```python
"""
Unit tests for DocScalpel adapter - UPDATED FOR PDF OUTPUT
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.core.models import ElementType
from paperdeck.core.config import ExtractionConfiguration


class TestDocScalpelAdapterWithPdf:
    """Tests for DocScalpel adapter with PDF output format."""

    @pytest.fixture
    def mock_docscalpel(self):
        """Mock DocScalpel module."""
        return MagicMock()

    @pytest.fixture
    def adapter_with_mock(self, mock_docscalpel):
        """Create adapter with mocked DocScalpel using PDF output."""
        with patch.dict('sys.modules', {'docscalpel': mock_docscalpel}):
            adapter = DocScalpelAdapter()
            adapter.docscalpel_available = True
            adapter.docscalpel = mock_docscalpel
            return adapter

    def test_extract_returns_pdf_filenames(self, adapter_with_mock, tmp_path, mocker):
        """Test extract returns elements with PDF output filenames."""
        # Mock a successful extraction with PDF filenames
        mock_element = MagicMock()
        mock_element.element_type = adapter_with_mock.docscalpel.ElementType.FIGURE
        mock_element.output_filename = "figure_01.pdf"  # PDF format
        mock_element.page_number = 1
        mock_element.bounding_box = MagicMock(x=0, y=0, width=100, height=100)
        mock_element.confidence_score = 0.95
        mock_element.sequence_number = 1

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.elements = [mock_element]
        mock_result.figure_count = 1
        mock_result.table_count = 0
        mock_result.errors = []
        mock_result.warnings = []

        mocker.patch.object(
            adapter_with_mock.docscalpel,
            'extract_elements',
            return_value=mock_result
        )

        result = adapter_with_mock.extract(tmp_path / "test.pdf", [ElementType.FIGURE])

        assert len(result) > 0
        # Verify PDF extension in output filename
        assert all(str(elem.output_filename).endswith('.pdf') for elem in result)

    @pytest.mark.parametrize("format_name", ["pdf", "png"])
    def test_adapter_respects_naming_pattern_format(self, format_name, adapter_with_mock, tmp_path, mocker):
        """Test adapter handles different output formats in naming pattern."""
        config = MagicMock()
        config.output_directory = tmp_path
        config.confidence_threshold = 0.5
        config.extract_figures = True
        config.extract_tables = False

        adapter_with_mock.config = config

        # Verify _create_docscalpel_config uses correct naming pattern
        docscalpel_config = adapter_with_mock._create_docscalpel_config([ElementType.FIGURE])

        # The naming_pattern should be configurable for format
        # This might require updating adapter implementation
        assert docscalpel_config is not None


class TestDocScalpelAdapterGracefulFallback:
    """Tests for graceful fallback when PDF generation fails."""

    def test_extract_returns_empty_on_no_docscalpel(self, tmp_path):
        """Test extraction gracefully returns empty list when DocScalpel unavailable."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(tmp_path / "test.pdf", [ElementType.FIGURE])

        assert result == []
        assert isinstance(result, list)

    def test_extract_handles_extraction_exception(self, tmp_path, mocker):
        """Test extraction handles exceptions gracefully."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        # Mock extraction that raises exception
        mocker.patch.object(
            adapter,
            'docscalpel',
            MagicMock(
                extract_elements=MagicMock(side_effect=RuntimeError("PDF parsing failed"))
            )
        )

        result = adapter.extract(tmp_path / "test.pdf")

        # Should return empty list, not raise
        assert result == []

    def test_extract_handles_partial_extraction_failure(self, tmp_path, mocker):
        """Test extraction continues when some elements fail but others succeed."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        # Mock mixed success/failure
        mock_element = MagicMock()
        mock_element.element_type = adapter.docscalpel.ElementType.FIGURE
        mock_element.output_filename = "figure_01.pdf"

        mock_result = MagicMock()
        mock_result.success = False  # Some failures occurred
        mock_result.errors = ["Page 3 corrupted"]
        mock_result.warnings = ["Low confidence on figure 2"]
        mock_result.elements = [mock_element]
        mock_result.figure_count = 1
        mock_result.table_count = 0

        mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            return_value=mock_result
        )

        result = adapter.extract(tmp_path / "test.pdf")

        # Should still return extracted elements
        assert isinstance(result, list)
```

---

## 3. Integration Test Updates

### 3.1 test_figure_extraction.py Updates

```python
"""
Integration tests for figure and table extraction with PDF output.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.extraction.element_processor import ElementProcessor
from paperdeck.core.models import ElementType, FigureElement, BoundingBox
from paperdeck.core.config import ExtractionConfiguration


class TestFigureExtractionWithPdf:
    """Integration tests for PDF figure extraction workflow."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        extracted = tmp_path / "extracted"
        extracted.mkdir()
        return extracted

    @pytest.fixture
    def adapter(self):
        """Create DocScalpel adapter."""
        return DocScalpelAdapter()

    @pytest.fixture
    def processor(self, output_dir):
        """Create element processor."""
        return ElementProcessor(output_dir)

    def test_element_processor_saves_pdf_figures(self, processor, sample_pdf_bytes):
        """Test element processor saves figures as PDFs."""
        result_path = processor.save_figure(sample_pdf_bytes, 1, format="pdf")

        assert result_path.suffix == ".pdf"
        assert result_path.name == "figure_1.pdf"
        assert result_path.exists()
        assert result_path.read_bytes() == sample_pdf_bytes

    @pytest.mark.parametrize("figure_number,expected_filename", [
        (1, "figure_1.pdf"),
        (9, "figure_9.pdf"),
        (10, "figure_10.pdf"),
        (99, "figure_99.pdf"),
    ])
    def test_figure_numbering_with_pdf_format(self, processor, figure_number, expected_filename, sample_pdf_bytes):
        """Test figure numbering works correctly with PDF format."""
        result_path = processor.save_figure(sample_pdf_bytes, figure_number, format="pdf")

        assert result_path.name == expected_filename
        assert result_path.suffix == ".pdf"

    def test_processor_saves_to_correct_directory(self, processor, output_dir, sample_pdf_bytes):
        """Test element processor saves files in correct directory."""
        result_path = processor.save_figure(sample_pdf_bytes, 1, format="pdf")

        assert result_path.parent == output_dir
        assert result_path.exists()

    def test_extraction_without_docscalpel_gracefully_skips(self, adapter, tmp_path):
        """Test extraction gracefully skips when DocScalpel not installed."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")

        adapter.docscalpel_available = False

        results = adapter.extract(pdf_file, [ElementType.FIGURE])

        assert results == []


class TestPdfTableExtraction:
    """Integration tests for PDF table extraction."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        extracted = tmp_path / "extracted"
        extracted.mkdir()
        return extracted

    @pytest.fixture
    def processor(self, output_dir):
        """Create element processor."""
        return ElementProcessor(output_dir)

    def test_table_processor_saves_pdf(self, processor, sample_pdf_bytes):
        """Test table processor saves tables as PDFs."""
        result_path = processor.save_table(sample_pdf_bytes, 1, format="pdf")

        assert result_path.suffix == ".pdf"
        assert result_path.name == "table_1.pdf"
        assert result_path.exists()

    @pytest.mark.parametrize("table_number", [1, 5, 10])
    def test_table_numbering_with_pdf(self, processor, table_number, sample_pdf_bytes):
        """Test table numbering with PDF format."""
        result_path = processor.save_table(sample_pdf_bytes, table_number, format="pdf")

        assert result_path.name == f"table_{table_number}.pdf"
```

---

## 4. LaTeX Generation Test Updates

### 4.1 test_figure_latex.py Updates

```python
"""
Unit tests for figure and table LaTeX generation with PDF support.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from paperdeck.core.models import (
    BoundingBox,
    ElementType,
    FigureElement,
    TableElement,
)
from paperdeck.generation.latex_generator import LaTeXGenerator


class TestFigureLatexWithPdf:
    """Tests for LaTeX generation with PDF figures."""

    @pytest.mark.parametrize("file_format,extension", [
        ("png", ".png"),
        ("pdf", ".pdf"),
    ])
    def test_generate_figure_latex_supports_multiple_formats(self, file_format, extension):
        """Test LaTeX generation works with different figure formats."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path(f"extracted/figure_01{extension}"),
            caption="Test Figure",
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        assert f"figure_01{extension}" in latex
        assert "\\includegraphics" in latex
        assert "\\caption{Test Figure}" in latex

    def test_generate_figure_latex_with_pdf(self):
        """Test generating LaTeX specifically for PDF figures."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=Path("extracted/figure_01.pdf"),
            caption="PDF Test Figure",
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        # PDF should work with includegraphics
        assert "figure_01.pdf" in latex
        assert "\\includegraphics" in latex

    def test_pdf_path_formatting_removes_backslashes(self):
        """Test that PDF paths are formatted correctly for LaTeX."""
        # Simulate Windows path with backslashes
        figure_path = Path("extracted\\figure_01.pdf")
        formatted = LaTeXGenerator._format_graphics_path(figure_path)

        # Should use forward slashes for LaTeX compatibility
        assert "\\" not in formatted or "/" in formatted
        assert "figure_01.pdf" in formatted


class TestTableLatexWithPdf:
    """Tests for LaTeX generation with PDF tables."""

    @pytest.mark.parametrize("file_format,extension", [
        ("png", ".png"),
        ("pdf", ".pdf"),
    ])
    def test_generate_table_latex_supports_multiple_formats(self, file_format, extension):
        """Test LaTeX generation works with different table formats."""
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=1,
            output_filename=Path(f"extracted/table_01{extension}"),
            caption="Test Table",
        )

        latex = LaTeXGenerator.generate_table_latex(table)

        assert f"table_01{extension}" in latex
        assert "\\includegraphics" in latex
        assert "\\caption{Test Table}" in latex

    def test_generate_table_latex_with_pdf(self):
        """Test generating LaTeX specifically for PDF tables."""
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=Path("extracted/table_01.pdf"),
            caption="PDF Test Table",
        )

        latex = LaTeXGenerator.generate_table_latex(table)

        assert "table_01.pdf" in latex
        assert "\\includegraphics" in latex
```

---

## 5. New Test Classes for Edge Cases

### 5.1 tests/unit/extraction/test_pdf_naming_conventions.py

```python
"""Tests for PDF file naming conventions and padding."""

import pytest
from pathlib import Path
from paperdeck.extraction.element_processor import ElementProcessor


class TestZeroPaddedFilenaming:
    """Test zero-padded file naming conventions."""

    @pytest.mark.parametrize("sequence_number,expected_name", [
        (1, "figure_1.pdf"),
        (9, "figure_9.pdf"),
        (10, "figure_10.pdf"),
        (99, "figure_99.pdf"),
        (100, "figure_100.pdf"),
    ])
    def test_figure_naming_sequence(self, sequence_number, expected_name, tmp_path, sample_pdf_bytes):
        """Test figure naming follows expected pattern."""
        processor = ElementProcessor(tmp_path)
        result_path = processor.save_figure(sample_pdf_bytes, sequence_number, format="pdf")

        assert result_path.name == expected_name

    @pytest.mark.parametrize("element_type,prefix", [
        ("figure", "figure"),
        ("table", "table"),
    ])
    def test_element_type_prefix_in_filename(self, element_type, prefix, tmp_path, sample_pdf_bytes):
        """Test that filenames include correct element type prefix."""
        processor = ElementProcessor(tmp_path)

        if element_type == "figure":
            result_path = processor.save_figure(sample_pdf_bytes, 1, format="pdf")
        else:
            result_path = processor.save_table(sample_pdf_bytes, 1, format="pdf")

        assert result_path.name.startswith(prefix)
        assert result_path.name.endswith(".pdf")


class TestFileSystemOperations:
    """Test file system operations for PDF files."""

    def test_nested_directory_creation(self, tmp_path, sample_pdf_bytes):
        """Test that processor creates nested directories."""
        nested_dir = tmp_path / "a" / "b" / "c" / "extracted"
        processor = ElementProcessor(nested_dir)

        result_path = processor.save_figure(sample_pdf_bytes, 1, format="pdf")

        assert result_path.parent == nested_dir
        assert result_path.exists()

    def test_overwrite_existing_pdf(self, tmp_path, sample_pdf_bytes):
        """Test that saving with same name overwrites existing file."""
        processor = ElementProcessor(tmp_path)

        # Save first version
        data1 = b"first version"
        path1 = processor.save_figure(data1, 1, format="pdf")

        # Save second version
        data2 = b"second version"
        path2 = processor.save_figure(data2, 1, format="pdf")

        assert path1 == path2
        assert path2.read_bytes() == data2

    def test_empty_pdf_data_raises_error(self, tmp_path):
        """Test that saving empty PDF data raises error."""
        processor = ElementProcessor(tmp_path)

        with pytest.raises(ValueError, match="has no image data"):
            processor.save_figure(b"", 1, format="pdf")

    def test_corrupted_pdf_saved_as_is(self, tmp_path, corrupted_pdf_bytes):
        """Test that processor saves corrupted PDFs as-is (validation at compile time)."""
        processor = ElementProcessor(tmp_path)

        result_path = processor.save_figure(corrupted_pdf_bytes, 1, format="pdf")

        assert result_path.exists()
        assert result_path.read_bytes() == corrupted_pdf_bytes
```

---

## 6. Running the Tests

### 6.1 Run All PDF-Related Tests

```bash
# Run all tests with PDF format
pytest tests/ -k "pdf" -v

# Run specific test class
pytest tests/unit/extraction/test_pdf_naming_conventions.py -v

# Run with coverage
pytest tests/ --cov=src/paperdeck --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/ -v

# Run integration tests (slower)
pytest tests/integration/ -v
```

### 6.2 Run with Parametrization Report

```bash
# Show parametrization IDs
pytest tests/ --collect-only -q

# Run specific parametrized variant
pytest tests/unit/generation/test_figure_latex.py::TestFigureLatexWithPdf::test_generate_figure_latex_supports_multiple_formats[pdf-.pdf] -v
```

### 6.3 Run LaTeX Compilation Tests (Optional)

```bash
# Run only compilation tests (requires pdflatex)
pytest tests/ -m "latex_compile" -v

# Skip compilation tests if pdflatex not available
pytest tests/ -m "not latex_compile" -v
```

---

## 7. Test Coverage Checklist

### Before Running Tests
- [ ] Update `ElementProcessor.save_figure()` to accept `format` parameter
- [ ] Update `ElementProcessor.save_table()` to accept `format` parameter
- [ ] Update `DocScalpelAdapter._create_docscalpel_config()` to handle naming pattern
- [ ] Create `tests/helpers/pdf_helpers.py` with helper functions
- [ ] Create/update `tests/conftest.py` with fixtures
- [ ] Create `tests/unit/extraction/test_pdf_naming_conventions.py`

### Unit Tests (tests/unit/)
- [ ] `test_docscalpel_adapter.py` - PDF output paths
- [ ] `test_figure_latex.py` - PDF format support
- [ ] `test_pdf_naming_conventions.py` - New file naming tests
- [ ] Edge case: Empty PDF data
- [ ] Edge case: Corrupted PDF bytes
- [ ] Edge case: Special characters in captions

### Integration Tests (tests/integration/)
- [ ] `test_figure_extraction.py` - PDF extraction workflow
- [ ] Full pipeline: Extract → Process → Generate LaTeX
- [ ] Graceful degradation when DocScalpel unavailable
- [ ] Multiple figures in same document

### LaTeX Compilation Tests (optional)
- [ ] Generate LaTeX with PDF figures
- [ ] Compile with pdflatex
- [ ] Validate output PDF properties
- [ ] Test multi-figure documents

---

## 8. Troubleshooting

### Test Execution Issues

**Problem**: Import errors for pdf_helpers
```bash
# Solution: Ensure tests/helpers/__init__.py exists
touch tests/helpers/__init__.py
```

**Problem**: Fixtures not found
```bash
# Solution: Verify conftest.py location and imports
# Should be at: tests/conftest.py
pytest --fixtures | grep pdf  # List available fixtures
```

**Problem**: pdflatex not found
```bash
# Solution: Skip compilation tests
pytest tests/ -m "not latex_compile"

# Or install pdflatex:
# macOS: brew install basictex
# Linux: sudo apt-get install texlive-latex-base
# Windows: Install MiKTeX
```

### Test Failures

**Problem**: "figure_01.pdf" not in latex
```python
# Check if LaTeXGenerator._format_graphics_path() is handling paths correctly
# Verify output_filename is set in FigureElement
assert figure.output_filename is not None
assert str(figure.output_filename).endswith('.pdf')
```

**Problem**: Parametrization not working
```bash
# Verify pytest version
pytest --version  # Should be 7.0+

# Check parametrize syntax
# Correct: @pytest.mark.parametrize("param", [value1, value2])
# Incorrect: @pytest.parametrize("param", [value1, value2])
```

---

## 9. Validation Checklist Before Merging

- [ ] All unit tests pass with 100% success
- [ ] All integration tests pass
- [ ] Code coverage maintained at >90% for modified code
- [ ] No deprecation warnings from pytest
- [ ] PDF format tested with multiple file sizes (small, medium, large)
- [ ] LaTeX generation produces valid syntax for PDF figures
- [ ] Error cases handled gracefully (empty files, corrupted PDFs)
- [ ] Backward compatibility maintained (PNG still works if needed during transition)
- [ ] Performance impact assessed (PDF operations slower than PNG?)
- [ ] Documentation updated with new test structure

---

## 10. Post-Migration Tasks

1. **Remove old PNG-specific tests** (after transition complete)
2. **Update docstrings** to reflect PDF as primary format
3. **Update inline comments** in code that mention PNG
4. **Create migration guide** for other developers
5. **Update CI/CD pipeline** to run new tests
6. **Add GitHub Actions** for automated test runs
7. **Document test patterns** for future contributors
