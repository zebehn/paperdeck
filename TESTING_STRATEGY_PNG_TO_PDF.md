# Testing Strategy for File Format Changes: PNG → PDF Migration

## Executive Summary

This document provides comprehensive strategies for migrating PaperDeck's test suite from PNG to PDF file output. Based on analysis of current test architecture and industry best practices, we recommend a hybrid approach combining mocks for unit tests with real files for integration tests, parametrized test cases for file naming conventions, and structured error handling tests for graceful degradation.

---

## 1. Test Migration Strategy

### 1.1 Overview of Current Architecture

PaperDeck's current testing structure:
- **Unit tests**: `tests/unit/extraction/test_docscalpel_adapter.py` (mocked DocScalpel)
- **Integration tests**: `tests/integration/test_figure_extraction.py` (real workflows)
- **LaTeX generation tests**: `tests/unit/generation/test_figure_latex.py` (PNG paths hardcoded)
- **Fixture structure**: `tests/fixtures/malformed_latex/` with LaTeX test cases

### 1.2 Migration Approach: Parametrization Strategy

Use pytest parametrization to handle file format differences systematically:

```python
import pytest
from pathlib import Path

# Define format parameters
FORMATS = ["png", "pdf"]
FORMAT_PARAMS = [
    pytest.param(
        format_type,
        id=f"format-{format_type}"
    )
    for format_type in FORMATS
]

class TestElementProcessorFormats:
    """Test element processor with multiple output formats."""

    @pytest.mark.parametrize("format_type", FORMAT_PARAMS)
    def test_save_figure_with_format(self, format_type, tmp_path):
        """Test figure saving with different formats."""
        processor = ElementProcessor(tmp_path)
        figure_data = b"fake image data"

        result_path = processor.save_figure(figure_data, 1, format=format_type)

        assert result_path.suffix == f".{format_type}"
        assert result_path.name == f"figure_1.{format_type}"
        assert result_path.exists()
```

### 1.3 Update Strategy by Test Layer

#### **Unit Tests**: Mock-Focused (minimal file I/O)
- Mock DocScalpel output with PDF paths
- Mock `ElementProcessor.save_figure()` to return PDF paths
- Test naming convention logic separately

**File**: `tests/unit/extraction/test_docscalpel_adapter.py`

```python
def test_extract_returns_pdf_paths_when_docscalpel_available(self, mocker, tmp_path):
    """Test extract returns elements with PDF output filenames."""
    adapter = DocScalpelAdapter()
    adapter.docscalpel_available = True

    # Mock DocScalpel output with PDF paths
    mock_element = MagicMock()
    mock_element.output_filename = "figure_01.pdf"  # Zero-padded PDF

    mocker.patch.object(
        adapter.docscalpel,
        'extract_elements',
        return_value=MagicMock(
            success=True,
            elements=[mock_element],
            figure_count=1,
            table_count=0,
            errors=[],
            warnings=[]
        )
    )

    result = adapter.extract(tmp_path / "test.pdf", [ElementType.FIGURE])

    assert len(result) == 1
    assert result[0].output_filename == Path("figure_01.pdf")
```

#### **Integration Tests**: Real Files (complete workflows)
- Create temporary PDF files for testing
- Test full extraction → processing → LaTeX generation pipeline
- Verify LaTeX compilation with PDF references

**File**: `tests/integration/test_figure_extraction.py`

```python
def test_full_pipeline_with_pdf_output(self, tmp_path):
    """Test complete extraction, processing, and LaTeX generation with PDFs."""
    # Create fake PDF input
    pdf_input = tmp_path / "paper.pdf"
    pdf_input.write_bytes(b"fake pdf content")

    output_dir = tmp_path / "extracted"

    # Setup components
    adapter = DocScalpelAdapter()
    processor = ElementProcessor(output_dir)

    # Simulate PDF extraction (mock DocScalpel)
    adapter.docscalpel_available = False  # Graceful fallback
    elements = adapter.extract(pdf_input, [ElementType.FIGURE])

    # For real test, manually create PDF output files
    pdf_data = create_minimal_pdf()  # Helper function
    pdf_path = processor.save_figure(pdf_data, 1, format="pdf")

    assert pdf_path.suffix == ".pdf"
    assert pdf_path.exists()
```

