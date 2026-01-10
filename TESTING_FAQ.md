# Testing Strategy FAQ: PNG → PDF Migration

## Common Questions and Answers

---

## Q1: Should I use real PDF files or mocks in tests?

**A:** Use both strategically:

**Use Real PDF Files for:**
- Integration tests (full workflow from extraction to LaTeX)
- End-to-end testing where components interact
- Tests that validate file I/O operations
- Testing error handling with actual file corruption

**Use Mocks for:**
- Unit tests that test single components in isolation
- Testing logic without side effects (like path formatting)
- When testing external dependencies (DocScalpel library)
- When speed is critical (quick feedback loops)

**Example:**
```python
# Unit test - MOCK
def test_adapter_configures_docscalpel(mocker, tmp_path):
    adapter = DocScalpelAdapter()
    mock_docscalpel = mocker.MagicMock()
    adapter.docscalpel = mock_docscalpel
    # Test configuration logic, not actual extraction

# Integration test - REAL
def test_full_extraction_workflow(tmp_path, sample_pdf_bytes):
    processor = ElementProcessor(tmp_path)
    result = processor.save_figure(sample_pdf_bytes, 1, format="pdf")
    # Test actual file creation and handling
```

---

## Q2: How do I handle zero-padded numbering like figure_01.pdf vs figure_1.pdf?

**A:** The current implementation doesn't use zero-padding. Here are three options:

**Option 1: Keep current behavior (no padding)**
```python
# figure_1.pdf, figure_2.pdf, ..., figure_10.pdf
filename = f"figure_{sequence_number}.pdf"
```

**Option 2: Use fixed-width padding**
```python
# figure_001.pdf, figure_002.pdf, ..., figure_999.pdf
filename = f"figure_{sequence_number:03d}.pdf"
```

**Option 3: Dynamic padding (adaptive)**
```python
# Requires knowing total figure count
# figure_01.pdf if <= 99 figures, figure_001.pdf if > 99 figures
def get_filename(sequence_number, total_figures):
    padding = len(str(total_figures))
    return f"figure_{sequence_number:0{padding}d}.pdf"
```

**Recommendation**: Use Option 1 (current, no padding) to avoid breaking changes. If you need padding, implement Option 3 at the document level.

---

## Q3: What's the difference between test_docscalpel_adapter.py and test_figure_extraction.py?

**A:** Different testing layers:

| File | Focus | Setup | Uses Mocks | Tests What |
|------|-------|-------|-----------|-----------|
| `test_docscalpel_adapter.py` | **Unit tests** | Isolated components | Mocked DocScalpel | Adapter logic, error handling |
| `test_figure_extraction.py` | **Integration tests** | Full workflows | Real temp files | Component interactions |

**test_docscalpel_adapter.py (Unit):**
```python
# Tests the adapter in isolation
def test_extract_filters_by_element_type(self, mocker):
    adapter = DocScalpelAdapter()
    adapter.docscalpel = mocker.MagicMock()
    # Test that adapter correctly filters FIGURE vs TABLE types
```

**test_figure_extraction.py (Integration):**
```python
# Tests the full extraction workflow
def test_full_pipeline(self, tmp_path, sample_pdf_bytes):
    adapter = DocScalpelAdapter()
    processor = ElementProcessor(tmp_path)
    # Test that extraction → processing → LaTeX generation works together
```

---

## Q4: How do I test graceful degradation when DocScalpel fails?

**A:** Test multiple failure scenarios:

