"""
Unit tests for CLI skip-extraction option validation.

Tests CLI argument validation and error messages for skip-extraction feature.
"""


import pytest
from click.testing import CliRunner

from paperdeck.cli.main import cli


class TestSkipExtractionCLIValidation:
    """Tests for User Story 2: CLI error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_skip_extraction_without_input_dir_uses_default(self, runner, tmp_path):
        """CLI uses default directory when --skip-extraction used without --elements-input-dir."""
        # Create a dummy PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--api-key", "dummy-key",
        ])

        # Should fail because default directory doesn't exist, not because option is required
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()
        # Should NOT say the option is required
        assert "--elements-input-dir is required" not in result.output

    def test_skip_extraction_nonexistent_dir_fails(self, runner, tmp_path):
        """CLI fails with clear error when --elements-input-dir points to nonexistent directory."""
        # Create a dummy PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Point to nonexistent directory
        nonexistent_dir = tmp_path / "does_not_exist"

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(nonexistent_dir),
        ])

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()

    def test_skip_extraction_file_not_directory_fails(self, runner, tmp_path):
        """CLI fails when --elements-input-dir points to a file, not directory."""
        # Create a dummy PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Create a file (not directory)
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(file_path),
        ])

        assert result.exit_code != 0
        assert "not a directory" in result.output.lower()


class TestSkipExtractionPathHandling:
    """Tests for User Story 3: Path flexibility."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_skip_extraction_relative_path(self, runner, tmp_path):
        """CLI accepts relative path for --elements-input-dir."""
        # Create test structure
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        elements_dir = tmp_path / "extracted"
        elements_dir.mkdir()
        (elements_dir / "figure_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Use relative path
        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(elements_dir),
            "--api-key", "dummy-key",
        ])

        # Should not fail due to path format
        # (may fail later due to mock AI service, but path should be accepted)
        assert "does not exist" not in result.output.lower()

    def test_skip_extraction_absolute_path(self, runner, tmp_path):
        """CLI accepts absolute path for --elements-input-dir."""
        # Create test structure
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        elements_dir = tmp_path / "extracted"
        elements_dir.mkdir()
        (elements_dir / "figure_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Use absolute path
        absolute_dir = elements_dir.resolve()

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(absolute_dir),
            "--api-key", "dummy-key",
        ])

        # Should not fail due to path format
        assert "does not exist" not in result.output.lower()

    def test_skip_extraction_path_with_spaces(self, runner, tmp_path):
        """CLI accepts paths with spaces for --elements-input-dir."""
        # Create test structure
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        elements_dir = tmp_path / "extracted with spaces"
        elements_dir.mkdir()
        (elements_dir / "figure_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--skip-extraction",
            "--elements-input-dir", str(elements_dir),
            "--api-key", "dummy-key",
        ])

        # Should not fail due to path format
        assert "does not exist" not in result.output.lower()

    def test_skip_extraction_default_directory(self, runner, tmp_path):
        """CLI defaults to <output>/extracted when --elements-input-dir not specified."""
        # Create test structure
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        # Create default extracted directory (output_dir defaults to ./<pdf_stem>)
        default_dir = tmp_path / "test" / "extracted"
        default_dir.mkdir(parents=True)
        (default_dir / "figure_01.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--output", str(tmp_path / "test"),
            "--skip-extraction",
            "--api-key", "dummy-key",
        ])

        # Should use default directory and not complain about missing --elements-input-dir
        assert "--elements-input-dir is required" not in result.output

    def test_skip_extraction_default_directory_not_exists_helpful_error(self, runner, tmp_path):
        """CLI provides helpful error when default directory doesn't exist."""
        # Create test structure without extracted directory
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        result = runner.invoke(cli, [
            "generate",
            str(pdf_path),
            "--output", str(tmp_path / "test"),
            "--skip-extraction",
            "--api-key", "dummy-key",
        ])

        # Should fail with helpful hint
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()
        assert (
            "hint:" in result.output.lower()
            or "run without --skip-extraction" in result.output.lower()
        )
