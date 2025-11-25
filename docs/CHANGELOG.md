# Changelog

All notable changes to PaperDeck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Web interface for browser-based generation
- Batch processing support for multiple papers
- Custom Beamer theme support
- Figure/table caption generation
- Multi-language support
- Presentation notes generation

## [0.1.0] - 2025-11-25

### Added
- Initial release of PaperDeck
- PDF element extraction using Docling
- AI-powered slide organization
- Multi-provider AI support (OpenAI, Anthropic, Ollama, LM Studio)
- LaTeX Beamer presentation generation
- Four built-in prompt templates (default, technical, accessible, pedagogical)
- CLI interface with Click
- Automatic LaTeX to PDF compilation
- Configuration system with YAML support
- Comprehensive test suite (141 tests passing)
- Documentation (README, CONTRIBUTING, examples)

### Core Features
- **Extraction Layer**
  - PDF validation and processing
  - Figure, table, and equation extraction
  - Confidence scoring for extracted elements
  - Bounding box detection

- **AI Service Layer**
  - Abstract service interface
  - OpenAI GPT integration
  - Retry logic with exponential backoff
  - Service orchestration and selection
  - Support for multiple AI providers

- **Generation Layer**
  - LaTeX code generation with proper escaping
  - Jinja2 templating with custom delimiters
  - Intelligent slide organization
  - Support for all standard Beamer themes
  - Element grouping (small vs. large elements)

- **Prompt Management**
  - Template-based prompt system
  - Metadata-driven template loading
  - Multiple presentation styles
  - Custom template support

- **CLI Interface**
  - `generate` command for presentation creation
  - `list-prompts` command for template listing
  - `version` command for version info
  - Progress indicators
  - Verbose logging option
  - Environment variable support

### Technical Details
- Python 3.11+ requirement
- Type hints throughout codebase
- Comprehensive docstrings
- Unit and integration tests
- Code formatting with Black
- Linting with Ruff
- Type checking with mypy

### Dependencies
- click >= 8.0 (CLI framework)
- jinja2 >= 3.0 (templating)
- tiktoken >= 0.5 (tokenization)
- tenacity >= 8.0 (retry logic)
- openai >= 1.0 (OpenAI API)
- anthropic (Anthropic API)
- ollama (Ollama support)
- requests >= 2.28 (HTTP client)
- pyyaml >= 6.0 (configuration)
- pytest >= 7.0 (testing)
- black (code formatting)
- ruff (linting)
- mypy (type checking)

### Known Limitations
- Docling can be installed via pip: `pip install docling`
- LaTeX distribution required for PDF compilation
- API keys required for cloud AI providers
- Limited to PDF input format
- English language only

### Documentation
- Comprehensive README with usage examples
- CONTRIBUTING guide for developers
- MIT License
- Code documentation with docstrings
- Integration test examples

## Version History

### Version Numbering

PaperDeck follows Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Release Schedule

- **Stable releases**: Tagged versions (e.g., v0.1.0)
- **Development**: `main` branch
- **Features**: Feature branches

## Migration Guides

### Migrating to 0.1.0

Initial release - no migration needed.

## Deprecation Notices

None currently.

## Security

### Security Advisories

No known security issues at this time.

### Reporting Security Issues

Please report security vulnerabilities to: security@paperdeck.example.com

Do not open public issues for security vulnerabilities.

## Support

- **Issues**: [GitHub Issues](https://github.com/zebehn/paperdeck/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zebehn/paperdeck/discussions)
- **Documentation**: [GitHub Repository](https://github.com/zebehn/paperdeck)

---

[Unreleased]: https://github.com/zebehn/paperdeck/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zebehn/paperdeck/releases/tag/v0.1.0
