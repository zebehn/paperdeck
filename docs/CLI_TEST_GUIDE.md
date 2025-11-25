# PaperDeck CLI Testing Guide

## Text Extraction Integration - Complete Workflow

Text extraction is now **automatically integrated** into the CLI! When you run the `generate` command, it will:

1. ✅ Extract text from the PDF using PyMuPDF
2. ✅ Sanitize the text (remove page numbers, headers, DOIs)
3. ✅ Extract figures, tables, and equations
4. ✅ Generate the presentation with LLM
5. ✅ Compile to PDF

## Quick Start

### 1. Install PaperDeck (if not already done)

```bash
cd /Users/jangminsu/Development/paperdeck
pip install -e .
```

### 2. Set up API Key

```bash
# For OpenAI (default)
export OPENAI_API_KEY="your-api-key-here"

# OR pass it via command line
```

### 3. Run the Generate Command

```bash
# Basic usage (text extraction is automatic!)
paperdeck generate path/to/paper.pdf

# With verbose logging to see text extraction in action
paperdeck generate path/to/paper.pdf -v

# Full example with options
paperdeck generate ~/Downloads/paper.pdf \
    --output ./my_presentation \
    --theme Madrid \
    --provider openai \
    --verbose
```

## Command Options

```bash
paperdeck generate [OPTIONS] PDF_PATH

Options:
  -o, --output PATH         Output directory (default: ./paperdeck_output)
  -t, --theme TEXT          Beamer theme (default: Madrid)
  -p, --prompt TEXT         Prompt template (default: default)
  --provider CHOICE         AI provider: openai|anthropic|ollama|lmstudio
  --model TEXT              Specific model (e.g., gpt-4)
  --api-key TEXT            API key (or use environment variable)
  --no-compile              Skip PDF compilation
  -v, --verbose             Enable verbose output (shows text extraction logs)
  --help                    Show help message
```

## Expected Output (Verbose Mode)

When you run with `-v`, you'll see the text extraction happening:

```
Input PDF: paper.pdf
Output directory: ./paperdeck_output
Theme: Madrid
Prompt: default
Provider: openai

INFO - Starting text extraction for paper.pdf...
INFO - Extraction metrics for paper.pdf:
INFO -   Status: success
INFO -   Pages: 12
INFO -   Raw text length: 25,430 chars
INFO -   Clean text length: 24,156 chars
INFO -   Sanitization reduced text by 5.0%
INFO -   Extraction time: 0.52s
INFO - Text extraction successful for paper.pdf: 12 pages, 24156 characters, 0.52s

Generating presentation  [####################################]  4/4

✓ Presentation generated successfully!
  LaTeX file: ./paperdeck_output/paper.tex
  PDF file: ./paperdeck_output/paper.pdf
  Slides: 15
```

## Testing Different Scenarios

### Test 1: Normal PDF (Should Extract Text)

```bash
# Download a test paper from arXiv
curl -o test_paper.pdf "https://arxiv.org/pdf/2301.00001.pdf"

# Generate with verbose logging
paperdeck generate test_paper.pdf -v --no-compile
```

**Expected:** See text extraction logs, successful generation

### Test 2: Encrypted PDF (Should Gracefully Fall Back)

```bash
# If you have an encrypted PDF
paperdeck generate encrypted.pdf -v

# You should see:
# WARNING - Text extraction failed for encrypted.pdf
# WARNING -   Error: PDF is encrypted
# WARNING - Falling back to metadata-only mode
# (Generation continues with metadata only)
```

### Test 3: Missing File (Should Error)

```bash
paperdeck generate nonexistent.pdf -v

# Expected: Clear error message
```

## Verify Text Extraction Worked

After generation, you can verify text was extracted by checking the Paper object would have been populated. The presentation content should reflect the actual paper content, not just metadata.

## Disable Text Extraction (Future)

Currently, text extraction is always enabled. In Phase 5 (User Story 3), we'll add flags:

```bash
# Future: Explicitly disable text extraction
paperdeck generate paper.pdf --no-text

# Future: Set token limit
paperdeck generate paper.pdf --max-tokens 4000
```

## Troubleshooting

### Issue: No text extraction logs visible

**Solution:** Use `-v` flag for verbose mode

```bash
paperdeck generate paper.pdf -v
```

### Issue: "Module not found" error

**Solution:** Reinstall in development mode

```bash
pip install -e .
```

### Issue: Text extraction fails silently

**Solution:** Check logs with verbose mode. The system will gracefully fall back to metadata-only mode and continue generation.

### Issue: PyMuPDF not installed

**Solution:** Install dependencies

```bash
pip install PyMuPDF>=1.23.0
```

## Full Example Session

```bash
# 1. Download a test paper
curl -o ml_paper.pdf "https://arxiv.org/pdf/2010.11929.pdf"

# 2. Generate presentation with verbose logging
paperdeck generate ml_paper.pdf \
    --output ./my_presentation \
    --theme Copenhagen \
    --verbose \
    --no-compile

# 3. Check the output
ls -lh ./my_presentation/
# Should see: ml_paper.tex

# 4. View the LaTeX to confirm it used actual paper content
head -50 ./my_presentation/ml_paper.tex
```

## Integration Details

The CLI now uses `GenerationService.prepare_paper()` which:

1. **Extracts text** from PDF using PyMuPDFTextExtractor
2. **Sanitizes** text using TextSanitizer (removes artifacts)
3. **Logs** extraction status, metrics, and any errors
4. **Falls back** gracefully to metadata-only if extraction fails
5. **Populates** Paper model with text_content field

This happens automatically in `Step 1` of the generation pipeline before element extraction and slide organization.

## Testing Checklist

- [ ] Basic generation works: `paperdeck generate paper.pdf`
- [ ] Verbose mode shows extraction logs: `paperdeck generate paper.pdf -v`
- [ ] Multi-page PDFs extract correctly (10+ pages)
- [ ] Encrypted PDFs fall back gracefully
- [ ] Missing files show clear error messages
- [ ] Generated presentations reflect actual paper content

## Next Steps

After verifying text extraction works via CLI:

1. **Phase 4:** Add token counting and management (so large papers are truncated intelligently)
2. **Phase 5:** Add CLI flags for controlling extraction (`--no-text`, `--max-tokens`)
3. **Phase 6:** Performance testing and documentation
