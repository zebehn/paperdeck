#!/usr/bin/env python
"""
Simple interactive test for text extraction.

This script provides a quick way to test extraction on any PDF.
"""

from pathlib import Path
from src.paperdeck.extraction.text_extractor import PyMuPDFTextExtractor
from src.paperdeck.core.config import TextExtractionConfig

def quick_test(pdf_path: str):
    """Quick test of text extraction."""

    # Create extractor
    extractor = PyMuPDFTextExtractor()

    # Create config
    config = TextExtractionConfig(
        enabled=True,
        remove_page_numbers=True,
        remove_headers_footers=True,
    )

    # Extract
    print(f"\n🔍 Extracting from: {pdf_path}")
    result = extractor.extract(Path(pdf_path), config)

    # Show results
    print(f"\n✅ Status: {result.status.value}")
    print(f"📄 Pages: {result.page_count}")
    print(f"📝 Text length: {result.clean_text_length} characters")
    print(f"⏱️  Time: {result.extraction_time_seconds:.2f}s")

    if result.text_content:
        print(f"\n📖 First 300 characters:")
        print("-" * 60)
        print(result.text_content[:300])
        print("-" * 60)

    return result

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_extraction_simple.py <pdf_path>")
        print("\nExample:")
        print("  python test_extraction_simple.py paper.pdf")
    else:
        quick_test(sys.argv[1])
