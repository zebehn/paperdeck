"""Command-line interface for PaperDeck.

This module provides the main CLI commands for generating presentations from
research papers.
"""

import sys
import logging
import os
from pathlib import Path
from typing import Optional

import click

from ..core.config import AppConfiguration, AIServiceConfiguration, ExtractionConfiguration
from ..core.exceptions import PaperDeckError
from ..core.models import ElementType


@click.group()
@click.version_option(version="0.1.0", prog_name="paperdeck")
@click.pass_context
def cli(ctx):
    """PaperDeck - Generate LaTeX presentations from research papers.

    Transform PDF research papers into polished Beamer presentations using AI.
    """
    # Initialize context
    ctx.ensure_object(dict)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Output directory for generated files (default: ./paperdeck_output)",
)
@click.option(
    "-t",
    "--theme",
    default="Madrid",
    help="Beamer theme to use (default: Madrid)",
)
@click.option(
    "-p",
    "--prompt",
    "prompt_name",
    default="default",
    help="Prompt template name or path to custom prompt file (default: default)",
)
@click.option(
    "--provider",
    default="openai",
    type=click.Choice(["openai", "anthropic", "ollama", "lmstudio"]),
    help="AI service provider (default: openai)",
)
@click.option(
    "--model",
    help="Specific model to use (e.g., gpt-4, claude-3-opus)",
)
@click.option(
    "--api-key",
    help="API key for cloud providers (or set via environment variable)",
)
@click.option(
    "--no-compile",
    is_flag=True,
    help="Skip LaTeX compilation to PDF",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--extract-figures/--no-extract-figures",
    default=True,
    help="Extract figures from PDF (default: enabled)",
)
@click.option(
    "--extract-tables/--no-extract-tables",
    default=True,
    help="Extract tables from PDF (default: enabled)",
)
@click.option(
    "--extraction-confidence",
    type=float,
    default=0.75,
    help="Minimum confidence threshold for extracted elements (0.0-1.0, default: 0.75)",
)
@click.option(
    "--elements-output-dir",
    type=click.Path(path_type=Path),
    help="Directory to save extracted elements (default: <output>/extracted)",
)
@click.pass_context
def generate(
    ctx,
    pdf_path: Path,
    output_path: Optional[Path],
    theme: str,
    prompt_name: str,
    provider: str,
    model: Optional[str],
    api_key: Optional[str],
    no_compile: bool,
    verbose: bool,
    extract_figures: bool,
    extract_tables: bool,
    extraction_confidence: float,
    elements_output_dir: Optional[Path],
):
    """Generate a presentation from a PDF research paper.

    PDF_PATH: Path to the input PDF file
    """
    from .commands import generate_presentation

    # Set up configuration
    output_dir = output_path or Path("./paperdeck_output")

    # Configure AI service
    ai_config_kwargs = {"default_provider": provider}

    # Check for API key from CLI option or environment variable
    if api_key:
        # CLI option takes precedence
        if provider == "openai":
            ai_config_kwargs["openai_api_key"] = api_key
        elif provider == "anthropic":
            ai_config_kwargs["anthropic_api_key"] = api_key
    else:
        # Check environment variables
        if provider == "openai":
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                ai_config_kwargs["openai_api_key"] = openai_key
        elif provider == "anthropic":
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_key:
                ai_config_kwargs["anthropic_api_key"] = anthropic_key

    try:
        ai_config = AIServiceConfiguration(**ai_config_kwargs)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            f"\nHint: Set API key via --api-key option or environment variable (OPENAI_API_KEY or ANTHROPIC_API_KEY)",
            err=True,
        )
        sys.exit(1)

    # Configure element extraction
    extraction_element_types = []
    if extract_figures:
        extraction_element_types.append(ElementType.FIGURE)
    if extract_tables:
        extraction_element_types.append(ElementType.TABLE)

    # If no types selected, fall back to both (avoid empty list)
    if not extraction_element_types:
        extraction_element_types = [ElementType.FIGURE, ElementType.TABLE]

    try:
        extraction_config = ExtractionConfiguration(
            confidence_threshold=extraction_confidence,
            element_types=extraction_element_types,
            output_directory=elements_output_dir or (output_dir / "extracted"),
            extract_figures=extract_figures,
            extract_tables=extract_tables,
        )
    except ValueError as e:
        click.echo(f"Error: Invalid extraction configuration: {e}", err=True)
        sys.exit(1)

    config = AppConfiguration(
        ai_services=ai_config,
        output_directory=output_dir,
        log_level="DEBUG" if verbose else "INFO",
        extraction_config=extraction_config,
    )

    # Setup logging
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format='%(levelname)s - %(message)s' if verbose else '%(message)s'
    )

    # Display progress
    if verbose:
        click.echo(f"Input PDF: {pdf_path}")
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Theme: {theme}")
        click.echo(f"Prompt: {prompt_name}")
        click.echo(f"Provider: {provider}")
        if model:
            click.echo(f"Model: {model}")

    # Generate presentation
    try:
        with click.progressbar(
            length=4,
            label="Generating presentation",
            show_percent=False,
            show_pos=True,
        ) as bar:
            result = generate_presentation(
                pdf_path=pdf_path,
                config=config,
                theme=theme,
                prompt_name=prompt_name,
                model=model,
                compile_pdf=not no_compile,
                progress_callback=lambda: bar.update(1),
            )

        # Display results
        click.echo(f"\n✓ Presentation generated successfully!")
        click.echo(f"  LaTeX file: {result['tex_path']}")
        if result.get("pdf_path"):
            click.echo(f"  PDF file: {result['pdf_path']}")
        click.echo(f"  Slides: {result['slide_count']}")

    except PaperDeckError as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nUnexpected error: {e}", err=True)
        if verbose:
            import traceback

            click.echo("\nTraceback:", err=True)
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--library-path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to prompt library directory",
)
def list_prompts(library_path: Optional[Path]):
    """List available prompt templates."""
    from ..prompts.manager import PromptLibrary

    try:
        if not library_path:
            # Use default location
            library_path = Path(__file__).parent.parent.parent.parent / "prompts" / "templates"

        library = PromptLibrary(library_path=library_path)
        templates = library.list_templates()

        if not templates:
            # Try to load default templates
            for name in ["default", "technical", "accessible", "pedagogical"]:
                try:
                    library.get_template(name)
                except:
                    pass
            templates = library.list_templates()

        if not templates:
            click.echo("No prompt templates found.")
            return

        click.echo(f"\nAvailable prompt templates ({len(templates)}):\n")
        for template in sorted(templates, key=lambda t: t.name):
            builtin = " [builtin]" if template.is_builtin else ""
            click.echo(f"  • {template.name}{builtin}")
            click.echo(f"    {template.description}")
            click.echo(f"    Style: {template.style}, Detail: {template.detail_level}\n")

    except Exception as e:
        click.echo(f"Error listing prompts: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    click.echo("PaperDeck 0.1.0")
    click.echo("LaTeX Presentation Generator for Research Papers")


if __name__ == "__main__":
    cli()