```python
class TestGracefulDegradation:
    """Test that system continues working even when DocScalpel fails."""

    def test_missing_docscalpel_library(self, tmp_path):
        """DocScalpel not installed."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(tmp_path / "test.pdf")

        assert result == []  # Returns empty, not error

    def test_corrupted_pdf_file(self, tmp_path, mocker):
        """PDF file is corrupted/unreadable."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            side_effect=RuntimeError("PDF parsing failed")
        )

        result = adapter.extract(tmp_path / "corrupted.pdf")

        assert result == []  # Graceful fallback

    def test_partial_extraction_failure(self, tmp_path, mocker):
        """Some figures extracted, others fail."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True

        # Mock: success=False but still returned 1 figure
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ["Page 3 corrupted"]
        mock_result.elements = [MagicMock()]  # Still got 1 element

        mocker.patch.object(
            adapter.docscalpel,
            'extract_elements',
            return_value=mock_result
        )

        result = adapter.extract(tmp_path / "test.pdf")

        # Should return what was successfully extracted
        assert isinstance(result, list)

    def test_write_failure_during_processing(self, tmp_path, mocker):
        """Disk full or permission error during file write."""
        processor = ElementProcessor(tmp_path)

        mocker.patch.object(
            Path,
            'write_bytes',
            side_effect=IOError("Disk full")
        )

        with pytest.raises(ExtractionError):
            processor.save_figure(b"data", 1, format="pdf")
```

---

## Q5: How do I test that LaTeX actually compiles with PDF figures?

**A:** Use subprocess to call pdflatex:

```python
import subprocess
import shutil

@pytest.mark.skipif(
    not shutil.which("pdflatex"),
    reason="pdflatex not installed"
)
def test_pdf_figures_compile_with_latex(tmp_path, sample_pdf_bytes):
    """Test that generated LaTeX actually compiles with pdflatex."""

    # Create test PDF figure
    figure_dir = tmp_path / "extracted"
    figure_dir.mkdir()
    figure_path = figure_dir / "figure_01.pdf"
    figure_path.write_bytes(sample_pdf_bytes)

    # Create figure element
    figure = FigureElement(
        uuid=uuid4(),
        element_type=ElementType.FIGURE,
        page_number=1,
        bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
        confidence_score=0.9,
        sequence_number=1,
        output_filename=figure_path,
        caption="Test Figure",
    )

    # Generate LaTeX
    latex = LaTeXGenerator.generate_figure_latex(figure, output_dir=tmp_path)

    # Create minimal LaTeX document
    document = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\begin{{document}}
{latex}
\\end{{document}}
"""

    # Write LaTeX file
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(document)

    # Compile with pdflatex
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode",
         "-output-directory", str(tmp_path), str(tex_file)],
        capture_output=True,
        timeout=10
    )

    # Verify compilation succeeded
    assert result.returncode == 0, f"pdflatex failed: {result.stderr.decode()}"
    assert (tmp_path / "test.pdf").exists()
```

**Tips:**
- Use `@pytest.mark.skipif` to skip if pdflatex not installed
- Capture output for debugging when compilation fails
- Set a reasonable timeout (pdflatex can hang)
- Test with both single and multiple figures

---

## Q6: How do I organize test data and fixtures?

**A:** Use a clear directory structure:

```
tests/
├── conftest.py                    # Shared fixtures
├── helpers/
│   ├── __init__.py
│   └── pdf_helpers.py            # PDF creation helpers
├── fixtures/
│   ├── sample_papers/            # Existing
│   ├── malformed_latex/          # Existing
│   ├── pdfs/                     # NEW: Add sample PDFs
│   │   ├── minimal.pdf           # Minimal valid PDF
│   │   ├── multipage.pdf         # Multi-page PDF
│   │   └── corrupted.pdf         # Intentionally bad
│   └── README.md                 # Document fixtures
├── unit/
│   ├── extraction/
│   │   ├── test_docscalpel_adapter.py
│   │   └── test_pdf_naming_conventions.py  # NEW
│   └── generation/
│       └── test_figure_latex.py
└── integration/
    └── test_figure_extraction.py
```

**In conftest.py:**
```python
@pytest.fixture
def pdf_file(tmp_path):
    """Temporary PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(create_minimal_pdf())
    return pdf_path

@pytest.fixture
def sample_pdf_bytes():
    """Minimal PDF bytes without file I/O."""
    return create_minimal_pdf()
```