#### **LaTeX Generation Tests**: Format-Agnostic
- Test that LaTeX paths work with both PNG and PDF
- Verify `includegraphics` paths are correct regardless of format

**File**: `tests/unit/generation/test_figure_latex.py`

```python
@pytest.mark.parametrize("format_type,extension", [
    ("png", ".png"),
    ("pdf", ".pdf"),
])
def test_generate_figure_latex_with_formats(self, format_type, extension):
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
```

---

## 2. Mock vs Real File Approach

### 2.1 Decision Matrix

| Scenario | Use Mocks | Use Real Files | Rationale |
|----------|-----------|----------------|-----------|
| Unit test: Adapter initialization | ✓ | | Isolate import logic |
| Unit test: Path formatting | ✓ | | Test logic, not I/O |
| Integration test: Full extraction | | ✓ | Need real PDF files in workflow |
| Integration test: Error handling | ✓ or ✓ | | Test exception paths |
| LaTeX generation | ✓ | | Test string generation, not file I/O |
| End-to-end with compilation | | ✓ | Verify complete pipeline |

### 2.2 Hybrid Strategy

**For Unit Tests** (test_docscalpel_adapter.py):
```python
# Use mocks for external dependencies
@pytest.fixture
def mock_docscalpel(mocker):
    """Mock the DocScalpel library."""
    return mocker.MagicMock()

def test_extract_with_mock(mocker, tmp_path, mock_docscalpel):
    """Unit test with mocked DocScalpel."""
    adapter = DocScalpelAdapter()
    adapter.docscalpel_available = True
    adapter.docscalpel = mock_docscalpel

    # Mock return value with PDF paths
    mocker.patch.object(
        mock_docscalpel,
        'extract_elements',
        return_value=MagicMock(
            success=True,
            elements=[],
            figure_count=0,
            table_count=0
        )
    )

    result = adapter.extract(tmp_path / "test.pdf")
    assert isinstance(result, list)
```

**For Integration Tests** (test_figure_extraction.py):
```python
# Use real temporary files
@pytest.fixture
def sample_pdf_bytes():
    """Create minimal valid PDF bytes for testing."""
    # Minimal PDF that's valid but empty
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
203
%%EOF
"""

def test_element_processor_saves_pdf(tmp_path, sample_pdf_bytes):
    """Integration test with real PDF files."""
    processor = ElementProcessor(tmp_path)

    pdf_path = processor.save_figure(sample_pdf_bytes, 1, format="pdf")

    assert pdf_path.suffix == ".pdf"
    assert pdf_path.read_bytes() == sample_pdf_bytes
```

### 2.3 Benefits of Hybrid Approach

| Benefit | Unit Tests | Integration Tests |
|---------|-----------|-------------------|
| Speed | Fast (no I/O) | Slower but comprehensive |
| Isolation | High (mocked dependencies) | Lower (real interactions) |
| Maintainability | Easy (simple mocks) | Requires real PDFs |
| Coverage | Logic coverage | End-to-end validation |
| Reliability | Deterministic | Depends on PDF generation |

---

## 3. Specific Test Cases to Add/Modify

### 3.1 File Naming Convention Tests

Create dedicated test class for naming conventions:

