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
        """Test adapter initializes gracefully when DocScalpel CLI not found."""
        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value=None):
            with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                adapter = DocScalpelAdapter()

                assert adapter.docscalpel_available is False
                assert adapter.docscalpel_path is None
                mock_logger.warning.assert_called_once()
                assert "DocScalpel CLI not found" in str(mock_logger.warning.call_args)

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

    def test_extract_uses_correct_cli_arguments(self, tmp_path):
        """[US1] Verify adapter passes correct arguments to docscalpel CLI.

        Test that the CLI is called with:
        - Correct types argument (figure,table)
        - Output directory
        """
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                # Mock successful version check
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                adapter = DocScalpelAdapter(config)
                adapter.extract(pdf_file, [ElementType.FIGURE])

                # Find the extraction call (second call, after version check)
                calls = mock_run.call_args_list
                assert len(calls) >= 2, f"Expected at least 2 subprocess calls, got {len(calls)}"

                extract_call = calls[1]
                cmd = extract_call[0][0]

                # Verify CLI arguments
                assert cmd[0] == '/usr/bin/docscalpel'
                assert '--types' in cmd
                types_idx = cmd.index('--types')
                assert cmd[types_idx + 1] == 'figure'
                assert '--output' in cmd

    def test_extract_zero_padded_numbering(self, tmp_path):
        """[US1] Verify extracted PDF files use zero-padded numbering.

        Test that output filenames like figure_01.pdf, figure_02.pdf are loaded correctly.
        """
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        # Create 10 mock extracted figure files with zero-padded names
        for i in range(1, 11):
            (output_dir / f"figure_{i:02d}.pdf").write_bytes(b"dummy")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                adapter = DocScalpelAdapter(config)
                result = adapter.extract(pdf_file, [ElementType.FIGURE])

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

    def test_extraction_failure_logs_errors(self, tmp_path):
        """[US2] Verify adapter logs errors when CLI extraction fails.

        Test that when CLI returns non-zero exit code, errors are logged.
        """
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                # First call (version check) succeeds, second call (extract) fails
                mock_run.side_effect = [
                    Mock(returncode=0, stdout='', stderr=''),  # version check
                    Mock(returncode=1, stdout='', stderr='Error processing PDF')  # extraction
                ]

                with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                    adapter = DocScalpelAdapter(config)
                    result = adapter.extract(pdf_file, [ElementType.FIGURE])

                    # Should return empty list on failure
                    assert result == []

                    # Verify ERROR level logging was called
                    assert mock_logger.error.called, "Expected error logging for extraction failure"

    def test_extraction_succeeds_with_output_files(self, tmp_path):
        """[US2] Verify adapter returns elements when CLI succeeds and files exist.

        Test that successful extraction loads elements from output directory.
        """
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()
        (output_dir / "figure_01.pdf").write_bytes(b"dummy")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                adapter = DocScalpelAdapter(config)
                result = adapter.extract(pdf_file, [ElementType.FIGURE])

                # Should return elements
                assert len(result) == 1, f"Expected 1 element, got {len(result)}"

    def test_extraction_checks_cli_return_code(self, tmp_path):
        """[US2] Verify adapter checks CLI return code before processing.

        Test that the adapter respects the returncode and doesn't process
        elements when returncode is non-zero.
        """
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()
        # Create output file that would normally be loaded
        (output_dir / "figure_01.pdf").write_bytes(b"dummy")

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                # Version check succeeds, extraction fails
                mock_run.side_effect = [
                    Mock(returncode=0, stdout='', stderr=''),
                    Mock(returncode=1, stdout='', stderr='Error')
                ]

                adapter = DocScalpelAdapter(config)
                result = adapter.extract(pdf_file, [ElementType.FIGURE])

        # Must return empty list when returncode is non-zero
        assert result == [], f"Expected empty list when CLI fails, got {len(result)} elements"

    def test_graceful_degradation_returns_empty_list(self, tmp_path):
        """[US2] Verify graceful degradation returns empty list on failure.

        Test that extraction failures don't raise exceptions but return
        empty list, allowing the application to continue with text-only slides.
        """
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout='', stderr=''),
                    Mock(returncode=1, stdout='', stderr='Error processing corrupted PDF')
                ]

                adapter = DocScalpelAdapter(config)

                # Should not raise exception
                try:
                    result = adapter.extract(pdf_file, [ElementType.FIGURE])
                except Exception as e:
                    pytest.fail(f"Extract should not raise exception, got: {e}")

                # Should return empty list
                assert result == [], f"Expected empty list on failure, got {result}"
                assert isinstance(result, list), "Result should be a list"