---

## Q7: What should I test for file format changes?

**A:** Create a comprehensive test matrix:

```python
@pytest.mark.parametrize("file_format,expected_extension", [
    ("png", ".png"),
    ("pdf", ".pdf"),
    ("jpg", ".jpg"),
])
def test_all_supported_formats(file_format, expected_extension, tmp_path, sample_bytes):
    """Test that all formats are handled correctly."""
    processor = ElementProcessor(tmp_path)

    result_path = processor.save_figure(sample_bytes, 1, format=file_format)

    assert result_path.suffix == expected_extension
    assert result_path.exists()
```

**Coverage checklist:**
- [ ] Different file formats (PNG, PDF, JPG)
- [ ] Different file sizes (small, medium, large)
- [ ] Empty data (error handling)
- [ ] Corrupted data (robustness)
- [ ] Special characters in filenames/captions
- [ ] Directory creation and nesting
- [ ] File overwrites
- [ ] LaTeX path formatting

---

## Q8: How do I test error messages and logging?

**A:** Use pytest fixtures for capturing output:

```python
def test_adapter_logs_missing_docscalpel(caplog):
    """Test that adapter logs when DocScalpel not available."""
    with caplog.at_level(logging.WARNING):
        adapter = DocScalpelAdapter()

    assert "DocScalpel not installed" in caplog.text

def test_processor_logs_file_write(caplog):
    """Test that processor logs successful write."""
    with caplog.at_level(logging.INFO):
        processor = ElementProcessor(tmp_path)
        processor.save_figure(b"data", 1, format="pdf")

    assert "Saved figure" in caplog.text
    assert "figure_1.pdf" in caplog.text
```

---

## Q9: Should I remove old PNG tests?

**A:** Depends on your transition plan:

**Option 1: Gradual Transition (Recommended)**
1. Add PDF tests alongside PNG tests
2. Mark PNG tests as "deprecated" with comments
3. Update CI to run both
4. After PDF is stable, remove PNG tests
5. Timeline: 1-2 sprints

**Option 2: Clean Break**
1. Replace all PNG tests immediately
2. Update implementation to PDF-only
3. Risk: May break downstream code
4. Timeline: 1 sprint

**Option 3: Support Both Formats**
1. Keep both PNG and PDF tests
2. Make format configurable
3. Test both in parametrized tests
4. Most maintainable but more complex

**Recommendation:** Use Option 1 for safety.

```python
# Mark as deprecated but keep functional during transition
@pytest.mark.skip(reason="PNG deprecated, use PDF tests instead")
def test_png_support_legacy():
    """Legacy: PNG support - migrating to PDF."""
    pass
```

---

## Q10: How do I ensure test data is minimal and maintainable?

**A:** Generate test data programmatically:

```python
# DON'T: Store large binary files in git
# Large PDF files in tests/fixtures/pdfs/

# DO: Generate minimal PDF bytes at test time
def create_minimal_pdf():
    """Generate minimal valid PDF without external files."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
...
"""

# Use in fixture
@pytest.fixture
def sample_pdf_bytes():
    return create_minimal_pdf()
```

**Benefits:**
- No large binary files in git
- Tests are deterministic and reproducible
- Easy to create variations (corrupted, multi-page, etc.)
- Faster test execution
- Clear visibility into test data structure

---

## Q11: What's the recommended test execution order?

**A:** Run tests in this order for efficient feedback:

```bash
# 1. Fast unit tests first (instant feedback)
pytest tests/unit/ -v

# 2. Parametrized format tests (comprehensive coverage)
pytest tests/unit/ -k "parametrize" -v

# 3. Integration tests (slower)
pytest tests/integration/ -v

# 4. LaTeX compilation tests (slowest, optional)
pytest tests/ -m "latex_compile" -v

# 5. Full suite with coverage
pytest tests/ --cov=src/paperdeck --cov-report=html

# In CI/CD, run all in parallel:
pytest tests/ -n auto  # Uses pytest-xdist for parallelization
```