```python
class TestFilenameNaming:
    """Test file naming with different padding and formats."""

    @pytest.mark.parametrize("sequence_number,expected_name", [
        (1, "figure_01.pdf"),      # Zero-padded
        (9, "figure_09.pdf"),      # Zero-padded
        (10, "figure_10.pdf"),     # Two digits (no padding needed)
        (99, "figure_99.pdf"),
        (100, "figure_100.pdf"),   # Three digits
    ])
    def test_figure_naming_with_padding(self, sequence_number, expected_name, tmp_path):
        """Test zero-padded figure numbering."""
        processor = ElementProcessor(tmp_path)
        figure_data = b"test"

        # Note: Current implementation uses f"{number}.pdf"
        # This test may require updating ElementProcessor
        result_path = processor.save_figure(figure_data, sequence_number, format="pdf")

        assert result_path.name == expected_name

    @pytest.mark.parametrize("element_type,format_type", [
        ("figure", "pdf"),
        ("figure", "png"),
        ("table", "pdf"),
        ("table", "png"),
    ])
    def test_element_filenames_by_type_and_format(self, element_type, format_type, tmp_path):
        """Test filename generation respects element type and format."""
        processor = ElementProcessor(tmp_path)
        test_data = b"test content"

        if element_type == "figure":
            result_path = processor.save_figure(test_data, 1, format=format_type)
        else:
            result_path = processor.save_table(test_data, 1, format=format_type)

        assert result_path.stem == f"{element_type}_1"
        assert result_path.suffix == f".{format_type}"
```

### 3.2 LaTeX Path Tests with PDF

```python
class TestLatexPathsWithPdf:
    """Test LaTeX \includegraphics paths with PDF files."""

    @pytest.mark.parametrize("file_extension", [".pdf", ".png", ".jpg"])
    def test_latex_path_formatting_preserves_extension(self, file_extension):
        """Test that LaTeX paths preserve file extensions."""
        path = Path(f"extracted/figure_01{file_extension}")
        formatted = LaTeXGenerator._format_graphics_path(path)

        assert f"figure_01{file_extension}" in formatted
        assert "\\" not in formatted  # No Windows backslashes
        assert "/" in formatted or "figure" in formatted

    def test_pdf_figures_generate_valid_latex(self):
        """Test PDF figures generate valid LaTeX code."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path("extracted/figure_01.pdf"),
            caption="Test PDF Figure",
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        # Verify LaTeX is valid
        assert "\\begin{figure}" in latex
        assert "\\includegraphics[width" in latex
        assert "figure_01.pdf" in latex
        assert "\\caption{Test PDF Figure}" in latex
        assert "\\end{figure}" in latex

        # PDFs should work fine with \includegraphics
        assert "figure_01.pdf" in latex
```

### 3.3 Error Handling for Malformed PDFs

```python
class TestMalformedPdfHandling:
    """Test graceful handling of corrupted or invalid PDFs."""

    def test_element_processor_handles_empty_pdf_data(self, tmp_path):
        """Test processor handles empty PDF data gracefully."""
        processor = ElementProcessor(tmp_path)

        with pytest.raises(ValueError, match="Figure .* has no image data"):
            processor.save_figure(b"", 1, format="pdf")

    def test_element_processor_handles_invalid_pdf_bytes(self, tmp_path):
        """Test processor handles truly invalid PDF bytes."""
        processor = ElementProcessor(tmp_path)
        invalid_data = b"not a pdf at all"

        # Processor just writes bytes, doesn't validate
        # But test that it at least creates the file
        result_path = processor.save_figure(invalid_data, 1, format="pdf")

        assert result_path.exists()
        assert result_path.suffix == ".pdf"

    def test_adapter_handles_extraction_failure_gracefully(self, tmp_path, mocker):
        """Test adapter gracefully handles DocScalpel extraction errors."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        # Mock extraction failure
        mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            side_effect=RuntimeError("PDF parsing failed")
        )

        result = adapter.extract(tmp_path / "corrupted.pdf")

        # Should return empty list, not raise
        assert result == []
```

---

## 4. Edge Case Testing Recommendations

### 4.1 Zero-Padded Numbering Edge Cases

