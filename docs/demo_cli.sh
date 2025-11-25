#!/bin/bash
# Demo script for testing CLI with text extraction

set -e

echo "=========================================="
echo "PaperDeck CLI Demo - Text Extraction Test"
echo "=========================================="
echo ""

# Check if a PDF is provided
if [ -z "$1" ]; then
    echo "Usage: ./demo_cli.sh <path_to_pdf>"
    echo ""
    echo "Example:"
    echo "  ./demo_cli.sh ~/Downloads/paper.pdf"
    echo ""
    echo "Or download a test paper:"
    echo "  curl -o test_paper.pdf https://arxiv.org/pdf/2301.00001.pdf"
    echo "  ./demo_cli.sh test_paper.pdf"
    exit 1
fi

PDF_FILE="$1"

if [ ! -f "$PDF_FILE" ]; then
    echo "❌ Error: PDF file not found: $PDF_FILE"
    exit 1
fi

echo "📄 PDF File: $PDF_FILE"
echo ""

# Check if paperdeck is installed
if ! command -v paperdeck &> /dev/null; then
    echo "⚠️  paperdeck command not found. Installing in development mode..."
    pip install -e .
    echo ""
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
    echo "   Or pass via --api-key flag"
    echo ""
fi

echo "🚀 Running paperdeck generate with verbose logging..."
echo "   (This will show text extraction in action)"
echo ""
echo "Command:"
echo "  paperdeck generate \"$PDF_FILE\" --no-compile --verbose"
echo ""
echo "Press Enter to continue..."
read

# Run the command
paperdeck generate "$PDF_FILE" \
    --output ./demo_output \
    --theme Madrid \
    --no-compile \
    --verbose

echo ""
echo "=========================================="
echo "✅ Demo Complete!"
echo "=========================================="
echo ""
echo "Check the generated LaTeX file:"
echo "  cat ./demo_output/$(basename ${PDF_FILE%.pdf}).tex"
echo ""
echo "The presentation should include content from the paper text,"
echo "not just metadata!"
