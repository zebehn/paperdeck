#!/usr/bin/env python
"""Advanced usage example for PaperDeck.

This example demonstrates advanced features:
- Custom configuration
- Multiple AI providers
- Custom prompts
- Error handling
- Progress tracking
"""

import sys
from pathlib import Path
from paperdeck.cli.commands import generate_presentation
from paperdeck.core.config import (
    AppConfiguration,
    AIServiceConfiguration,
    ExtractionConfiguration,
)
from paperdeck.core.exceptions import PaperDeckError
from paperdeck.core.models import ElementType

def progress_callback():
    """Custom progress callback."""
    print(".", end="", flush=True)

def generate_with_custom_config(pdf_path: Path, provider: str = "openai"):
    """Generate presentation with custom configuration.

    Args:
        pdf_path: Path to PDF file
        provider: AI provider to use (openai, anthropic, ollama, lmstudio)
    """

    # Custom extraction configuration
    extraction_config = ExtractionConfiguration(
        confidence_threshold=0.8,  # Higher confidence threshold
        element_types=[ElementType.FIGURE, ElementType.TABLE],  # Only figures and tables
        max_pages=50,  # Limit to first 50 pages
        output_directory=Path("./extracted_elements"),
    )

    # Custom AI service configuration
    ai_config = AIServiceConfiguration(
        default_provider=provider,
        max_retries=5,  # More retries
        timeout_seconds=120,  # Longer timeout
    )

    # Set API keys based on provider
    if provider == "openai":
        import os
        ai_config.openai_api_key = os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        import os
        ai_config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # Application configuration
    config = AppConfiguration(
        ai_services=ai_config,
        extraction_config=extraction_config,
        output_directory=Path("./presentations"),
        log_level="DEBUG",  # Verbose logging
    )

    return config

def main():
    """Main execution function."""

    # Example 1: Generate with OpenAI (default)
    print("Example 1: Using OpenAI GPT-4")
    print("-" * 50)

    pdf_path = Path("path/to/paper.pdf")

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        print("\nPlease update the pdf_path in this script to point to a real PDF file.")
        sys.exit(1)

    try:
        config = generate_with_custom_config(pdf_path, provider="openai")

        result = generate_presentation(
            pdf_path=pdf_path,
            config=config,
            theme="Copenhagen",  # Different theme
            prompt_name="technical",  # Technical presentation
            model="gpt-4",  # Specific model
            compile_pdf=True,
            progress_callback=progress_callback,
        )

        print(f"\n✅ Generated: {result['tex_path']}")

    except PaperDeckError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    # Example 2: Generate with local Ollama (no API key needed)
    print("\n\nExample 2: Using Ollama (local)")
    print("-" * 50)

    try:
        config = generate_with_custom_config(pdf_path, provider="ollama")

        result = generate_presentation(
            pdf_path=pdf_path,
            config=config,
            theme="Berlin",
            prompt_name="accessible",  # Accessible presentation
            model="llama2",  # Local model
            compile_pdf=False,  # Don't compile to PDF
            progress_callback=progress_callback,
        )

        print(f"\n✅ Generated: {result['tex_path']}")
        print("   (LaTeX only, PDF compilation skipped)")

    except PaperDeckError as e:
        print(f"\n❌ Error: {e}")
        print("   Note: Ollama must be running locally")

    # Example 3: Batch processing multiple papers
    print("\n\nExample 3: Batch processing")
    print("-" * 50)

    papers = [
        # Add your paper paths here
        # Path("paper1.pdf"),
        # Path("paper2.pdf"),
        # Path("paper3.pdf"),
    ]

    if not papers:
        print("No papers configured for batch processing")
        print("Update the 'papers' list in this script to enable batch processing")
    else:
        config = generate_with_custom_config(papers[0], provider="openai")

        for i, paper_path in enumerate(papers, 1):
            print(f"\nProcessing {i}/{len(papers)}: {paper_path.name}")

            try:
                result = generate_presentation(
                    pdf_path=paper_path,
                    config=config,
                    theme="Madrid",
                    prompt_name="default",
                    compile_pdf=True,
                    progress_callback=progress_callback,
                )

                print(f" ✅ Success")

            except PaperDeckError as e:
                print(f" ❌ Failed: {e}")
                continue

if __name__ == "__main__":
    main()