```python
class TestZeroPaddingEdgeCases:
    """Test edge cases for zero-padded figure numbering."""

    @pytest.mark.parametrize("num_figures", [1, 9, 10, 99, 100, 999, 1000])
    def test_padding_adjusts_to_document_size(self, num_figures, tmp_path):
        """Test that padding width matches document figure count."""
        processor = ElementProcessor(tmp_path)

        # Save figures up to num_figures
        for i in range(1, num_figures + 1):
            path = processor.save_figure(b"data", i, format="pdf")
            # Extract padding width from filename pattern
            # This test may require custom naming logic
            assert path.suffix == ".pdf"

    def test_mixed_padding_in_same_document(self, tmp_path):
        """Test document with both single-digit and multi-digit figure numbers."""
        processor = ElementProcessor(tmp_path)

        # Create 15 figures (spanning single to double digits)
        paths = [processor.save_figure(b"data", i, format="pdf") for i in range(1, 16)]

        # Verify all have consistent extensions
        assert all(p.suffix == ".pdf" for p in paths)
```

### 4.2 File System Interaction Edge Cases

```python
class TestFileSystemEdgeCases:
    """Test edge cases in file system operations."""

    def test_save_to_nonexistent_parent_directory(self, tmp_path):
        """Test processor creates nested directories."""
        nested_dir = tmp_path / "a" / "b" / "c" / "extracted"
        processor = ElementProcessor(nested_dir)

        path = processor.save_figure(b"data", 1, format="pdf")

        assert path.parent == nested_dir
        assert path.exists()

    def test_overwrite_existing_pdf(self, tmp_path):
        """Test that saving with same name overwrites existing file."""
        processor = ElementProcessor(tmp_path)

        # Save first version
        data1 = b"first version"
        path1 = processor.save_figure(data1, 1, format="pdf")

        # Save second version with same number
        data2 = b"second version"
        path2 = processor.save_figure(data2, 1, format="pdf")

        # Should be same path, with new data
        assert path1 == path2
        assert path2.read_bytes() == data2

    def test_special_characters_in_caption(self, tmp_path):
        """Test LaTeX generation with special chars in captions."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=Path("figure_01.pdf"),
            caption="Results: $100 & 10% improvement (R&D)",  # Contains special chars
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        # Special chars should be escaped
        assert "\\$" in latex or "$" not in latex.split("caption")[1].split("}")[0]
        assert "\\&" in latex or "&" not in latex.split("caption")[1].split("}")[0]
```

### 4.3 Format-Specific Edge Cases

```python
class TestFormatSpecificEdgeCases:
    """Test edge cases specific to PDF vs PNG formats."""

    def test_pdf_with_multiple_pages_reference(self, tmp_path):
        """Test that multi-page PDFs are handled correctly."""
        # Create a mock multi-page PDF
        multipage_pdf = create_multipage_pdf(3)  # 3 pages
        processor = ElementProcessor(tmp_path)

        path = processor.save_figure(multipage_pdf, 1, format="pdf")

        assert path.exists()
        # LaTeX includegraphics doesn't specify pages by default
        # (would need pdfpages package for page selection)

    @pytest.mark.parametrize("format_type,file_size_kb", [
        ("png", 50),   # PNG might be larger
        ("pdf", 100),  # PDF might be larger for complex content
    ])
    def test_large_figure_handling(self, format_type, file_size_kb, tmp_path):
        """Test handling of large figure files."""
        processor = ElementProcessor(tmp_path)

        # Create large "figure" data
        large_data = b"x" * (file_size_kb * 1024)

        path = processor.save_figure(large_data, 1, format=format_type)

        assert path.exists()
        assert len(path.read_bytes()) == len(large_data)
```

---

## 5. Testing Graceful Degradation

### 5.1 Adapter Fallback Testing

