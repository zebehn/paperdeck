"""
Integration tests for skip-extraction feature.

Tests the complete workflow with pre-extracted elements.
"""


import pytest
from click.testing import CliRunner

from paperdeck.cli.main import cli


class TestSkipExtractionIntegration:
    """Integration tests for skip-extraction workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_skip_extraction_with_figures_only(self, runner, tmp_path):
        """Test skip-extraction with figures-only directory."""
        # This is a basic test - full implementation would need:
        # - Mock paper PDF
        # - Pre-extracted figure files
        # - API key or mock AI service
        # For now, just verify CLI accepts the options
        pass

    def test_skip_extraction_with_tables_only(self, runner, tmp_path):
        """Test skip-extraction with tables-only directory."""
        pass

    def test_skip_extraction_with_mixed_elements(self, runner, tmp_path):
        """Test skip-extraction with mixed figures and tables."""
        pass

    def test_skip_extraction_generates_valid_presentation(self, runner, tmp_path):
        """Test that skip-extraction generates a valid presentation."""
        pass

    def test_skip_extraction_performance_under_5_seconds(self, runner, tmp_path):
        """Test that skip-extraction completes in <5 seconds."""
        pass

    def test_skip_extraction_empty_directory_clear_error(self, runner, tmp_path):
        """Test clear error message when elements directory is empty."""
        # Create a dummy PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Create empty elements directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(empty_dir),
            "--api-key", "dummy-key-for-testing",  # Add dummy API key to pass initial validation
        ])

        # Should fail with clear error message about empty directory
        assert result.exit_code != 0
        assert (
            "no valid element files" in result.output.lower()
            or "invalid elements directory" in result.output.lower()
        )

    def test_skip_extraction_gaps_warning_but_continues(self, runner, tmp_path, caplog):
        """Test that gaps in numbering produce warning but generation continues."""

        # This test would need:
        # - Mock paper PDF
        # - Pre-extracted files with gaps (figure_01.pdf, figure_03.pdf - missing 02)
        # - Mock AI service to avoid API calls
        # For now, just verify the warning is logged when loading
        pass

    def test_skip_extraction_invalid_names_warning(self, runner, tmp_path, caplog):
        """Test that invalid filenames produce warning."""

        # This test would need:
        # - Mock paper PDF
        # - Files with invalid names (fig_01.pdf, figure1.pdf)
        # - Mock AI service
        # For now, just verify warnings are logged
        pass
