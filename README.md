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
- `-o, --output PATH` - Output directory (default: ./paperdeck_output)
- `-t, --theme TEXT` - Beamer theme (default: Madrid)
- `-p, --prompt TEXT` - Prompt template (default: default)
- `--provider TEXT` - AI provider: openai, anthropic, ollama, lmstudio (default: openai)
- `--model TEXT` - Specific model to use (e.g., gpt-4, claude-3-opus)
- `--api-key TEXT` - API key for cloud providers
- `--no-compile` - Skip LaTeX compilation to PDF
- `-v, --verbose` - Enable verbose output
- `--help` - Show help message

**Examples:**

```bash
# Basic usage with defaults
paperdeck generate my_paper.pdf

# Custom output directory and theme
paperdeck generate my_paper.pdf -o presentations/ -t Berkeley

# Use custom prompt template (e.g., hangeul for Korean language presentations)
# Demonstrates customizability of prompts for specific purposes
paperdeck generate my_paper.pdf -p hangeul

# Use GPT-4 with verbose output
paperdeck generate my_paper.pdf --model gpt-4 -v

# Use local Ollama model
paperdeck generate my_paper.pdf --provider ollama --model llama2

# Generate LaTeX only, skip PDF compilation
paperdeck generate my_paper.pdf --no-compile
```

#### `paperdeck list-prompts`

List available prompt templates.

```bash
paperdeck list-prompts
```

**Output:**
```
Available prompt templates (2):

  • default [builtin]
    Standard presentation template with balanced technical content
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
  confidence_threshold: 0.75
  element_types:
    - FIGURE
    - TABLE
    - EQUATION

output_directory: ~/Documents/paperdeck_output
default_theme: Madrid
default_prompt: default
log_level: INFO
```

### Prompt Templates

PaperDeck includes two built-in prompt templates:

#### 1. **Default**
- Suitable for: General academic presentations
- Detail level: Medium
- Audience: Academic researchers
- Features: Balanced technical content with clear structure

#### 2. **Hangeul** (Korean Language)
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
│       └── prompts/         # Prompt management
│           └── manager.py
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

**Issue: LaTeX compilation fails**
```bash
# Generate LaTeX only and inspect
paperdeck generate paper.pdf --no-compile

# Check the generated .tex file in paperdeck_output/
# Manually compile to see detailed errors:
cd paperdeck_output
pdflatex presentation.tex
```

## 📊 Performance

Typical processing times on standard hardware:
- PDF extraction: 5-10 seconds per paper
- AI processing: 10-30 seconds (depends on provider/model)
- LaTeX generation: < 1 second
- PDF compilation: 2-5 seconds

Total: ~20-50 seconds per paper

## 🔒 Security & Privacy

- API keys are never logged or stored
- PDF files are processed locally
- Only extracted text/metadata is sent to AI providers
- No data retention by PaperDeck
- Refer to your AI provider's privacy policy for their data handling

---

**Made with ❤️ by the PaperDeck Team**
