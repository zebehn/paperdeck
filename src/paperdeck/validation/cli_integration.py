"""CLI integration helpers for validation and fixing.

This module provides helper functions for integrating validation
into the CLI generation pipeline.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from .backup_manager import BackupManager, BackupMetadata
from .latex_fixer import FixerConfig, LaTeXFixer
from .latex_validator import LaTeXValidator, ValidationConfig
from .validation_errors import ValidationResult

logger = logging.getLogger(__name__)


def validate_and_fix_latex_file(
    tex_path: Path,
    output_dir: Path,
    config: Optional[ValidationConfig] = None,
    fixer_config: Optional[FixerConfig] = None,
    attempt_number: int = 1
) -> Tuple[bool, Optional[BackupMetadata], int]:
    """Validate and fix a LaTeX file with automatic backup.

    Args:
        tex_path: Path to LaTeX file to validate and fix
        output_dir: Output directory for backups
        config: Validation configuration (optional)
        fixer_config: Fixer configuration (optional)
        attempt_number: Current retry attempt number

    Returns:
        Tuple of (fixed_successfully, backup_metadata, num_fixes_applied)
    """
    try:
        # Validate the file
        validator = LaTeXValidator(config=config or ValidationConfig())
        validation_result = validator.validate_file(tex_path)

        if validation_result.is_valid:
            logger.debug("No structural errors found")
            return False, None, 0

        logger.info(f"Found {len(validation_result.errors)} structural error(s)")

        # Log errors for debugging
        for error in validation_result.errors[:5]:  # Show first 5
            logger.debug(f"  Line {error.line_number}: {error.message}")

        # Create backup manager
        backup_dir = output_dir / ".backup"
        backup_manager = BackupManager(backup_dir=str(backup_dir))

        # Apply fixes with automatic backup
        fixer_cfg = fixer_config or FixerConfig(
            create_backup=True,
            backup_dir=str(backup_dir)
        )
        fixer = LaTeXFixer(config=fixer_cfg, backup_manager=backup_manager)

        # Fix file in place
        fixed_content, changes, backup_metadata = fixer.fix_file(
            tex_path,
            validation_result.errors,
            in_place=True
        )

        if not changes:
            logger.warning("Auto-fix unable to fix any errors")
            return False, backup_metadata, 0

        # Log changes
        logger.info(f"Applied {len(changes)} fix(es):")
        for change in changes:
            logger.info(f"  - Line {change.line_number}: {change.description}")

        return True, backup_metadata, len(changes)

    except Exception as e:
        logger.error(f"Error during validation/fix: {e}")
        return False, None, 0


def validate_latex_file(
    tex_path: Path,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """Validate a LaTeX file without fixing.

    Args:
        tex_path: Path to LaTeX file to validate
        config: Validation configuration (optional)

    Returns:
        ValidationResult object
    """
    validator = LaTeXValidator(config=config or ValidationConfig())
    return validator.validate_file(tex_path)


def report_validation_results(
    result: ValidationResult,
    show_warnings: bool = False
) -> None:
    """Report validation results to logger.

    Args:
        result: ValidationResult to report
        show_warnings: Whether to show warnings
    """
    if result.is_valid:
        logger.info("✅ LaTeX validation passed")
        return

    # Report errors
    error_count = len(result.errors)
    auto_fixable = result.auto_fixable_count
    manual_fix = result.manual_fix_count

    logger.warning(f"❌ LaTeX validation found {error_count} error(s)")
    logger.info(f"  - {auto_fixable} auto-fixable")
    logger.info(f"  - {manual_fix} require manual review")

    # Show error details
    for error in result.errors[:10]:  # Show first 10
        logger.info(f"  Line {error.line_number}: {error.message}")

    if len(result.errors) > 10:
        logger.info(f"  ... and {len(result.errors) - 10} more error(s)")

    # Show warnings if requested
    if show_warnings and result.warnings:
        logger.info(f"⚠️  {len(result.warnings)} warning(s)")


def get_validation_summary(result: ValidationResult) -> str:
    """Get a one-line validation summary.

    Args:
        result: ValidationResult to summarize

    Returns:
        Summary string
    """
    if result.is_valid:
        return "✅ Valid"

    auto = result.auto_fixable_count
    manual = result.manual_fix_count
    total = len(result.errors)

    return f"❌ {total} error(s): {auto} auto-fixable, {manual} manual"