```python
class TestDocScalpelAdapterGracefulDegradation:
    """Test graceful fallback when DocScalpel fails or is unavailable."""

    def test_extraction_when_docscalpel_not_installed(self, tmp_path):
        """Test extraction gracefully returns empty when DocScalpel unavailable."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(tmp_path / "test.pdf", [ElementType.FIGURE])

        assert result == []
        assert isinstance(result, list)  # Not None, not error

    def test_extraction_continues_with_partial_failures(self, tmp_path, mocker):
        """Test extraction continues when some elements fail but others succeed."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        # Mock mixed success/failure scenario
        mock_result = MagicMock()
        mock_result.success = False  # Some failures
        mock_result.errors = ["Page 3 unreadable"]
        mock_result.warnings = ["Low confidence on figure 2"]
        mock_result.elements = [MagicMock(output_filename="figure_01.pdf")]
        mock_result.figure_count = 1
        mock_result.table_count = 0

        mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            return_value=mock_result
        )

        result = adapter.extract(tmp_path / "test.pdf")

        # Should still return successfully extracted elements
        assert len(result) >= 0  # Depending on conversion logic

    def test_processing_continues_when_file_write_fails(self, tmp_path, mocker):
        """Test ElementProcessor handles write failures gracefully."""
        processor = ElementProcessor(tmp_path)

        # Mock write failure
        mocker.patch.object(Path, 'write_bytes', side_effect=IOError("Disk full"))

        with pytest.raises(ExtractionError):
            processor.save_figure(b"data", 1, format="pdf")

    def test_latex_generation_with_missing_pdf_files(self):
        """Test LaTeX generation when referenced PDF files don't exist."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=Path("extracted/figure_01.pdf"),  # File doesn't exist
            caption="Test Figure",
        )

        # LaTeX generator should still produce valid LaTeX
        # (pdflatex will handle missing files at compile time)
        latex = LaTeXGenerator.generate_figure_latex(figure)

        assert "\\includegraphics" in latex
        assert "figure_01.pdf" in latex
```

### 5.2 Configuration-Based Fallback Testing

```python
class TestExtractionConfigurationFallbacks:
    """Test fallback behavior with different configurations."""

    def test_disabled_figure_extraction_config(self, tmp_path, mocker):
        """Test that disabled feature in config is respected."""
        config = ExtractionConfiguration(
            extract_figures=False,
            extract_tables=True,
        )
        adapter = DocScalpelAdapter(config)
        adapter.docscalpel_available = True

        # Mock to verify correct element types requested
        mock_result = MagicMock(
            success=True,
            elements=[],
            figure_count=0,
            table_count=0
        )
        mock_extract = mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            return_value=mock_result
        )

        adapter.extract(tmp_path / "test.pdf")

        # Verify figures were filtered out
        call_config = mock_extract.call_args[0][1]
        # Assertions depend on how config is passed to docscalpel

    def test_confidence_threshold_filtering(self, tmp_path, mocker):
        """Test that low-confidence elements can be filtered."""
        config = ExtractionConfiguration(confidence_threshold=0.8)
        adapter = DocScalpelAdapter(config)
        adapter.docscalpel_available = True

        # Verify confidence_threshold is used
        # (depends on implementation details)
```

---

## 6. PDF Compilation and Validation Testing

### 6.1 LaTeX Compilation Verification

```python
class TestPdfCompilationValidation:
    """Test that generated LaTeX compiles correctly with PDF figures."""

    @pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
    def test_generated_latex_with_pdf_figures_compiles(self, tmp_path):
        """Test that LaTeX with PDF figures compiles successfully."""
        # Create a test PDF figure
        pdf_data = create_minimal_pdf()
        figure_path = tmp_path / "extracted" / "figure_01.pdf"
        figure_path.parent.mkdir(parents=True)
        figure_path.write_bytes(pdf_data)

        # Create figure element pointing to PDF
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=figure_path,
            caption="Test PDF Figure",
        )

        # Generate LaTeX
        latex = LaTeXGenerator.generate_figure_latex(figure, output_dir=tmp_path)

        # Create minimal document
        doc = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\begin{{document}}
{latex}
\\end{{document}}
"""

        # Write and compile
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(doc)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_file)],
            capture_output=True,
            timeout=10
        )

        # Verify compilation succeeded
        assert result.returncode == 0, f"pdflatex failed: {result.stderr.decode()}"
        assert (tmp_path / "test.pdf").exists()

    @pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
    @pytest.mark.parametrize("num_figures", [1, 3, 5])
    def test_multi_figure_document_compilation(self, num_figures, tmp_path):
        """Test document with multiple PDF figures compiles."""
        # Create test PDF figures
        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()

        figures = []
        for i in range(1, num_figures + 1):
            pdf_data = create_minimal_pdf()
            pdf_path = extracted_dir / f"figure_{i:02d}.pdf"
            pdf_path.write_bytes(pdf_data)

            figure = FigureElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
                confidence_score=0.9,
                sequence_number=i,
                output_filename=pdf_path,
                caption=f"Figure {i}",
            )
            figures.append(figure)

        # Generate LaTeX for all figures
        figure_latex = "\n".join(
            LaTeXGenerator.generate_figure_latex(fig, output_dir=tmp_path)
            for fig in figures
        )

        # Create document
        doc = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\begin{{document}}
{figure_latex}
\\end{{document}}
"""

        # Compile
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(doc)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_file)],
            capture_output=True,
            timeout=15
        )

        assert result.returncode == 0
        assert (tmp_path / "test.pdf").exists()
```