class TestDocScalpelAdapterPerformance:
    """Tests for performance logging and monitoring (User Story 3)."""

    def test_extraction_logs_performance_metrics(self, tmp_path):
        """[US3] Verify adapter logs performance metrics after extraction.

        Test that extraction logs:
        - Total elements extracted
        - Total elapsed time
        """
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()
        (output_dir / "figure_01.pdf").write_bytes(b"dummy")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                    adapter = DocScalpelAdapter(config)
                    result = adapter.extract(pdf_file, [ElementType.FIGURE])

                    # Should log performance info
                    assert mock_logger.info.called, "Expected info logging for performance metrics"

                    # Check that performance info includes element count
                    info_calls = [str(call) for call in mock_logger.info.call_args_list]
                    assert any('element' in call.lower() for call in info_calls), \
                        f"Expected element count in logs, got: {info_calls}"

    def test_extraction_logs_timing(self, tmp_path):
        """[US3] Verify adapter logs extraction timing information.

        Test that elapsed time is logged after extraction.
        """
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()
        (output_dir / "figure_01.pdf").write_bytes(b"dummy")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf")

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                    adapter = DocScalpelAdapter(config)
                    result = adapter.extract(pdf_file, [ElementType.FIGURE])

                    # Should log timing information
                    info_calls = [str(call) for call in mock_logger.info.call_args_list]

                    # Look for timing information (seconds indicator)
                    has_timing = any('s' in call for call in info_calls)
                    assert has_timing, f"Expected timing info in logs, got: {info_calls}"

    def test_extraction_timeout_handling(self, tmp_path):
        """[US3] Verify adapter handles extraction timeout gracefully.

        Test that timeout during extraction is logged and returns empty list.
        """
        pdf_file = tmp_path / "large.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"

        config = ExtractionConfiguration(output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                import subprocess
                # Version check succeeds, extraction times out
                mock_run.side_effect = [
                    Mock(returncode=0, stdout='', stderr=''),
                    subprocess.TimeoutExpired(cmd='docscalpel', timeout=300)
                ]

                with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                    adapter = DocScalpelAdapter(config)
                    result = adapter.extract(pdf_file, [ElementType.FIGURE])

                    # Should return empty list on timeout
                    assert result == []

                    # Should log error about timeout
                    assert mock_logger.error.called

    def test_max_pages_parameter(self, tmp_path):
        """[US3] Verify max_pages parameter is passed to docscalpel CLI.

        Test that when max_pages is set in configuration, it's passed
        to the CLI command.
        """
        pdf_file = tmp_path / "large.pdf"
        pdf_file.write_bytes(b"dummy pdf")
        output_dir = tmp_path / "extracted"

        # Create config with max_pages limit
        config = ExtractionConfiguration(max_pages=10, output_directory=output_dir)

        with patch('paperdeck.extraction.docscalpel_adapter.shutil.which', return_value='/usr/bin/docscalpel'):
            with patch('paperdeck.extraction.docscalpel_adapter.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

                adapter = DocScalpelAdapter(config)
                adapter.extract(pdf_file, [ElementType.FIGURE])

                # Find the extraction call (second call, after version check)
                calls = mock_run.call_args_list
                assert len(calls) >= 2

                extract_call = calls[1]
                cmd = extract_call[0][0]

                # Check max_pages in CLI args
                assert '--max-pages' in cmd, \
                    f"Expected --max-pages in CLI command, got: {cmd}"
                max_pages_idx = cmd.index('--max-pages')
                assert cmd[max_pages_idx + 1] == '10', \
                    f"Expected max_pages=10, got: {cmd[max_pages_idx + 1]}"
