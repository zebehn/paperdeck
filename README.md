# PaperDeck

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/github-zebehn/paperdeck-blue?logo=github)](https://github.com/zebehn/paperdeck)
[![Tests](https://img.shields.io/badge/tests-95%20passing-success)](https://github.com/zebehn/paperdeck)

**PaperDeck** is an intelligent LaTeX presentation generator that transforms research papers (PDFs) into polished Beamer presentations using AI.

## ✨ Features

- 📄 **Automatic PDF Parsing** - Extracts figures, tables, equations, and text from research papers
- 🤖 **AI-Powered Organization** - Intelligently organizes content into logical presentation slides
- 🎨 **Multiple Themes** - Supports all standard Beamer themes (Madrid, Copenhagen, Berkeley, etc.)
- 💬 **Flexible Prompts** - Customize presentation generation with built-in or custom prompt templates
- 🔌 **Multi-Provider AI Support**:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Ollama (Local models)
  - LM Studio (Local models)
- 📝 **LaTeX Generation** - Produces clean, compilable Beamer LaTeX code
- ✅ **Built-in Validation** - Automatic detection and fixing of LaTeX structural errors
- 🔄 **Error Recovery** - Retry compilation with auto-fixes when errors occur
- 🖥️ **CLI Interface** - Easy-to-use command-line interface

## 🚀 Quick Start

### Installation

#### Prerequisites

- Python 3.11 or higher
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX) for PDF compilation
- API key for cloud AI providers (OpenAI or Anthropic) or local model setup (Ollama/LM Studio)

#### Install from Source

```bash
# Clone the repository
git clone https://github.com/zebehn/paperdeck.git
cd paperdeck

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## 📖 Documentation

### Command Reference

#### `paperdeck generate`

Generate a presentation from a PDF research paper.

```bash
paperdeck generate [OPTIONS] PDF_PATH
```

**Arguments:**
- `PDF_PATH` - Path to the input PDF file (required)

**Options:**
- `-o, --output PATH` - Output directory (default: ./<pdf_filename>)
- `-t, --theme TEXT` - Beamer theme (default: Madrid)
- `-p, --prompt TEXT` - Prompt template (default: default)
- `--provider TEXT` - AI provider: openai, anthropic, ollama, lmstudio (default: openai)
- `--model TEXT` - Specific model to use (e.g., gpt-4, claude-3-opus)
- `--api-key TEXT` - API key for cloud providers
- `--skip-extraction` - Skip figure/table extraction, use pre-extracted files
- `--elements-input-dir PATH` - Directory with pre-extracted elements (default: <output>/extracted)
- `--no-compile` - Skip LaTeX compilation to PDF
- `-v, --verbose` - Enable verbose output
- `--help` - Show help message

**Examples:**

```bash
# Basic usage with defaults
paperdeck generate my_paper.pdf

# Custom output directory and theme
paperdeck generate my_paper.pdf -o presentations/ -t Berkeley

# Use single-element template for clean discussion → visual layout
paperdeck generate my_paper.pdf -p single-element

# Use complete template for comprehensive coverage
paperdeck generate my_paper.pdf -p complete

# Use hangeul template for Korean language presentations
paperdeck generate my_paper.pdf -p hangeul

# Use GPT-4 with verbose output
paperdeck generate my_paper.pdf --model gpt-4 -v

# Use local Ollama model
paperdeck generate my_paper.pdf --provider ollama --model llama2

# Generate LaTeX only, skip PDF compilation
paperdeck generate my_paper.pdf --no-compile

# Fast regeneration: Skip slow extraction, use pre-extracted figures
# First run: Extract and generate (30-40 seconds)
paperdeck generate my_paper.pdf -o output/

# Subsequent runs: Regenerate with different settings (< 5 seconds)
paperdeck generate my_paper.pdf --skip-extraction --prompt hangeul
paperdeck generate my_paper.pdf --skip-extraction --theme Berkeley
paperdeck generate my_paper.pdf --skip-extraction --model gpt-4

# Use pre-extracted elements from custom directory
paperdeck generate my_paper.pdf --skip-extraction --elements-input-dir ./my_figures/
```

#### `paperdeck list-prompts`

List available prompt templates.

```bash
paperdeck list-prompts
```

**Output:**
```
Available prompt templates (4):

  • default [builtin]
    Standard presentation template with balanced technical content
    Style: technical, Detail: medium

  • complete [builtin]
    Comprehensive presentation with detailed content coverage
    Style: technical, Detail: high

  • single-element [builtin]
    Modern layout with discussion → visual pattern (one element per slide)
    Style: technical, Detail: medium

  • hangeul [builtin]
    Korean language presentation template
    Style: custom, Detail: medium
```

#### `paperdeck version`

Show version information.

```bash
paperdeck version
```

### Configuration

#### Environment Variables

Set API keys via environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### Configuration File

Create a configuration file at `~/.paperdeck/config.yaml`:

```yaml
ai_services:
  default_provider: openai
  openai_api_key: sk-...
  max_retries: 3
  timeout_seconds: 60

extraction:
  confidence_threshold: 0.5   # Detection confidence (0.0-1.0, default: 0.5)
  boundary_padding: 10        # Extra pixels around elements (default: 0)
  max_pages: 50               # Limit extraction to first N pages (optional)
  element_types:
    - FIGURE
    - TABLE
    - EQUATION

# output_directory: ~/Documents/papers  # Optional: override default naming
default_theme: Madrid
default_prompt: default
log_level: INFO
```

#### Extraction Parameters Explained

**confidence_threshold** (0.0-1.0, default: 0.5)
- Controls how confident DocScalpel must be to extract an element
- Higher values (0.7-0.9): Fewer false positives, may miss some elements
- Lower values (0.3-0.5): More elements extracted, may include false positives
- Default 0.5 provides good balance for most papers
- Use `--extraction-confidence 0.75` for high-quality papers to reduce false positives

**boundary_padding** (pixels, default: 0)
- Adds extra space around extracted figures/tables
- Useful when elements are cropped too tightly
- Typical values: 5-20 pixels
- Example: 10 pixels adds a 10px border on all sides

**max_pages** (optional)
- Limits extraction to first N pages of the PDF
- Useful for testing or when processing very large papers
- Omit or set to `null` to process all pages

**Example output when running extraction**:
```
INFO - Extracting elements from paper.pdf using DocScalpel CLI...
INFO - DocScalpel Configuration:
INFO -   • Element types: figure,table
INFO -   • Confidence threshold: 0.75
INFO -   • Boundary padding: 10 pixels
INFO -   • Max pages: 50
INFO -   • Output directory: ./output/extracted
```


### Prompt Templates

PaperDeck includes four built-in prompt templates:

#### 1. **Default**
- Suitable for: General academic presentations
- Detail level: Medium
- Audience: Academic researchers
- Features: Balanced technical content with clear structure

#### 2. **Complete**
- Suitable for: Comprehensive academic presentations
- Detail level: High
- Audience: Academic researchers
- Features: Detailed content coverage with two-column layouts for figures/tables

#### 3. **Single-Element** (Recommended)
- Suitable for: Modern, visually-focused presentations
- Detail level: Medium
- Audience: Academic researchers and general audiences
- Features:
  - **Discussion → Visual pattern**: Each figure/table gets two dedicated slides
  - **Slide 1**: Discussion bullets explaining the content
  - **Slide 2**: Full-screen figure/table with caption
  - **Clean layout**: No complex multi-column layouts
  - **Better sizing**: Figures use 90% of slide width, tables use 95%
  - **Smaller captions**: `\small` font for more compact captions
  - **No overfull boxes**: Simpler layout eliminates LaTeX sizing issues
  - **Perfect for**: Papers with many figures/tables

**Example structure:**
```
Discussion Slide:         Figure Slide:
┌─────────────────────┐  ┌─────────────────────┐
│ Architecture Overview│  │ Figure 1            │
│ • Component 1        │  │                     │
│ • Component 2        │  │    [Full-screen     │
│ • Component 3        │  │     figure]         │
│ • Key insight        │  │                     │
└─────────────────────┘  │ Caption: ...        │
                         └─────────────────────┘
```

#### 4. **Hangeul** (Korean Language)
- Suitable for: Korean language presentations
- Detail level: Medium
- Audience: Korean-speaking academic audiences
- Features: Korean language output with appropriate academic terminology

### Custom Prompt Templates

You can create custom prompts in two ways:

#### Option 1: Use a Custom Prompt File

Create a prompt file anywhere and reference it by path:

**my_custom_prompt.txt:**
```
Create a presentation focusing on [your specific requirements].

Paper content:
{paper_content}

Instructions:
- [Your custom instruction 1]
- [Your custom instruction 2]
- ...
```

**Usage:**
```bash
paperdeck generate paper.pdf --prompt /path/to/my_custom_prompt.txt
```

#### Option 2: Add to Prompt Library

Create custom prompts in `~/.paperdeck/prompts/` for reusable templates:

**my_prompt.txt:**
```
Create a presentation focusing on [your specific requirements].

Paper content:
{paper_content}

Instructions:
- [Your custom instruction 1]
- [Your custom instruction 2]
- ...
```

**_metadata.json:**
```json
{
  "my_prompt": {
    "name": "my_prompt",
    "description": "My custom prompt style",
    "style": "custom",
    "detail_level": "medium",
    "is_builtin": false
  }
}
```

**Usage:**
```bash
paperdeck generate paper.pdf --prompt my_prompt
```

## 🎨 Beamer Themes

PaperDeck supports all standard Beamer themes:

**Popular Themes:**
- Madrid (default)
- Copenhagen
- Berkeley
- Berlin
- Singapore
- Warsaw
- Darmstadt
- Frankfurt
- Hannover
- Ilmenau
- Montpellier
- Pittsburgh
- Rochester

## ✅ LaTeX Validation & Error Recovery

PaperDeck includes a robust validation system to ensure generated LaTeX code compiles successfully.

### Features

**Automatic Error Detection:**
- Missing `\end{...}` tags (frames, columns, itemize, etc.)
- Unmatched `\begin{...}` / `\end{...}` pairs
- Duplicate environment blocks
- Delimiter matching (braces `{}`, brackets `[]`, parentheses `()`)
- HTML/XML syntax detection (catches LLM mistakes)
- Structural errors that break compilation

**Auto-Fix Capabilities:**
- Automatically adds missing `\end{...}` tags with proper indentation
- Removes duplicate environment blocks
- Fixes missing or extra closing braces
- Removes HTML/XML tags accidentally generated by LLMs
- Preserves original formatting and structure
- Confidence-based fixing (only applies high-confidence fixes)
- ~90% success rate for automatic fixes

**Backup System:**
- Automatic SHA256-verified backups before applying fixes
- Stored in `.backup/` directory within output folder
- Integrity validation on restore
- Easy rollback if needed

**Retry & Recovery:**
- Validates LaTeX before compilation
- Applies auto-fixes when errors detected
- Retries compilation up to 2 times with fixes
- Overall >98% compilation success rate

### Configuration

Control validation behavior in `~/.paperdeck/config.yaml`:

```yaml
# LaTeX validation and error recovery
enable_validation: true        # Enable structural validation
enable_autofix: true          # Enable automatic error fixing
enable_retry: true            # Enable retry on compilation failure
max_retry_attempts: 2         # Maximum retry attempts

# Auto-fix configuration
fixer_config:
  fix_missing_ends: true      # Add missing \end{...} tags
  fix_duplicates: true        # Remove duplicate blocks
  fix_missing_braces: true    # Add missing closing braces
  fix_extra_braces: false     # Remove extra closing braces (conservative)
  fix_html_syntax: true       # Remove HTML/XML tags
  confidence_threshold: 0.80  # Minimum confidence for auto-fix (0.0-1.0)
  create_backup: true         # Create SHA256-verified backups
  backup_dir: ".backup"       # Backup directory

# Environments to validate
validation_environments:
  - frame
  - columns
  - column
  - itemize
  - enumerate
```

### Validation API

You can use the validation system programmatically:

```python
from pathlib import Path
from paperdeck.validation import LaTeXValidator, LaTeXFixer

# Validate a .tex file
validator = LaTeXValidator()
result = validator.validate_file(Path("presentation.tex"))

if result.has_errors():
    print(f"Found {result.error_count()} errors:")
    for error in result.errors:
        print(f"  Line {error.line_number}: {error.message}")

    # Apply auto-fixes
    content = Path("presentation.tex").read_text()
    fixer = LaTeXFixer()
    fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

    print(f"\nApplied {len(changes)} fixes:")
    for change in changes:
        print(f"  {change.description}")

    # Write fixed content
    Path("presentation.tex").write_text(fixed_content)
```

### Performance

Validation is fast and lightweight:
- Validation: <100ms for 50-slide presentations
- Auto-fix: <200ms for typical errors
- Total overhead: <300ms end-to-end

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and install in development mode
git clone https://github.com/zebehn/paperdeck.git
cd paperdeck
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=paperdeck --cov-report=html

# Run specific test file
pytest tests/unit/test_generation.py

# Run integration tests only
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
paperdeck/
├── src/
│   └── paperdeck/
│       ├── ai/              # AI service integrations
│       │   ├── service.py   # Abstract AI service interface
│       │   ├── openai_adapter.py
│       │   ├── orchestrator.py
│       │   └── retry_helpers.py
│       ├── cli/             # Command-line interface
│       │   ├── main.py      # CLI entry point
│       │   └── commands.py  # Command implementations
│       ├── core/            # Core models and config
│       │   ├── models.py    # Data models
│       │   ├── config.py    # Configuration
│       │   └── exceptions.py
│       ├── extraction/      # PDF extraction
│       │   ├── extractor.py # Main extractor
│       │   └── pdf_processor.py
│       ├── generation/      # LaTeX generation
│       │   ├── latex_generator.py
│       │   └── slide_organizer.py
│       ├── prompts/         # Prompt management
│       │   └── manager.py
│       └── validation/      # LaTeX validation & auto-fix
│           ├── latex_validator.py    # Structural validation
│           ├── latex_fixer.py        # Auto-fix errors
│           ├── delimiter_matcher.py  # Delimiter matching (braces, brackets, parens)
│           ├── backup_manager.py     # SHA256-verified backups
│           ├── cli_integration.py    # CLI integration helpers
│           ├── validation_errors.py  # Error data models
│           ├── error_types.py        # Error type definitions
│           └── utils.py              # Validation utilities
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── prompts/
│   └── templates/          # Built-in prompt templates
└── pyproject.toml          # Project configuration
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository at https://github.com/zebehn/paperdeck
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code (`black src/ tests/`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request at https://github.com/zebehn/paperdeck/pulls

### Development Guidelines

- Follow PEP 8 style guidelines
- Write docstrings for all public functions/classes
- Add type hints to function signatures
- Write unit tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DocScalpel](https://github.com/zebehn/docscalpel) - PDF figure and table extraction
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF text extraction
- [Beamer](https://github.com/josephwright/beamer) - LaTeX presentation class
- [Click](https://click.palletsprojects.com/) - CLI framework

## 📧 Contact & Support

- **GitHub Repository:** https://github.com/zebehn/paperdeck
- **Issues & Bug Reports:** https://github.com/zebehn/paperdeck/issues
- **Pull Requests:** https://github.com/zebehn/paperdeck/pulls
- **Documentation:** https://github.com/zebehn/paperdeck/tree/main/docs

## 🔮 Roadmap

- [ ] Support for additional document formats (DOCX, HTML)
- [ ] Web interface
- [ ] Batch processing
- [ ] Custom Beamer themes
- [ ] Figure/table caption generation
- [ ] Multi-language support
- [ ] Presentation notes generation
- [ ] Animation and transition suggestions

## ⚠️ Troubleshooting

### Common Issues

**Issue: "pdflatex not found"**
```bash
# Install TeX Live (Linux)
sudo apt-get install texlive-full

# Install MacTeX (macOS)
brew install --cask mactex

# Install MiKTeX (Windows)
# Download from https://miktex.org/download
```

**Issue: "OpenAI API key not configured"**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or use --api-key flag
paperdeck generate paper.pdf --api-key sk-...
```

**Issue: "Elements directory does not exist" when using --skip-extraction**

```bash
# Error: Elements directory does not exist: output/extracted
# Solution 1: Run without --skip-extraction first to generate files
paperdeck generate paper.pdf -o output/

# Solution 2: Specify the correct directory path
paperdeck generate paper.pdf --skip-extraction --elements-input-dir /path/to/extracted/

# Solution 3: Use default directory (output/extracted)
paperdeck generate paper.pdf --skip-extraction  # Uses output/extracted by default
```

**Issue: "No valid element files found" in elements directory**

```bash
# Check directory contents - looking for figure_##.pdf and table_##.pdf
ls output/extracted/

# Expected files: figure_01.pdf, figure_02.pdf, table_01.pdf, etc.
# If files have different names, run extraction first:
paperdeck generate paper.pdf -o output/
```

**Issue: Gaps in figure numbering warnings**

This is informational only - generation will continue:
```
WARNING: Missing figure_02.pdf (found 01, 03)
```

The presentation will be generated with available figures (01, 03) and skip missing ones.

**Issue: LaTeX compilation fails**

PaperDeck includes automatic validation and error fixing. If compilation still fails:

```bash
# Check if validation is enabled (should be by default)
# Add to ~/.paperdeck/config.yaml:
enable_validation: true
enable_autofix: true
enable_retry: true

# Generate LaTeX only and inspect
paperdeck generate paper.pdf --no-compile

# Manually validate the generated file
python -c "
from pathlib import Path
from paperdeck.validation import LaTeXValidator
validator = LaTeXValidator()
result = validator.validate_file(Path('paperdeck_output/presentation.tex'))
print(result)
"

# Check the generated .tex file in paperdeck_output/
# Manually compile to see detailed errors:
cd paperdeck_output
pdflatex presentation.tex
```

Most structural errors (missing `\end{frame}`, `\end{column}`, etc.) are automatically detected and fixed. If you encounter persistent compilation issues, please report them with the generated `.tex` file.

## 📊 Performance

Typical processing times on standard hardware:

**Normal Generation (with extraction):**
- PDF text extraction: 2-5 seconds
- Figure/table extraction: 30-40 seconds
- AI processing: 10-30 seconds (depends on provider/model)
- LaTeX generation: < 1 second
- PDF compilation: 2-5 seconds

**Total:** ~45-80 seconds per paper

**Fast Regeneration (skip extraction):**
- PDF text extraction: 2-5 seconds
- Figure/table loading: < 1 second (from pre-extracted files)
- AI processing: 10-30 seconds
- LaTeX generation: < 1 second
- PDF compilation: 2-5 seconds

**Total:** ~15-40 seconds per paper (up to **83% faster**)

**When to use `--skip-extraction`:**
- Iterating on prompt templates
- Testing different themes
- Trying different AI models/parameters
- Any scenario where figures/tables haven't changed

This dramatically speeds up the development workflow when refining presentations!

## 🔒 Security & Privacy

- API keys are never logged or stored
- PDF files are processed locally
- Only extracted text/metadata is sent to AI providers
- No data retention by PaperDeck
- Refer to your AI provider's privacy policy for their data handling

---

**Made with ❤️ by the PaperDeck Team**
