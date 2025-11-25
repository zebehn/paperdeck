# PaperDeck Documentation

This directory contains all documentation, guides, and testing scripts for PaperDeck.

## 📚 Documentation Files

### User Guides

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for getting up and running with PaperDeck
- **[CLI_TEST_GUIDE.md](CLI_TEST_GUIDE.md)** - Comprehensive guide for testing the CLI with text extraction feature

### Developer Guides

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guidelines for contributing to PaperDeck
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and project instructions for Claude Code

### Project Information

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and change log

## 🧪 Testing Scripts

### Text Extraction Testing

- **[test_extraction_simple.py](test_extraction_simple.py)** - Simple command-line test for text extraction
  ```bash
  python docs/test_extraction_simple.py paper.pdf
  ```

- **[test_extraction_manual.py](test_extraction_manual.py)** - Comprehensive test with detailed output
  ```bash
  python docs/test_extraction_manual.py paper.pdf
  python docs/test_extraction_manual.py paper.pdf --compare
  ```

### CLI Demo

- **[demo_cli.sh](demo_cli.sh)** - Interactive demo script for testing the complete CLI workflow
  ```bash
  ./docs/demo_cli.sh paper.pdf
  ```

## 🚀 Quick Start

1. **For Users:** Start with [QUICKSTART.md](QUICKSTART.md)
2. **For CLI Testing:** See [CLI_TEST_GUIDE.md](CLI_TEST_GUIDE.md)
3. **For Contributors:** Read [CONTRIBUTING.md](CONTRIBUTING.md)
4. **For Testing:** Run [demo_cli.sh](demo_cli.sh) or test scripts

## 📖 Documentation Structure

```
docs/
├── README.md                      # This file - documentation index
├── QUICKSTART.md                  # User quick start guide
├── CLI_TEST_GUIDE.md             # CLI testing guide
├── CONTRIBUTING.md                # Contribution guidelines
├── CLAUDE.md                      # Claude Code instructions
├── CHANGELOG.md                   # Version history
├── demo_cli.sh                    # CLI demo script
├── test_extraction_simple.py     # Simple extraction test
└── test_extraction_manual.py     # Detailed extraction test
```

## 🔗 Related Documentation

- **Main README:** See `../README.md` for project overview
- **Spec Documents:** See `../specs/` for feature specifications
- **Test Documentation:** See `../tests/` for test documentation

## 📝 Adding Documentation

When adding new documentation:

1. Place user-facing guides in this directory
2. Update this README with links to new documents
3. Use clear, descriptive filenames
4. Include usage examples where applicable
5. Keep technical specs in `../specs/` directory
