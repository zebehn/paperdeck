# PaperDeck Quick Start Guide

Get up and running with PaperDeck in 5 minutes!

## ⚡ 5-Minute Setup

### Step 1: Install Python (if needed)

```bash
# Check Python version (need 3.11+)
python --version

# If needed, install Python 3.11+
# Visit: https://www.python.org/downloads/
```

### Step 2: Install PaperDeck

```bash
# Clone repository
git clone https://github.com/zebehn/paperdeck.git
cd paperdeck

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt
pip install -e .
```

### Step 3: Set Up AI Provider

**Option A: OpenAI (Cloud, requires API key)**

```bash
# Get API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

**Option B: Ollama (Local, no API key needed)**

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Start Ollama
ollama serve
```

### Step 4: Generate Your First Presentation

```bash
# Using OpenAI
paperdeck generate your_paper.pdf

# Using Ollama (local)
paperdeck generate your_paper.pdf --provider ollama
```

### Step 5: View Results

```bash
cd paperdeck_output
# Open your_paper.pdf in PDF viewer
```

Done! 🎉

## 📋 Quick Command Reference

### Basic Commands

```bash
# Generate presentation (default settings)
paperdeck generate paper.pdf

# List available prompt templates
paperdeck list-prompts

# Show version
paperdeck version

# Help
paperdeck --help
paperdeck generate --help
```

### Common Options

```bash
# Choose theme
paperdeck generate paper.pdf --theme Copenhagen

# Choose presentation style
paperdeck generate paper.pdf --prompt technical

# Specify output directory
paperdeck generate paper.pdf -o my_presentations/

# Verbose output
paperdeck generate paper.pdf -v

# Generate LaTeX only (skip PDF)
paperdeck generate paper.pdf --no-compile
```

### AI Provider Options

```bash
# OpenAI with specific model
paperdeck generate paper.pdf --provider openai --model gpt-4

# Anthropic Claude
paperdeck generate paper.pdf --provider anthropic --api-key sk-ant-...

# Ollama (local)
paperdeck generate paper.pdf --provider ollama --model llama2

# LM Studio (local)
paperdeck generate paper.pdf --provider lmstudio
```

## 🎨 Available Themes

Popular Beamer themes you can use:

- `Madrid` (default) - Clean and professional
- `Copenhagen` - Blue headers, simple
- `Berlin` - Colorful with TOC sidebar
- `Berkeley` - Blue theme with navigation
- `Singapore` - Minimalist
- `Warsaw` - Red accents
- `Frankfurt` - Vertical navigation
- `Hannover` - Tree-style navigation

Try them:
```bash
paperdeck generate paper.pdf --theme Berlin
```

## 💬 Prompt Styles

Choose the right style for your audience:

| Style | Best For | Detail Level |
|-------|----------|--------------|
| `default` | General academic presentations | Medium |
| `technical` | Conferences, expert audiences | High |
| `accessible` | Departmental talks, broad audiences | Low |
| `pedagogical` | Teaching, workshops, tutorials | Medium |

Try them:
```bash
paperdeck generate paper.pdf --prompt pedagogical
```

## 🐛 Troubleshooting

### "Command not found: paperdeck"

```bash
# Activate virtual environment
source venv/bin/activate

# Or install globally (not recommended)
pip install -e . --user
```

### "API key not found"

```bash
# Set environment variable
export OPENAI_API_KEY="your-key"

# Or pass directly
paperdeck generate paper.pdf --api-key sk-...
```

### "pdflatex not found"

```bash
# Install LaTeX
# Ubuntu: sudo apt-get install texlive-full
# macOS: brew install --cask mactex
# Windows: https://miktex.org/

# Or skip PDF compilation
paperdeck generate paper.pdf --no-compile
```

### "PDF parsing failed"

- Check PDF is not encrypted
- Ensure PDF is valid (not corrupted)
- Try a different paper
- Use `--verbose` for details

### "Ollama connection failed"

```bash
# Make sure Ollama is running
ollama serve

# Check if models are downloaded
ollama list
```

## 📚 Next Steps

### Learn More

1. **Read full documentation**: [README.md](README.md)
2. **Try examples**: See [examples/](examples/)
3. **Customize**: Create custom prompts
4. **Contribute**: Check [CONTRIBUTING.md](CONTRIBUTING.md)

### Example Workflows

**For Researchers:**
```bash
# Conference presentation
paperdeck generate research.pdf --prompt technical --theme Berlin -v
```

**For Teachers:**
```bash
# Lecture slides
paperdeck generate textbook.pdf --prompt pedagogical --theme Madrid
```

**For Students:**
```bash
# Paper presentation (free, using Ollama)
paperdeck generate paper.pdf --provider ollama --prompt accessible
```

**For Quick Review:**
```bash
# Fast overview
paperdeck generate paper.pdf --no-compile -v
```

## 🎯 Pro Tips

1. **Start with Ollama** - No API costs, good for testing
2. **Use `--no-compile`** - Faster iteration during development
3. **Try different themes** - Presentations look different with each theme
4. **Customize LaTeX** - Edit generated .tex file for fine-tuning
5. **Batch process** - Use shell scripts for multiple papers

## 🆘 Getting Help

- **Quick questions**: Check [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/zebehn/paperdeck/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zebehn/paperdeck/discussions)
- **Documentation**: [GitHub Repository](https://github.com/zebehn/paperdeck)

## 📦 What's Included

When you generate a presentation, you get:

```
paperdeck_output/
├── your_paper.tex          # LaTeX source
├── your_paper.pdf          # Compiled presentation (if --compile)
├── your_paper.log          # Compilation log
└── extracted/              # Extracted figures/tables
    ├── figure_1.pdf
    ├── figure_2.pdf
    └── ...
```

## ⚙️ Configuration

### Quick Config

Create `~/.paperdeck/config.yaml`:

```yaml
ai_services:
  default_provider: ollama
  ollama_base_url: http://localhost:11434

extraction:
  confidence_threshold: 0.75

output_directory: ~/presentations
default_theme: Copenhagen
default_prompt: technical
```

### Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export PAPERDECK_OUTPUT_DIR="~/presentations"
```

## 🚀 Advanced Quick Tips

### Process Entire Directory

```bash
# Bash
for pdf in papers/*.pdf; do
  paperdeck generate "$pdf" -o presentations/
done

# Python
from pathlib import Path
for pdf in Path("papers").glob("*.pdf"):
    # Use PaperDeck Python API
```

### Custom Pipeline

```python
from paperdeck.cli.commands import generate_presentation
from paperdeck.core.config import AppConfiguration

config = AppConfiguration()
result = generate_presentation(
    pdf_path=Path("paper.pdf"),
    config=config,
    theme="Berlin",
    prompt_name="technical",
)
```

### Integrate with CI/CD

```yaml
# GitHub Actions example
- name: Generate Presentations
  run: |
    pip install paperdeck
    paperdeck generate paper.pdf --provider ollama
```

## 📈 Performance

Typical times for a 10-page paper:

- **PDF Extraction**: 5-10 seconds
- **AI Processing**: 10-30 seconds
- **LaTeX Generation**: < 1 second
- **PDF Compilation**: 2-5 seconds
- **Total**: 20-50 seconds

## 🎓 Learning Resources

1. **LaTeX/Beamer**: https://www.overleaf.com/learn/latex/Beamer
2. **AI Prompting**: https://platform.openai.com/docs/guides/prompt-engineering
3. **Examples**: See `examples/` directory
4. **Documentation**: See `README.md`

---

**Ready to create amazing presentations? Let's go! 🚀**

For detailed documentation, see [README.md](README.md)