### 6.2 PDF Properties Validation

```python
class TestPdfPropertiesValidation:
    """Test validation of PDF properties in compiled documents."""

    @pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
    def test_compiled_pdf_has_correct_page_count(self, tmp_path):
        """Test that compiled PDF has expected number of pages."""
        pdf_data = create_minimal_pdf()
        figure_path = tmp_path / "extracted" / "figure_01.pdf"
        figure_path.parent.mkdir(parents=True)
        figure_path.write_bytes(pdf_data)

        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=figure_path,
            caption="Test",
        )

        latex = LaTeXGenerator.generate_figure_latex(figure, output_dir=tmp_path)

        doc = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\begin{{document}}
{latex}
\\end{{document}}
"""

        tex_file = tmp_path / "test.tex"
        tex_file.write_text(doc)

        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_file)],
            capture_output=True,
            timeout=10
        )

        # Use PyMuPDF to validate PDF properties
        try:
            import fitz
            pdf_file = tmp_path / "test.pdf"
            doc = fitz.open(pdf_file)

            # Verify at least 1 page
            assert len(doc) >= 1

            # Verify page dimensions are reasonable (letter size)
            page = doc[0]
            rect = page.rect
            assert 500 < rect.width < 700  # Reasonable width
            assert 500 < rect.height < 1000  # Reasonable height
        except ImportError:
            pytest.skip("PyMuPDF not available for PDF validation")
```

### 6.3 LaTeX Error Detection

```python
class TestLatexErrorDetection:
    """Test detection of LaTeX errors related to PDF figures."""

    @pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
    def test_missing_pdf_figure_detected_by_pdflatex(self, tmp_path):
        """Test that missing PDF file is caught by pdflatex."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            confidence_score=0.9,
            sequence_number=1,
            output_filename=Path("extracted/figure_01.pdf"),  # File doesn't exist
            caption="Test",
        )

        latex = LaTeXGenerator.generate_figure_latex(figure, output_dir=tmp_path)

        doc = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\begin{{document}}
{latex}
\\end{{document}}
"""

        tex_file = tmp_path / "test.tex"
        tex_file.write_text(doc)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_file)],
            capture_output=True,
            timeout=10
        )

        # pdflatex should report error but still produce PDF
        output = result.stderr.decode() + result.stdout.decode()
        assert "figure_01.pdf" in output or "Cannot find" in output or "not found" in output
```

---

## 7. Summary: Test Migration Checklist

### Before Migration
- [ ] Document current PNG test expectations
- [ ] Identify all files referencing `.png` extension
- [ ] Create backup of existing tests
- [ ] Plan parametrization strategy

### Unit Test Updates (test_docscalpel_adapter.py)
- [ ] Update mock returns to use `.pdf` extension
- [ ] Add format parameter to mock configurations
- [ ] Test configuration flags with PDF output
- [ ] Verify error paths still work

