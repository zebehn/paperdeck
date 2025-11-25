#!/usr/bin/env python
"""
Manual test script for text extraction functionality.

Usage:
    python test_extraction_manual.py <path_to_pdf>

Example:
    python test_extraction_manual.py ~/Downloads/paper.pdf
"""

import sys
import logging
from pathlib import Path

# Setup logging to see extraction details
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from src.paperdeck.core.config import AppConfiguration, TextExtractionConfig
from src.paperdeck.services.generation_service import GenerationService


def test_text_extraction(pdf_path: str):
    """Test text extraction on a real PDF file."""

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Testing text extraction on: {pdf_file.name}")
    print(f"{'='*60}\n")

    # Create configuration
    config = AppConfiguration()
    config.text_extraction = TextExtractionConfig(
        enabled=True,
        remove_page_numbers=True,
        remove_headers_footers=True,
        min_line_length=3,
    )

    # Create service
    service = GenerationService(config)

    # Extract text
    print("🔄 Extracting text from PDF...\n")
    paper = service.prepare_paper(pdf_file)

    # Display results
    print(f"\n{'='*60}")
    print("EXTRACTION RESULTS")
    print(f"{'='*60}\n")

    print(f"📄 File: {paper.file_path.name}")
    print(f"✅ Has text content: {paper.has_text_content}")
    print(f"📊 Extraction status: {paper.text_extraction_status.value}")

    if paper.has_text_content:
        result = paper.text_extraction_result
        print(f"\n📈 Extraction Metrics:")
        print(f"  • Pages processed: {result.page_count}")
        print(f"  • Raw text length: {result.raw_text_length:,} characters")
        print(f"  • Clean text length: {result.clean_text_length:,} characters")
        print(f"  • Sanitization reduced by: {result.sanitization_reduction_pct:.1f}%")
        print(f"  • Extraction time: {result.extraction_time_seconds:.2f} seconds")

        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")

        # Show preview of extracted text
        print(f"\n📝 Text Preview (first 500 characters):")
        print(f"{'-'*60}")
        print(paper.text_content[:500])
        if len(paper.text_content) > 500:
            print("...")
        print(f"{'-'*60}")

        # Show last 200 characters
        print(f"\n📝 Text Preview (last 200 characters):")
        print(f"{'-'*60}")
        print("...")
        print(paper.text_content[-200:])
        print(f"{'-'*60}")

    else:
        print(f"\n❌ Extraction failed or no text content")
        if paper.text_extraction_result:
            result = paper.text_extraction_result
            if result.error_message:
                print(f"  • Error: {result.error_message}")

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}\n")


def test_with_different_configs(pdf_path: str):
    """Test extraction with different configuration options."""

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    configs = [
        ("Default (with sanitization)", TextExtractionConfig(
            enabled=True,
            remove_page_numbers=True,
            remove_headers_footers=True,
        )),
        ("No sanitization", TextExtractionConfig(
            enabled=True,
            remove_page_numbers=False,
            remove_headers_footers=False,
        )),
        ("Aggressive sanitization", TextExtractionConfig(
            enabled=True,
            remove_page_numbers=True,
            remove_headers_footers=True,
            min_line_length=10,  # Remove lines shorter than 10 chars
        )),
    ]

    print(f"\n{'='*60}")
    print(f"Testing different configurations on: {pdf_file.name}")
    print(f"{'='*60}\n")

    config = AppConfiguration()
    service = GenerationService(config)

    for name, extraction_config in configs:
        print(f"\n📋 Configuration: {name}")
        print(f"{'-'*60}")

        paper = service.prepare_paper(pdf_file, extraction_config=extraction_config)

        if paper.has_text_content:
            result = paper.text_extraction_result
            print(f"  • Clean text length: {result.clean_text_length:,} chars")
            print(f"  • Sanitization reduction: {result.sanitization_reduction_pct:.1f}%")
            print(f"  • Preview: {paper.text_content[:100]}...")
        else:
            print(f"  • ❌ No text extracted")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extraction_manual.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_extraction_manual.py ~/Downloads/paper.pdf")
        print("\nOptions:")
        print("  --compare    Test with different configurations")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--compare":
        test_with_different_configs(pdf_path)
    else:
        test_text_extraction(pdf_path)
