# Test Fixtures for Figure/Table Extraction

This directory contains sample PDF files for testing DocScalpel figure and table extraction.

## Required Test Fixtures

### with_figures.pdf
- Purpose: Test figure extraction
- Should contain: 2-3 figures with captions
- Format: Standard academic paper layout

### with_tables.pdf
- Purpose: Test table extraction
- Should contain: 1-2 tables with captions
- Format: Standard academic paper layout

### with_both.pdf
- Purpose: Test combined figure and table extraction
- Should contain: Mix of figures and tables
- Format: Standard academic paper layout

## Adding Test PDFs

1. Download sample academic papers from arXiv or similar sources
2. Rename according to conventions above
3. Ensure PDFs are not encrypted
4. Keep file sizes reasonable (< 5MB)

## Note

Actual PDF files are not committed to git (see .gitignore).
Tests will skip if fixture files are missing.
