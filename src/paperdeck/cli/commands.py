"""CLI command implementations.

This module contains the core logic for CLI commands.
"""

import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

from ..ai.orchestrator import AIOrchestrator
from ..ai.retry_helpers import generate_with_retry
from ..ai.service import AIRequest
from ..core.config import AppConfiguration
from ..core.exceptions import (
    CompilationError,
    ExtractionError,
    GenerationError,
    PaperDeckError,
)
from ..core.models import Paper
from ..extraction.extractor import PaperExtractor
from ..generation.latex_generator import LaTeXGenerator
from ..generation.slide_organizer import SlideOrganizer
from ..prompts.manager import PromptLibrary
from ..services.generation_service import GenerationService


def generate_presentation(
    pdf_path: Path,
    config: AppConfiguration,
    theme: str = "Madrid",
    prompt_name: str = "default",
    model: Optional[str] = None,
    compile_pdf: bool = True,
    progress_callback: Optional[Callable] = None,
) -> Dict:
    """Generate presentation from PDF paper.

    Args:
        pdf_path: Path to input PDF
        config: Application configuration
        theme: Beamer theme name
        prompt_name: Name of prompt template to use
        model: Specific model to use (optional)
        compile_pdf: Whether to compile LaTeX to PDF
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with results (tex_path, pdf_path, slide_count, etc.)

    Raises:
        PaperDeckError: If generation fails
    """

    def progress():
        """Call progress callback if provided."""
        if progress_callback:
            progress_callback()

    # Step 1: Prepare paper with text extraction
    try:
        # NEW: Use GenerationService to extract text from PDF
        generation_service = GenerationService(config)
        paper = generation_service.prepare_paper(pdf_path)

        progress()

    except Exception as e:
        raise ExtractionError(f"Failed to prepare paper: {e}")

    # Step 1.5: Extract elements (figures, tables, equations) from PDF
    try:
        extractor = PaperExtractor(
            confidence_threshold=config.extraction_config.confidence_threshold,
            output_directory=config.extraction_config.output_directory,
            extraction_config=config.extraction_config,
        )

        # Extract elements (figures, tables, equations)
        elements = extractor.extract(
            paper_path=pdf_path,
            element_types=config.extraction_config.element_types,
        )

        # Add elements to paper
        paper.extracted_elements = elements  # Use the new field from Phase 5

        progress()

    except Exception as e:
        raise ExtractionError(f"Failed to extract elements from PDF: {e}")

    # Step 2: Generate LaTeX using AI
    try:
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Generating presentation using AI...")

        # Call AI to generate complete LaTeX document
        latex_code = generate_with_ai(
            paper=paper,
            config=config,
            prompt_name=prompt_name,
            model=model,
            pdf_path=pdf_path,  # Pass PDF file to AI service
        )

        # Extract LaTeX from response if wrapped in markdown code blocks
        if "```latex" in latex_code:
            # Remove markdown code block markers
            latex_code = latex_code.split("```latex")[1].split("```")[0].strip()
        elif "```" in latex_code:
            # Remove generic code block markers
            latex_code = latex_code.split("```")[1].split("```")[0].strip()

        logger.info(f"AI generated {len(latex_code)} characters of LaTeX code")

        # Ensure output directory exists
        config.output_directory.mkdir(parents=True, exist_ok=True)

        # Write LaTeX file
        output_name = pdf_path.stem
        tex_path = config.output_directory / f"{output_name}.tex"
        tex_path.write_text(latex_code)

        logger.info(f"LaTeX file written to {tex_path}")

        progress()

    except Exception as e:
        raise GenerationError(f"Failed to generate LaTeX with AI: {e}")

    # Step 3: Compile to PDF (optional)
    pdf_output_path = None
    if compile_pdf:
        try:
            pdf_output_path = compile_latex(tex_path, config.output_directory)
            progress()
        except Exception as e:
            # Don't fail if compilation fails, just warn
            pdf_output_path = None

    # Count slides by counting \begin{frame} occurrences
    slide_count = latex_code.count(r"\begin{frame}") + latex_code.count(r"\frame{")

    return {
        "tex_path": tex_path,
        "pdf_path": pdf_output_path,
        "slide_count": slide_count,
        "latex_code": latex_code,
    }


def compile_latex(tex_path: Path, output_dir: Path) -> Path:
    """Compile LaTeX file to PDF.

    Args:
        tex_path: Path to .tex file
        output_dir: Output directory

    Returns:
        Path: Path to generated PDF

    Raises:
        CompilationError: If compilation fails
    """
    try:
        # Run pdflatex twice for references
        for _ in range(2):
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory",
                    str(output_dir),
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # Try to extract error message from log
                log_path = output_dir / f"{tex_path.stem}.log"
                error_msg = "LaTeX compilation failed"
                if log_path.exists():
                    log_content = log_path.read_text()
                    # Extract first error line
                    for line in log_content.split("\n"):
                        if line.startswith("!"):
                            error_msg = line
                            break

                raise CompilationError(f"{error_msg}\n\nSee {log_path} for details")

        # Return path to PDF
        pdf_path = output_dir / f"{tex_path.stem}.pdf"
        if not pdf_path.exists():
            raise CompilationError(f"PDF was not generated: {pdf_path}")

        return pdf_path

    except subprocess.TimeoutExpired:
        raise CompilationError("LaTeX compilation timed out after 60 seconds")
    except FileNotFoundError:
        raise CompilationError(
            "pdflatex not found. Please install TeX Live or MiKTeX."
        )
    except Exception as e:
        if isinstance(e, CompilationError):
            raise
        raise CompilationError(f"Compilation error: {e}")


