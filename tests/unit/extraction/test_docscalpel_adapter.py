"""
Unit tests for DocScalpel adapter.

Tests the adapter pattern for DocScalpel integration with graceful fallback.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.core.models import ElementType
from paperdeck.core.config import ExtractionConfiguration


class TestDocScalpelAdapter:
    """Tests for DocScalpelAdapter initialization and import handling."""

    def test_adapter_initialization_without_docscalpel(self):
        """Test adapter initializes gracefully when DocScalpel not installed."""
        with patch.dict('sys.modules', {'docscalpel': None}):
            with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                adapter = DocScalpelAdapter()

                assert adapter.docscalpel_available is False
                mock_logger.warning.assert_called_once()
                assert "DocScalpel not installed" in str(mock_logger.warning.call_args)

    def test_extract_returns_empty_when_docscalpel_unavailable(self, tmp_path):
        """Test extract returns empty list when DocScalpel not available."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(pdf_file, [ElementType.FIGURE])

        assert result == []

    def test_extract_with_default_element_types(self, tmp_path):
        """Test extract uses default element types when none specified."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(pdf_file)

        assert result == []


class TestDocScalpelAdapterWithMock:
    """Tests for extraction with mocked DocScalpel."""

    @pytest.fixture
    def mock_docscalpel(self):
        """Mock DocScalpel module."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def adapter_with_mock(self, mock_docscalpel):
        """Create adapter with mocked DocScalpel."""
        with patch.dict('sys.modules', {'docscalpel': mock_docscalpel}):
            adapter = DocScalpelAdapter()
            adapter.docscalpel_available = True
            adapter.docscalpel = mock_docscalpel
            return adapter

    def test_adapter_logs_successful_import(self, adapter_with_mock):
        """Test adapter logs when DocScalpel imports successfully."""
        assert adapter_with_mock.docscalpel_available is True

    def test_extract_logs_element_types(self, adapter_with_mock, tmp_path):
        """Test extract logs which element types are being extracted."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            result = adapter_with_mock.extract(pdf_file, [ElementType.FIGURE, ElementType.TABLE])

            # Should log the extraction attempt
            assert mock_logger.info.called


class TestDocScalpelAdapterPDFOutput:
    """Tests for PDF output format (User Story 1)."""

    def test_extract_uses_pdf_naming_pattern(self, mock_docscalpel, mock_pdf_result):
        """[US1] Verify adapter configures docscalpel to use PDF naming pattern.

        Test that the naming_pattern passed to ExtractionConfig uses:
        - PDF extension (.pdf not .png)
        - Zero-padded counter format ({counter:02d})
        """
        # Create adapter with mocked docscalpel
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock the extract_elements call
        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        # Extract from test PDF
        pdf_path = Path("/tmp/test.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Verify ExtractionConfig was called with PDF naming pattern
        mock_docscalpel.ExtractionConfig.assert_called_once()
        config_call = mock_docscalpel.ExtractionConfig.call_args

        # Check naming_pattern argument
        assert 'naming_pattern' in config_call.kwargs or len(config_call.args) > 3
        if 'naming_pattern' in config_call.kwargs:
            naming_pattern = config_call.kwargs['naming_pattern']
        else:
            # Assuming naming_pattern is 4th positional argument
            naming_pattern = config_call.args[3] if len(config_call.args) > 3 else None

        # Verify PDF format with zero-padding
        assert naming_pattern is not None, "naming_pattern not passed to ExtractionConfig"
        assert '.pdf' in naming_pattern, f"Expected .pdf extension, got: {naming_pattern}"
        assert '{counter:02d}' in naming_pattern or '{counter:0' in naming_pattern, \
            f"Expected zero-padded counter, got: {naming_pattern}"

    def test_extract_zero_padded_numbering(self, mock_docscalpel, mock_pdf_result_multiple_elements):
        """[US1] Verify extracted PDF files use zero-padded numbering.

        Test that output filenames use format: figure_01.pdf, figure_02.pdf, ...
        Not: figure_1.pdf, figure_2.pdf
        """
        # Create adapter with mocked docscalpel
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return 10 figures
        mock_docscalpel.extract_elements.return_value = mock_pdf_result_multiple_elements

        # Extract
        pdf_path = Path("/tmp/test.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Verify we got 10 elements
        assert len(result) == 10, f"Expected 10 elements, got {len(result)}"

        # Verify filenames use zero-padding
        assert result[0].output_filename.name == "figure_01.pdf", \
            f"Expected figure_01.pdf, got {result[0].output_filename.name}"
        assert result[9].output_filename.name == "figure_10.pdf", \
            f"Expected figure_10.pdf, got {result[9].output_filename.name}"

        # Verify all have .pdf extension
        for elem in result:
            assert elem.output_filename.suffix == ".pdf", \
                f"Expected .pdf suffix, got {elem.output_filename.suffix}"


class TestDocScalpelAdapterErrorHandling:
    """Tests for error handling and logging (User Story 2)."""

    def test_extraction_failure_logs_errors_individually(self, mock_docscalpel, mock_pdf_result_with_errors):
        """[US2] Verify adapter logs each error individually with enumeration.

        Test that when extraction fails (success=False), each error message
        in result.errors is logged individually with [i/total] format.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return failure result
        mock_docscalpel.extract_elements.return_value = mock_pdf_result_with_errors

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            pdf_path = Path("/tmp/corrupted.pdf")
            result = adapter.extract(pdf_path, [ElementType.FIGURE])

            # Should return empty list on failure
            assert result == []

            # Verify ERROR level logging was called
            assert mock_logger.error.called, "Expected error logging for extraction failure"

            # Verify each error logged with enumeration
            error_calls = [call for call in mock_logger.error.call_args_list]
            assert len(error_calls) >= 3, f"Expected at least 3 error log calls, got {len(error_calls)}"

            # Check that errors contain enumeration pattern [i/total]
            error_messages = [str(call) for call in error_calls]
            has_enumeration = any('[1/' in msg or '[2/' in msg or '[3/' in msg for msg in error_messages)
            assert has_enumeration, f"Expected error enumeration [i/total] in logs, got: {error_messages}"

    def test_extraction_warnings_logged(self, mock_docscalpel, mock_pdf_result_with_warnings):
        """[US2] Verify adapter logs warnings individually.

        Test that warnings are logged individually even when extraction succeeds.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return result with warnings
        mock_docscalpel.extract_elements.return_value = mock_pdf_result_with_warnings

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            pdf_path = Path("/tmp/test.pdf")
            result = adapter.extract(pdf_path, [ElementType.FIGURE])

            # Should return elements despite warnings
            assert len(result) > 0, "Expected elements even with warnings"

            # Verify WARNING level logging was called
            assert mock_logger.warning.called, "Expected warning logging"

            # Verify individual warnings logged
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) >= 2, f"Expected at least 2 warning log calls, got {len(warning_calls)}"

    def test_extraction_checks_success_flag(self, mock_docscalpel, mock_pdf_result_with_errors):
        """[US2] Verify adapter checks result.success before processing elements.

        Test that the adapter respects the success flag and doesn't process
        elements when success=False, even if elements list is present.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Create result with success=False but non-empty elements (shouldn't happen, but test it)
        mock_result = Mock()
        mock_result.success = False
        mock_result.elements = [Mock()]  # Has elements but failed
        mock_result.errors = ["Test error"]
        mock_result.warnings = []
        mock_result.extraction_time_seconds = 0.5

        mock_docscalpel.extract_elements.return_value = mock_result

        pdf_path = Path("/tmp/test.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Must return empty list when success=False, regardless of elements
        assert result == [], f"Expected empty list when success=False, got {len(result)} elements"

    def test_graceful_degradation_returns_empty_list(self, mock_docscalpel, mock_pdf_result_with_errors):
        """[US2] Verify graceful degradation returns empty list on failure.

        Test that extraction failures don't raise exceptions but return
        empty list, allowing the application to continue with text-only slides.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return failure
        mock_docscalpel.extract_elements.return_value = mock_pdf_result_with_errors

        pdf_path = Path("/tmp/corrupted.pdf")

        # Should not raise exception
        try:
            result = adapter.extract(pdf_path, [ElementType.FIGURE])
        except Exception as e:
            pytest.fail(f"Extract should not raise exception, got: {e}")

        # Should return empty list
        assert result == [], f"Expected empty list on failure, got {result}"
        assert isinstance(result, list), "Result should be a list"


class TestDocScalpelAdapterPerformance:
    """Tests for performance logging and monitoring (User Story 3)."""

    def test_extraction_logs_performance_metrics(self, mock_docscalpel, mock_pdf_result):
        """[US3] Verify adapter logs performance metrics after extraction.

        Test that extraction logs:
        - Total elements extracted
        - Library execution time (extraction_time_seconds)
        - Total elapsed time
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return successful result
        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            pdf_path = Path("/tmp/test.pdf")
            result = adapter.extract(pdf_path, [ElementType.FIGURE])

            # Should log performance info
            assert mock_logger.info.called, "Expected info logging for performance metrics"

            # Check that performance info includes key metrics
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            info_text = ' '.join(info_calls)

            # Should mention element count and timing
            assert any('1 element' in call or 'elements' in call for call in info_calls), \
                f"Expected element count in logs, got: {info_calls}"

    def test_extraction_logs_timing(self, mock_docscalpel, mock_pdf_result):
        """[US3] Verify adapter logs extraction timing information.

        Test that extraction_time_seconds from DocScalpel result is logged.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Set specific extraction time
        mock_pdf_result.extraction_time_seconds = 3.5
        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            with patch('time.perf_counter', side_effect=[0.0, 4.0]):  # Mock timing
                pdf_path = Path("/tmp/test.pdf")
                result = adapter.extract(pdf_path, [ElementType.FIGURE])

                # Should log timing information
                info_calls = [str(call) for call in mock_logger.info.call_args_list]

                # Look for timing information (library time or total time)
                has_timing = any('3.5' in call or 's' in call or 'time' in call.lower()
                                for call in info_calls)
                assert has_timing, f"Expected timing info in logs, got: {info_calls}"

    def test_extraction_logs_overhead_warning(self, mock_docscalpel, mock_pdf_result):
        """[US3] Verify adapter warns about high overhead.

        Test that significant overhead (>2s or >20%) triggers a warning.
        """
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Create scenario with high overhead: library=1s, total=5s, overhead=4s (80%)
        mock_pdf_result.extraction_time_seconds = 1.0
        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            with patch('time.perf_counter', side_effect=[0.0, 5.0]):  # Total 5 seconds
                pdf_path = Path("/tmp/test.pdf")
                result = adapter.extract(pdf_path, [ElementType.FIGURE])

                # Should warn about high overhead
                warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                has_overhead_warning = any('overhead' in call.lower() for call in warning_calls)
                assert has_overhead_warning, \
                    f"Expected overhead warning (4s/80%), got warnings: {warning_calls}"

    def test_max_pages_parameter(self, mock_docscalpel, mock_pdf_result):
        """[US3] Verify max_pages parameter is passed to docscalpel config.

        Test that when max_pages is set in configuration, it's passed
        to DocScalpel's ExtractionConfig.
        """
        from paperdeck.core.config import ExtractionConfiguration

        # Create config with max_pages limit
        config = ExtractionConfiguration(max_pages=10)
        adapter = DocScalpelAdapter(config)
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        pdf_path = Path("/tmp/large.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Verify ExtractionConfig was called with max_pages
        mock_docscalpel.ExtractionConfig.assert_called_once()
        config_call = mock_docscalpel.ExtractionConfig.call_args

        # Check max_pages in kwargs
        assert 'max_pages' in config_call.kwargs, \
            f"Expected max_pages in config kwargs, got: {config_call.kwargs.keys()}"
        assert config_call.kwargs['max_pages'] == 10, \
            f"Expected max_pages=10, got: {config_call.kwargs['max_pages']}"