### Integration Test Updates (test_figure_extraction.py)
- [ ] Create helper function for minimal PDF generation
- [ ] Update fixture paths from PNG to PDF
- [ ] Add parametrized tests for both formats during transition
- [ ] Test complete workflows with real PDF files

### LaTeX Generation Tests (test_figure_latex.py)
- [ ] Make tests format-agnostic (use parametrization)
- [ ] Test zero-padded numbering with PDF
- [ ] Verify special character escaping works
- [ ] Add PDF compilation tests (if pdflatex available)

### New Test Classes to Add
- [ ] TestFilenameNaming - Zero-padded numbering edge cases
- [ ] TestFileSystemEdgeCases - Directory creation, overwrites
- [ ] TestMalformedPdfHandling - Corruption and error cases
- [ ] TestDocScalpelAdapterGracefulDegradation - Fallback paths
- [ ] TestPdfCompilationValidation - End-to-end LaTeX compilation

### Fixtures to Create
- [ ] sample_pdf_bytes - Minimal valid PDF
- [ ] multipage_pdf - Multi-page PDF for edge cases
- [ ] create_minimal_pdf() - Helper function
- [ ] malformed_pdf_bytes - Invalid PDF for error testing

### Configuration
- [ ] Update pytest markers if needed
- [ ] Consider adding @pytest.mark.slow for compilation tests
- [ ] Document any new test dependencies (PyMuPDF, etc.)

---

## 8. References and Resources

### Testing Best Practices
- [Pytest Common Mocking Problems & Best Practices](https://pytest-with-eric.com/mocking/pytest-common-mocking-problems/)
- [Good Integration Practices - pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [pytest-mock · PyPI](https://pypi.org/project/pytest-mock/)
- [End-to-End Python Integration Testing: A Complete Guide](https://www.lambdatest.com/learning-hub/python-integration-testing)

### Pytest Parametrization
- [Parametrizing tests — pytest documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [Mastering Default Naming Conventions in pytest](https://www.qabash.com/pytest-default-naming-conventions-guide/)
- [Deep dive into Pytest parametrization](https://medium.com/opsops/deepdive-into-pytest-parametrization-cb21665c05b9)

### Error Handling & Graceful Degradation
- [How To Test Python Exception Handling Using Pytest Assert](https://pytest-with-eric.com/introduction/pytest-assert-exception/)
- [Handling Exceptions in Pytest: Strategies for Error Testing](https://medium.com/@venu_5446/handling-exceptions-in-pytest-strategies-for-error-testing-28ae4c9522dc)
- [Flaky Tests: Turning your Python tests from flaky to robust](https://pratikshasalimath.medium.com/flaky-tests-turning-your-python-tests-from-flaky-to-robust-794fef723a08/)
- [AWS Reliability Pillar: Graceful Degradation](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)

### LaTeX Testing
- [How to beat publisher PDF checks with LaTeX document unit testing](https://blog.martisak.se/2020/05/16/latex-test-cases/)
- [Visual Validation of PDF Files - Test Automation University](https://testautomationu.applitools.com/visual-testing-python/chapter9.html)
- [Overleaf LaTeX Validation Service](https://www.overleaf.com/blog/574-new-from-overleaf-the-latex-validation-service)

---

## 9. Implementation Timeline

1. **Phase 1**: Update unit tests with parametrization (1-2 days)
   - Add format parameter to tests
   - Update mocks to return PDF paths
   - Maintain backward compatibility during transition

2. **Phase 2**: Create integration tests with real PDFs (2-3 days)
   - Implement PDF helper functions
   - Create integration test fixtures
   - Add edge case tests

3. **Phase 3**: Add graceful degradation tests (1 day)
   - Test error paths
   - Verify fallback mechanisms
   - Document error handling

4. **Phase 4**: Add LaTeX compilation tests (optional, 1-2 days)
   - Set up conditional tests (skip if pdflatex unavailable)
   - Test PDF figure compilation
   - Validate output

5. **Phase 5**: Documentation and cleanup (1 day)
   - Update test documentation
   - Add comments for complex test logic
   - Create migration guide
