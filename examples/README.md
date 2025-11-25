# PaperDeck Examples

This directory contains example scripts demonstrating how to use PaperDeck.

## Examples

### 1. Basic Usage (`basic_usage.py`)

The simplest way to generate a presentation:

```bash
python examples/basic_usage.py
```

**Features demonstrated:**
- Default configuration
- Single paper processing
- OpenAI integration
- PDF compilation

**What it does:**
- Reads a PDF research paper
- Extracts figures, tables, and equations
- Generates a Beamer presentation
- Compiles to PDF

### 2. Advanced Usage (`advanced_usage.py`)

Advanced features and customization:

```bash
python examples/advanced_usage.py
```

**Features demonstrated:**
- Custom extraction configuration
- Multiple AI providers (OpenAI, Ollama)
- Different themes and prompts
- Progress tracking
- Error handling
- Batch processing

**What it does:**
- Example 1: High-quality presentation with GPT-4
- Example 2: Local generation with Ollama (no API key)
- Example 3: Batch process multiple papers

### 3. CLI Examples

Using PaperDeck from command line:

#### Basic CLI Usage

```bash
# Simple generation
paperdeck generate paper.pdf

# With custom theme
paperdeck generate paper.pdf --theme Copenhagen

# Technical presentation
paperdeck generate paper.pdf --prompt technical
```

#### Advanced CLI Usage

```bash
# Use specific model
paperdeck generate paper.pdf --model gpt-4 --verbose

# Use local Ollama
paperdeck generate paper.pdf --provider ollama --model llama2

# Custom output directory
paperdeck generate paper.pdf -o ~/presentations/

# Skip PDF compilation
paperdeck generate paper.pdf --no-compile
```

## Prerequisites

Before running examples:

1. **Install PaperDeck:**
   ```bash
   pip install -e .
   ```

2. **Install LaTeX** (for PDF compilation):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install texlive-full

   # macOS
   brew install --cask mactex

   # Windows
   # Download from https://miktex.org/
   ```

3. **Set up AI provider:**

   For OpenAI:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

   For Anthropic:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

   For Ollama (local):
   ```bash
   # Install Ollama
   curl https://ollama.ai/install.sh | sh

   # Pull a model
   ollama pull llama2
   ```

## Sample Papers

You can test with:

1. **Your own papers** - Any PDF research paper
2. **arXiv papers** - Download from https://arxiv.org/
3. **Public datasets** - Academic paper collections

## Common Use Cases

### Academic Presentations

Generate presentation for conference/seminar:

```bash
paperdeck generate research_paper.pdf \
  --prompt technical \
  --theme Berlin \
  --model gpt-4
```

### Teaching Materials

Create educational slides:

```bash
paperdeck generate textbook_chapter.pdf \
  --prompt pedagogical \
  --theme Madrid \
  --provider openai
```

### Quick Overview

Fast overview of a paper (no API key):

```bash
paperdeck generate paper.pdf \
  --provider ollama \
  --model llama2 \
  --prompt accessible
```

### Batch Processing

Process multiple papers:

```bash
for paper in papers/*.pdf; do
  paperdeck generate "$paper" -o presentations/
done
```

## Customization

### Custom Prompt Template

Create `~/.paperdeck/prompts/my_template.txt`:

```
Create a presentation focusing on [your requirements].

Paper content:
{paper_content}

Instructions:
- Focus on methodology
- Include code examples
- Emphasize practical applications
```

Add metadata to `~/.paperdeck/prompts/_metadata.json`:

```json
{
  "my_template": {
    "name": "my_template",
    "description": "My custom presentation style",
    "style": "custom",
    "detail_level": "high",
    "is_builtin": false
  }
}
```

Use it:

```bash
paperdeck generate paper.pdf --prompt my_template
```

### Custom Theme

While PaperDeck uses standard Beamer themes, you can customize the generated
LaTeX file after generation:

1. Generate LaTeX without compiling:
   ```bash
   paperdeck generate paper.pdf --no-compile
   ```

2. Edit `paperdeck_output/paper.tex`

3. Add custom theme commands:
   ```latex
   \usetheme{Madrid}
   \usecolortheme{seahorse}
   \usefonttheme{serif}
   ```

4. Compile manually:
   ```bash
   cd paperdeck_output
   pdflatex paper.tex
   ```

## Troubleshooting

### Common Issues

**Issue: "API key not found"**
```bash
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"
```

**Issue: "pdflatex not found"**
```bash
# Solution: Install LaTeX or skip compilation
paperdeck generate paper.pdf --no-compile
```

**Issue: "Ollama not running"**
```bash
# Solution: Start Ollama service
ollama serve
```

**Issue: "PDF parsing failed"**
- Ensure PDF is not corrupted
- Check PDF is not encrypted
- Try with a different paper

### Getting Help

1. Check error message for specific issue
2. Run with `--verbose` flag for details
3. Check logs in output directory
4. Open issue on GitHub

## Performance Tips

1. **Use local models** (Ollama) for faster iteration
2. **Skip compilation** during development (`--no-compile`)
3. **Limit extraction** to specific element types
4. **Cache results** for repeated processing
5. **Batch process** multiple papers efficiently

## Next Steps

After running examples:

1. Try with your own papers
2. Experiment with different themes
3. Create custom prompts
4. Integrate into your workflow
5. Contribute improvements!

## Additional Resources

- [Main README](../README.md) - Full documentation
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines
- [Issue Tracker](https://github.com/zebehn/paperdeck/issues) - Report problems
- [Discussions](https://github.com/zebehn/paperdeck/discussions) - Ask questions

---

Happy presenting! 🎓
