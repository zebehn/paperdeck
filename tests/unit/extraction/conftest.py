"""Fixtures for extraction unit tests."""

import pytest
from unittest.mock import Mock
from pathlib import Path


@pytest.fixture
def mock_pdf_element(mock_docscalpel):
    """Create a mock docscalpel Element with PDF output.

    Args:
        mock_docscalpel: Mock docscalpel module fixture

    Returns:
        Mock Element object configured with PDF output path
    """
    mock_elem = Mock()
    mock_elem.element_type = mock_docscalpel.ElementType.FIGURE
    mock_elem.page_number = 1
    mock_elem.sequence_number = 1
    mock_elem.confidence_score = 0.95
    mock_elem.element_id = "fig_001"
    mock_elem.bounding_box = Mock(x=100, y=100, width=200, height=150)
    mock_elem.output_filename = "extracted/figure_01.pdf"  # PDF format with zero-padding
    return mock_elem


@pytest.fixture
def mock_pdf_result(mock_pdf_element):
    """Create a mock ExtractionResult with PDF outputs.

    Args:
        mock_pdf_element: Mock element fixture

    Returns:
        Mock ExtractionResult from docscalpel v1.0.0
    """
    mock_result = Mock()
    mock_result.success = True
    mock_result.elements = [mock_pdf_element]
    mock_result.errors = []
    mock_result.warnings = []
    mock_result.extraction_time_seconds = 2.5
    mock_result.figure_count = 1
    mock_result.table_count = 0
    mock_result.total_elements = 1
    mock_result.output_directory = "extracted"
    return mock_result


@pytest.fixture
def mock_pdf_result_multiple_elements(mock_docscalpel):
    """Create a mock ExtractionResult with multiple PDF elements.

    Args:
        mock_docscalpel: Mock docscalpel module fixture

    Returns:
        Mock ExtractionResult with 10 figures (testing zero-padding)
    """
    mock_elements = []

    # Create 10 figure elements to test zero-padding
    for i in range(1, 11):
        mock_elem = Mock()
        mock_elem.element_type = mock_docscalpel.ElementType.FIGURE
        mock_elem.page_number = i
        mock_elem.sequence_number = i
        mock_elem.confidence_score = 0.9
        mock_elem.element_id = f"fig_{i:03d}"
        mock_elem.bounding_box = Mock(x=100, y=100, width=200, height=150)
        mock_elem.output_filename = f"extracted/figure_{i:02d}.pdf"  # Zero-padded
        mock_elements.append(mock_elem)

    mock_result = Mock()
    mock_result.success = True
    mock_result.elements = mock_elements
    mock_result.errors = []
    mock_result.warnings = []
    mock_result.extraction_time_seconds = 5.0
    mock_result.figure_count = 10
    mock_result.table_count = 0
    mock_result.total_elements = 10
    mock_result.output_directory = "extracted"
    return mock_result


@pytest.fixture
def mock_pdf_result_with_errors():
    """Create a mock ExtractionResult with extraction failures.

    Returns:
        Mock ExtractionResult with success=False and error messages
    """
    mock_result = Mock()
    mock_result.success = False
    mock_result.elements = []
    mock_result.errors = [
        "Corrupted PDF structure on page 3",
        "Failed to decode image stream at offset 12345",
        "Invalid bounding box coordinates"
    ]
    mock_result.warnings = []
    mock_result.extraction_time_seconds = 0.5
    mock_result.figure_count = 0
    mock_result.table_count = 0
    mock_result.total_elements = 0
    mock_result.output_directory = "extracted"
    return mock_result


@pytest.fixture
def mock_pdf_result_with_warnings(mock_pdf_element):
    """Create a mock ExtractionResult with warnings.

    Args:
        mock_pdf_element: Mock element fixture

    Returns:
        Mock ExtractionResult with success=True but warnings present
    """
    mock_result = Mock()
    mock_result.success = True
    mock_result.elements = [mock_pdf_element]
    mock_result.errors = []
    mock_result.warnings = [
        "Low confidence score (0.65) for element on page 2",
        "Unusual aspect ratio detected for table on page 5"
    ]
    mock_result.extraction_time_seconds = 3.0
    mock_result.figure_count = 1
    mock_result.table_count = 0
    mock_result.total_elements = 1
    mock_result.output_directory = "extracted"
    return mock_result


@pytest.fixture
def mock_docscalpel():
    """Create a mock docscalpel module for testing.

    Returns:
        Mock docscalpel module with ExtractionConfig and ElementType
    """
    mock_ds = Mock()

    # Mock ElementType enum
    mock_ds.ElementType = Mock()
    mock_ds.ElementType.FIGURE = Mock(name="FIGURE")
    mock_ds.ElementType.TABLE = Mock(name="TABLE")
    mock_ds.ElementType.EQUATION = Mock(name="EQUATION")

    # Mock ExtractionConfig
    mock_ds.ExtractionConfig = Mock(return_value=Mock())

    # Mock extract_elements function
    mock_ds.extract_elements = Mock()

    return mock_ds
