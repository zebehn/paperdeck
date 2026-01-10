# paperdeck Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-30

## Active Technologies
- Python 3.11+ + Click (CLI), pathlib (file operations), core models and config from existing codebase (007-skip-extraction)
- Local filesystem for reading pre-extracted PDF files (007-skip-extraction)
- Python 3.11 + Click (CLI), pathlib (file operations), existing ExtractedElement model (007-skip-extraction)
- File system (pre-extracted PDFs in specified directory) (007-skip-extraction)
- Python 3.11 (pyproject.toml requires >=3.11) + Click 8.0+ (CLI), pathlib (file operations), existing paperdeck validation module (008-latex-syntax-agent)
- Local filesystem (LaTeX files, backups in `.backup/` directory, validation logs) (008-latex-syntax-agent)

- (006-docscalpel-pdf-output)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes
- 008-latex-syntax-agent: Added Python 3.11 (pyproject.toml requires >=3.11) + Click 8.0+ (CLI), pathlib (file operations), existing paperdeck validation module
- 007-skip-extraction: Added Python 3.11 + Click (CLI), pathlib (file operations), existing ExtractedElement model
- 007-skip-extraction: Added Python 3.11+ + Click (CLI), pathlib (file operations), core models and config from existing codebase


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