---

## Q12: How do I debug failing tests?

**A:** Use pytest's debugging tools:

```bash
# Show print statements
pytest tests/test_example.py -s

# Drop into debugger on failure
pytest tests/test_example.py -x --pdb

# Show local variables on failure
pytest tests/test_example.py -l

# Run single test
pytest tests/test_example.py::TestClass::test_method -v

# Run tests matching pattern
pytest tests/ -k "pdf" -v

# Show test execution order
pytest tests/ --collect-only -q
```

**In code:**
```python
def test_something():
    import pdb; pdb.set_trace()  # Debugger breakpoint
    result = some_function()
    assert result == expected
```

---

## Q13: How do I handle test dependencies and ordering?

**A:** Avoid test dependencies! Tests should be independent:

**DON'T:**
```python
class TestSequentialDependency:
    def test_1_create_file(self):
        # Creates figure_1.pdf
        ...

    def test_2_read_file(self):
        # Depends on test_1 creating the file
        # FRAGILE: Fails if run in isolation
        ...
```

**DO:**
```python
class TestIndependentTests:
    def test_create_file(self, tmp_path):
        # Each test gets its own tmp_path
        processor = ElementProcessor(tmp_path)
        processor.save_figure(b"data", 1, format="pdf")
        assert (tmp_path / "figure_1.pdf").exists()

    def test_read_file(self, tmp_path):
        # Independent setup
        processor = ElementProcessor(tmp_path)
        processor.save_figure(b"data", 1, format="pdf")
        assert (tmp_path / "figure_1.pdf").read_bytes() == b"data"
```

**Use Fixtures:**
- Each fixture gets a fresh state
- tmp_path automatically cleaned up
- Tests can run in any order

---

## Q14: What PDF library should I use for validation?

**A:** Depends on your needs:

| Library | Use Case | Pros | Cons |
|---------|----------|------|------|
| **PyMuPDF** | Read PDF properties | Fast, comprehensive | Non-free commercial use |
| **pypdf** | PDF manipulation | Pure Python, simple | Slower, limited features |
| **python-pptx** | N/A | N/A | Not for PDFs |
| **pdfplumber** | Extract text/tables | Accurate | Slower |
| **pdfminer** | Text extraction | Reliable | Complex API |

**Recommendation for PaperDeck:**
```python
# Only validate that PDF was created (not contents)
assert pdf_path.exists()
assert pdf_path.stat().st_size > 0  # Has content

# For detailed validation, use optional dependency:
try:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    assert len(doc) > 0  # Has pages
except ImportError:
    # Skip detailed validation if PyMuPDF not installed
    pass
```

---

## Q15: Should I version-control test PDFs?

**A:** No. Generate them instead:

```
# .gitignore
tests/fixtures/pdfs/*.pdf  # Ignore generated test PDFs
tests/fixtures/**/*.pdf    # Or ignore all PDFs

# But DO commit helpers:
tests/helpers/pdf_helpers.py  # Commit the generator
```

**Why:**
- PDFs are binary, hard to review in diffs
- Generators are smaller, easier to maintain
- Tests are faster with generated data
- No accidental large file commits

---

## Summary

**Key Takeaways:**
1. Use mocks for unit tests, real files for integration tests
2. Generate test data programmatically (no large binary files)
3. Make tests independent with fixtures
4. Parametrize tests to cover multiple formats
5. Test graceful degradation with multiple failure scenarios
6. Test LaTeX compilation if pdflatex is available
7. Keep test execution fast (unit tests < 100ms)
8. Use pytest's built-in tools for debugging
9. Don't test file I/O in unit tests (mock it)
10. Verify end-to-end in integration tests

See `TESTING_STRATEGY_PNG_TO_PDF.md` for comprehensive strategy and `TESTING_IMPLEMENTATION_GUIDE.md` for code examples.
