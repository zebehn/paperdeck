"""Integration tests for CLI commands.

These tests verify the command-line interface works correctly.
Tests should FAIL until CLI implementation is complete (TDD).
"""

import pytest
from pathlib import Path
from click.testing import CliRunner


@pytest.mark.integration
class TestCLIGenerate:
    """Tests for 'paperdeck generate' command."""

    def test_cli_generate_with_defaults(self, tmp_path):
        """Test generating presentation with default options."""
        pytest.skip("Implementation not complete - TDD test")

        # Future implementation:
        from paperdeck.cli.main import cli

        runner = CliRunner()

        # Create test PDF
        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")
        output_path = tmp_path / "presentation.tex"

        # Run CLI command
        result = runner.invoke(cli, ["generate", str(paper_path), str(output_path)])

        # Verify success
        assert result.exit_code == 0
        assert output_path.exists()
        assert "Generated presentation" in result.output

    def test_cli_generate_shows_progress(self, tmp_path):
        """Test that generate command shows progress indicators."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")

        result = runner.invoke(cli, ["generate", str(paper_path)])

        # Should show progress messages
        assert "Loading paper" in result.output or "Extracting" in result.output

    def test_cli_generate_with_model_option(self, tmp_path):
        """Test generate with --model option."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")

        result = runner.invoke(
            cli,
            ["generate", str(paper_path), "--model", "gpt-4"]
        )

        # Should use specified model
        assert result.exit_code == 0

    def test_cli_generate_with_prompt_option(self, tmp_path):
        """Test generate with --prompt option."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")

        result = runner.invoke(
            cli,
            ["generate", str(paper_path), "--prompt", "technical-detailed"]
        )

        assert result.exit_code == 0

    def test_cli_generate_with_theme_option(self, tmp_path):
        """Test generate with --theme option."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")

        result = runner.invoke(
            cli,
            ["generate", str(paper_path), "--theme", "Berkeley"]
        )

        assert result.exit_code == 0

    def test_cli_generate_missing_file_shows_error(self):
        """Test that missing input file shows clear error."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["generate", "/nonexistent/paper.pdf"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_cli_generate_invalid_file_shows_error(self, tmp_path):
        """Test that invalid PDF shows clear error."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        # Create non-PDF file
        invalid_file = tmp_path / "not_pdf.txt"
        invalid_file.write_text("not a pdf")

        result = runner.invoke(cli, ["generate", str(invalid_file)])

        assert result.exit_code != 0
        assert "pdf" in result.output.lower()

    def test_cli_generate_creates_output_directory(self, tmp_path):
        """Test that generate creates output directory if needed."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        paper_path = tmp_path / "paper.pdf"
        paper_path.write_text("%PDF-1.4 test")

        output_dir = tmp_path / "nonexistent" / "output"
        output_path = output_dir / "presentation.tex"

        result = runner.invoke(cli, ["generate", str(paper_path), str(output_path)])

        # Should create directory and file
        assert output_dir.exists()
        assert output_path.exists()

    def test_cli_help_shows_usage(self):
        """Test that --help shows usage information."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "generate" in result.output
        assert "Usage" in result.output

    def test_cli_version_shows_version(self):
        """Test that --version shows version number."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower() or "paperdeck" in result.output.lower()


@pytest.mark.integration
class TestCLIConfig:
    """Tests for configuration commands."""

    def test_cli_config_init_creates_config(self, tmp_path):
        """Test that config init creates configuration file."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        # Run in temp directory
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "init"])

            assert result.exit_code == 0
            # Config file should be created

    def test_cli_config_show_displays_config(self):
        """Test that config show displays current configuration."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        # Should show config values


@pytest.mark.integration
class TestCLIPrompts:
    """Tests for prompt management commands."""

    def test_cli_prompts_list_shows_templates(self):
        """Test that prompts list shows available templates."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["prompts", "list"])

        assert result.exit_code == 0
        assert "default" in result.output

    def test_cli_prompts_show_displays_template(self):
        """Test that prompts show displays template content."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        result = runner.invoke(cli, ["prompts", "show", "default"])

        assert result.exit_code == 0
        assert "{paper_content}" in result.output

    def test_cli_prompts_add_adds_template(self, tmp_path):
        """Test that prompts add adds custom template."""
        pytest.skip("Implementation not complete")

        from paperdeck.cli.main import cli

        runner = CliRunner()

        # Create custom prompt file
        prompt_file = tmp_path / "custom.txt"
        prompt_file.write_text("Custom prompt: {paper_content}")

        result = runner.invoke(
            cli,
            [
                "prompts",
                "add",
                "custom",
                str(prompt_file),
                "--description",
                "Custom prompt",
            ],
        )

        assert result.exit_code == 0
