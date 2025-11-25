# Contributing to PaperDeck

Thank you for your interest in contributing to PaperDeck! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We expect everyone to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or inflammatory comments
- Publishing others' private information
- Other conduct inappropriate in a professional setting

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of LaTeX and Beamer
- Familiarity with AI/LLM concepts (helpful but not required)

### First-Time Contributors

If you're new to open source:

1. Read through existing issues and documentation
2. Look for issues labeled `good-first-issue` or `help-wanted`
3. Ask questions! Use issue comments or discussions
4. Start small - documentation improvements are valuable contributions

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/paperdeck.git
cd paperdeck
git remote add upstream https://github.com/original/paperdeck.git
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Install DocScalpel (required for PDF extraction)
pip install git+https://github.com/DS4SD/docling-core.git
```

### 4. Verify Setup

```bash
# Run tests
pytest

# Check code formatting
black --check src/ tests/

# Run linter
ruff check src/ tests/

# Type checking
mypy src/
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes** - Fix existing issues
- **New features** - Implement new functionality
- **Documentation** - Improve or add documentation
- **Tests** - Add or improve test coverage
- **Performance** - Optimize existing code
- **Refactoring** - Improve code quality
- **Examples** - Add usage examples or tutorials

### Contribution Workflow

1. **Find or create an issue**
   - Check if issue already exists
   - Create new issue if needed
   - Discuss approach before major changes

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Make changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   pytest
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "Clear, descriptive commit message"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub
   ```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some specific conventions:

#### Code Formatting

- Use **Black** for code formatting (line length: 100)
- Use **Ruff** for linting
- Use **mypy** for type checking

```bash
# Auto-format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type check
mypy src/
```

#### Naming Conventions

```python
# Classes: PascalCase
class PaperExtractor:
    pass

# Functions/methods: snake_case
def extract_elements():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private methods: _leading_underscore
def _internal_method():
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def extract_elements(pdf_path: Path, element_types: List[ElementType]) -> List[ExtractedElement]:
    """Extract elements from PDF document.

    Args:
        pdf_path: Path to the PDF file
        element_types: Types of elements to extract

    Returns:
        List[ExtractedElement]: Extracted elements with metadata

    Raises:
        ExtractionError: If extraction fails
        FileNotFoundError: If PDF file not found

    Example:
        >>> extractor = PaperExtractor()
        >>> elements = extractor.extract(Path("paper.pdf"))
        >>> len(elements)
        42
    """
    pass
```

#### Type Hints

Always include type hints:

```python
from typing import List, Optional, Dict, Any
from pathlib import Path

def process_paper(
    pdf_path: Path,
    config: Optional[AppConfiguration] = None,
) -> Dict[str, Any]:
    """Process paper with type hints."""
    pass
```

#### Imports

Organize imports in this order:

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
import click
from jinja2 import Environment

# Local application
from ..core.models import Paper
from ..core.exceptions import PaperDeckError
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_models.py
│   ├── test_extraction.py
│   └── ...
├── integration/       # Integration tests for workflows
│   ├── test_workflow.py
│   └── test_cli.py
└── fixtures/          # Test data and fixtures
    ├── sample_papers/
    └── expected_outputs/
```

### Writing Tests

#### Unit Tests

```python
import pytest
from paperdeck.core.models import Paper

class TestPaper:
    """Test Paper model functionality."""

    def test_paper_creation(self, tmp_path):
        """Test creating a valid paper."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        paper = Paper(
            file_path=pdf_file,
            title="Test Paper",
            authors=["Author 1"],
        )

        assert paper.title == "Test Paper"
        assert len(paper.authors) == 1

    def test_paper_validation(self):
        """Test paper validation."""
        with pytest.raises(FileNotFoundError):
            Paper(
                file_path=Path("nonexistent.pdf"),
                title="Test",
            )
```

#### Integration Tests

```python
def test_end_to_end_generation(tmp_path):
    """Test complete generation workflow."""
    # Setup
    pdf_file = tmp_path / "paper.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")

    # Execute
    result = generate_presentation(
        pdf_path=pdf_file,
        config=test_config,
    )

    # Verify
    assert result["tex_path"].exists()
    assert result["slide_count"] > 0
```

### Test Coverage

- Aim for >80% code coverage
- Write tests for all public APIs
- Test edge cases and error conditions
- Use fixtures for common test data

```bash
# Run tests with coverage
pytest --cov=paperdeck --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`pytest`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] No linting errors (`ruff check src/ tests/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Title Format

Use conventional commit format:

```
feat: Add support for custom Beamer themes
fix: Correct LaTeX escaping for special characters
docs: Update installation instructions
test: Add integration tests for CLI
refactor: Simplify slide organization logic
perf: Optimize PDF parsing performance
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Automated checks run (tests, linting, type checking)
2. Maintainer reviews code
3. Address feedback
4. Approval and merge

## Issue Guidelines

### Bug Reports

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. ...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.4]
- PaperDeck version: [e.g., 0.1.0]

**Additional Context**
Any other relevant information
```

### Feature Requests

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should this work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

## Development Tips

### Useful Commands

```bash
# Run specific test
pytest tests/unit/test_generation.py::TestLaTeX::test_escaping -v

# Run tests matching pattern
pytest -k "test_latex" -v

# Run with debugging
pytest --pdb

# Generate coverage report
pytest --cov=paperdeck --cov-report=term-missing

# Auto-format on save (VS Code)
# Add to settings.json:
{
    "editor.formatOnSave": true,
    "python.formatting.provider": "black"
}
```

### Debugging

```python
# Use pdb for debugging
import pdb; pdb.set_trace()

# Or ipdb for better interface
import ipdb; ipdb.set_trace()

# Rich tracebacks
from rich.traceback import install
install(show_locals=True)
```

### Common Patterns

#### Adding a New AI Provider

1. Create adapter in `src/paperdeck/ai/`
2. Implement `AIService` interface
3. Add to `AIOrchestrator`
4. Update documentation

#### Adding a New Prompt Template

1. Create template in `prompts/templates/`
2. Add metadata to `_metadata.json`
3. Update tests
4. Update documentation

## Questions?

- Check existing [documentation](README.md)
- Search [existing issues](https://github.com/yourusername/paperdeck/issues)
- Ask in [discussions](https://github.com/yourusername/paperdeck/discussions)
- Email: your.email@example.com

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to PaperDeck! 🎉
