# Test PDF Fixtures

This directory contains sample PDF files for testing text extraction functionality.

## Required Fixtures

The following PDF fixtures are needed for comprehensive testing:

### 1. simple_single_column.pdf
- **Purpose**: Test basic single-column text extraction
- **Characteristics**:
  - Single-column layout
  - ~10 pages
  - Standard academic paper format
  - Clear text, no scanned content
  - Contains: title, abstract, introduction, methodology, results, conclusion
- **Source**: Any standard academic paper from arXiv or similar

### 2. multi_column_ieee.pdf
- **Purpose**: Test multi-column layout detection and extraction
- **Characteristics**:
  - Two-column IEEE format
  - ~8 pages
  - Academic conference paper format
  - Contains figures, tables, equations
  - Text flows across columns
- **Source**: IEEE conference paper or similar two-column format

### 3. large_50_pages.pdf
- **Purpose**: Test performance with large documents (SC-002: <10s extraction)
- **Characteristics**:
  - 50+ pages
  - Any standard academic format
  - Used for performance benchmarking
- **Source**: PhD thesis, technical report, or long research paper

### 4. encrypted.pdf (optional, for error handling)
- **Purpose**: Test error handling for encrypted/protected PDFs
- **Characteristics**:
  - PDF with password protection or copy restrictions
  - Should trigger extraction failure

### 5. scanned_images.pdf (optional, for edge case)
- **Purpose**: Test handling of scanned PDFs (no text layer)
- **Characteristics**:
  - Scanned images of text (no OCR)
  - Should produce minimal or no extracted text
  - Used to test graceful fallback

## How to Add Fixtures

1. **From arXiv**: Download any open-access paper:
   ```bash
   # Example: Download a paper from arXiv
   wget https://arxiv.org/pdf/XXXX.XXXXX.pdf -O simple_single_column.pdf
   ```

2. **From IEEE**: Download two-column conference paper (if you have access)

3. **Generate test PDF** (for development):
   ```python
   # Simple script to generate a test PDF
   from reportlab.pdfgen import canvas
   from reportlab.lib.pagesizes import letter

   c = canvas.Canvas("test_paper.pdf", pagesize=letter)
   c.drawString(100, 750, "Test Paper Title")
   c.drawString(100, 700, "Abstract: This is a test paper...")
   c.showPage()
   c.save()
   ```

## Usage in Tests

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "sample_papers"
SIMPLE_PDF = FIXTURES_DIR / "simple_single_column.pdf"
MULTI_COLUMN_PDF = FIXTURES_DIR / "multi_column_ieee.pdf"
LARGE_PDF = FIXTURES_DIR / "large_50_pages.pdf"

def test_extract_simple_pdf():
    result = extractor.extract(SIMPLE_PDF, config)
    assert result.status == ExtractionStatus.SUCCESS
```

## Note

**The actual PDF files are not committed to git** (see .gitignore excludes `*.pdf`).
Developers must add their own test PDFs to this directory for testing.

For CI/CD, consider using fixture generation scripts or downloading from public sources during test setup.