def generate_with_ai(
    paper: Paper,
    config: AppConfiguration,
    prompt_name: str,
    model: Optional[str],
    pdf_path: Optional[Path] = None,
) -> str:
    """Generate complete LaTeX presentation using AI.

    Args:
        paper: Paper model with text content and extracted elements
        config: Application configuration
        prompt_name: Name of prompt template
        model: Model to use
        pdf_path: Optional path to PDF file to send to AI service

    Returns:
        str: Complete LaTeX beamer document generated by AI

    Raises:
        GenerationError: If AI generation fails
    """
    import logging
    logger = logging.getLogger(__name__)

    # Load prompt template
    prompt_library_path = Path(__file__).parent.parent.parent.parent / "prompts" / "templates"
    library = PromptLibrary(library_path=prompt_library_path)
    template = library.get_template(prompt_name)

    # Prepare context - if PDF file is provided, use minimal text; otherwise use full extracted content
    if pdf_path:
        # When PDF file is attached, provide minimal context
        paper_content = f"**PDF file attached: {pdf_path.name}**\n\n"
        paper_content += f"Title: {paper.title or 'Untitled'}\n"
        paper_content += f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}\n\n"
        paper_content += "**Please read the attached PDF file for full paper content.**\n\n"

        # Add only extracted figure/table metadata for reference
        if paper.extracted_elements:
            figures = [e for e in paper.extracted_elements if e.element_type.value == "figure"]
            tables = [e for e in paper.extracted_elements if e.element_type.value == "table"]

            if figures:
                paper_content += "Extracted Figures:\n"
                for fig in figures:
                    filename = fig.output_filename.name if fig.output_filename else "unknown"
                    paper_content += f"- {filename} (page {fig.page_number})\n"
                paper_content += "\n"

            if tables:
                paper_content += "Extracted Tables:\n"
                for tbl in tables:
                    filename = tbl.output_filename.name if tbl.output_filename else "unknown"
                    paper_content += f"- {filename} (page {tbl.page_number})\n"
                paper_content += "\n"
    else:
        # No PDF file - use full extracted text content
        paper_content = f"Title: {paper.title or 'Untitled'}\n"
        paper_content += f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}\n\n"

        # Add full text content if available
        if paper.text_content:
            paper_content += "Full Text Content:\n"
            paper_content += "=" * 80 + "\n"
            paper_content += paper.text_content[:30000]  # Limit to first 30k chars to avoid token limits
            if len(paper.text_content) > 30000:
                paper_content += "\n\n[Content truncated for length...]"
            paper_content += "\n" + "=" * 80 + "\n\n"

        # Add section information
        if paper.sections:
            paper_content += "Paper Sections:\n"
            for section in paper.sections:
                paper_content += f"- {section.title}\n"
                if section.content:
                    # Include first 500 chars of each section
                    content_preview = section.content[:500]
                    paper_content += f"  {content_preview}...\n"
            paper_content += "\n"

        # Add extracted figures information
        if paper.extracted_elements:
            figures = [e for e in paper.extracted_elements if e.element_type.value == "figure"]
            tables = [e for e in paper.extracted_elements if e.element_type.value == "table"]

            if figures:
                paper_content += "Extracted Figures:\n"
                for fig in figures:
                    filename = fig.output_filename.name if fig.output_filename else "unknown"
                    paper_content += f"- {filename} (page {fig.page_number}, confidence: {fig.confidence_score:.2f})\n"
                paper_content += "\n"

            if tables:
                paper_content += "Extracted Tables:\n"
                for tbl in tables:
                    filename = tbl.output_filename.name if tbl.output_filename else "unknown"
                    paper_content += f"- {filename} (page {tbl.page_number}, confidence: {tbl.confidence_score:.2f})\n"
                paper_content += "\n"

    context = {"paper_content": paper_content}

    # Render prompt
    prompt = template.render(context)

    logger.info("Sending prompt to AI service for LaTeX generation...")
    logger.debug(f"Prompt length: {len(prompt)} characters")

    # Log the full prompt in verbose mode for debugging
    logger.info("=" * 80)
    logger.info("PROMPT SENT TO LLM SERVICE:")
    logger.info("=" * 80)
    logger.info(prompt)
    logger.info("=" * 80)

    # Get AI service
    orchestrator = AIOrchestrator(config.ai_services)
    service = orchestrator.get_default_service()

    # Determine model - use more capable models for LaTeX generation
    if not model:
        if config.ai_services.default_provider == "openai":
            model = "gpt-5.1"  # Use GPT-5.1 for better LaTeX generation
        elif config.ai_services.default_provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"  # Use Claude 3.5 Sonnet
        else:
            model = "default"

    # Create request with higher token limit for full LaTeX document
    request = AIRequest(
        prompt=prompt,
        model=model,
        max_tokens=16000,  # Increased for full LaTeX document
        temperature=0.3,  # Lower temperature for more structured output
        pdf_file_path=pdf_path,  # Include PDF file for direct access
    )

    # Generate with retry
    logger.info(f"Calling AI service ({model})...")
    response = generate_with_retry(service, request)

    logger.info(f"Received response from AI service ({len(response.content)} characters)")

    return response.content
