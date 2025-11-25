#!/usr/bin/env python
"""Basic usage example for PaperDeck.

This example demonstrates the most common use case: generating a presentation
from a PDF research paper using default settings.
"""

from pathlib import Path
from paperdeck.cli.commands import generate_presentation
from paperdeck.core.config import AppConfiguration, AIServiceConfiguration

def main():
    """Generate a presentation with default settings."""

    # Path to your PDF paper
    pdf_path = Path("path/to/your/paper.pdf")

    # Create configuration
    # Note: Set your API key via environment variable OPENAI_API_KEY
    # or pass it directly here
    ai_config = AIServiceConfiguration(
        default_provider="openai",
        # openai_api_key="sk-...",  # Uncomment and add your key
    )

    config = AppConfiguration(
        ai_services=ai_config,
        output_directory=Path("./output"),
    )

    # Generate presentation
    print(f"Generating presentation from {pdf_path}...")

    result = generate_presentation(
        pdf_path=pdf_path,
        config=config,
        theme="Madrid",
        prompt_name="default",
        compile_pdf=True,
    )

    # Print results
    print(f"\n✅ Presentation generated successfully!")
    print(f"   LaTeX file: {result['tex_path']}")
    if result.get('pdf_path'):
        print(f"   PDF file: {result['pdf_path']}")
    print(f"   Total slides: {result['slide_count']}")

if __name__ == "__main__":
    main()
