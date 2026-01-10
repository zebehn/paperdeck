"""Integration tests for backup system integration with LaTeXFixer."""

import pytest
import tempfile
import shutil
from pathlib import Path

from paperdeck.validation.latex_validator import LaTeXValidator
from paperdeck.validation.latex_fixer import LaTeXFixer, FixerConfig
from paperdeck.validation.backup_manager import BackupManager


class TestBackupIntegration:
    """Integration tests for backup system with LaTeXFixer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.mark.integration
    @pytest.mark.validation
    def test_fix_file_creates_backup(self, temp_dir):
        """Test that fixing a file creates a backup."""
        # Create test file with error
        test_file = temp_dir / "test.tex"
        original_content = r"\textbf{Missing brace"
        test_file.write_text(original_content)

        # Validate and fix with backup enabled
        validator = LaTeXValidator()
        result = validator.validate_content(original_content)

        config = FixerConfig(create_backup=True, backup_dir=str(temp_dir / ".backup"))
        fixer = LaTeXFixer(config=config)

        fixed_content, changes, backup_metadata = fixer.fix_file(test_file, result.errors)

        # Verify backup was created
        assert backup_metadata is not None
        assert backup_metadata.backup_path.exists()
        assert backup_metadata.backup_path.read_text() == original_content

        # Verify file was fixed
        assert test_file.read_text() != original_content
        assert '}' in test_file.read_text()

    @pytest.mark.integration
    @pytest.mark.validation
    def test_fix_file_without_backup(self, temp_dir):
        """Test fixing without creating backup."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{Missing brace")

        validator = LaTeXValidator()
        result = validator.validate_content(test_file.read_text())

        config = FixerConfig(create_backup=False)
        fixer = LaTeXFixer(config=config)

        fixed_content, changes, backup_metadata = fixer.fix_file(test_file, result.errors)

        # Verify no backup was created
        assert backup_metadata is None
        assert fixer.get_last_backup() is None

    @pytest.mark.integration
    @pytest.mark.validation
    def test_restore_from_backup_after_fix(self, temp_dir):
        """Test restoring file from backup after fixing."""
        test_file = temp_dir / "test.tex"
        original_content = r"\textbf{Missing brace"
        test_file.write_text(original_content)

        # Fix with backup
        validator = LaTeXValidator()
        result = validator.validate_content(original_content)

        backup_manager = BackupManager(backup_dir=str(temp_dir / ".backup"))
        config = FixerConfig(create_backup=True)
        fixer = LaTeXFixer(config=config, backup_manager=backup_manager)

        fixed_content, changes, backup_metadata = fixer.fix_file(test_file, result.errors)

        # Verify file was modified
        assert test_file.read_text() != original_content

        # Restore from backup
        backup_manager.restore_backup(backup_metadata)

        # Verify file was restored
        assert test_file.read_text() == original_content

    @pytest.mark.integration
    @pytest.mark.validation
    def test_multiple_fixes_multiple_backups(self, temp_dir):
        """Test multiple fixes create multiple backups."""
        test_file = temp_dir / "test.tex"

        backup_manager = BackupManager(backup_dir=str(temp_dir / ".backup"))
        config = FixerConfig(create_backup=True)
        fixer = LaTeXFixer(config=config, backup_manager=backup_manager)
        validator = LaTeXValidator()

        # Fix 1
        test_file.write_text(r"\textbf{Missing brace")
        result = validator.validate_content(test_file.read_text())
        _, _, backup1 = fixer.fix_file(test_file, result.errors)

        # Fix 2
        test_file.write_text(r"\textit{Another missing brace")
        result = validator.validate_content(test_file.read_text())
        _, _, backup2 = fixer.fix_file(test_file, result.errors)

        # Verify two different backups exist
        assert backup1.backup_path != backup2.backup_path
        assert backup1.backup_path.exists()
        assert backup2.backup_path.exists()

        # List backups
        backups = backup_manager.list_backups(test_file)
        assert len(backups) >= 2

    @pytest.mark.integration
    @pytest.mark.validation
    def test_backup_with_validation_cycle(self, temp_dir):
        """Test complete cycle: validate → backup → fix → validate."""
        test_file = temp_dir / "document.tex"
        test_file.write_text(r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Missing brace
\end{frame}
\end{document}
""")

        validator = LaTeXValidator()
        backup_manager = BackupManager(backup_dir=str(temp_dir / ".backup"))
        config = FixerConfig(create_backup=True)
        fixer = LaTeXFixer(config=config, backup_manager=backup_manager)

        # Step 1: Initial validation
        result = validator.validate_file(test_file)
        assert not result.is_valid

        # Step 2: Fix with backup
        _, changes, backup_metadata = fixer.fix_file(test_file, result.errors)
        assert len(changes) >= 1
        assert backup_metadata is not None

        # Step 3: Re-validate
        result_after = validator.validate_file(test_file)
        brace_errors = [e for e in result_after.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 0

        # Step 4: Verify backup integrity
        assert backup_manager.validate_backup(backup_metadata) is True

    @pytest.mark.integration
    @pytest.mark.validation
    def test_fix_file_in_place_false(self, temp_dir):
        """Test fixing without modifying original file."""
        test_file = temp_dir / "test.tex"
        original_content = r"\textbf{Missing brace"
        test_file.write_text(original_content)

        validator = LaTeXValidator()
        result = validator.validate_content(original_content)

        config = FixerConfig(create_backup=True, backup_dir=str(temp_dir / ".backup"))
        fixer = LaTeXFixer(config=config)

        # Fix without in_place
        fixed_content, changes, backup_metadata = fixer.fix_file(
            test_file,
            result.errors,
            in_place=False
        )

        # Verify file was NOT modified
        assert test_file.read_text() == original_content

        # Verify fixed content is correct
        assert '}' in fixed_content
        assert len(changes) >= 1

        # Backup should still be created (based on original content)
        assert backup_metadata is not None

    @pytest.mark.integration
    @pytest.mark.validation
    def test_get_last_backup_tracking(self, temp_dir):
        """Test tracking of last backup created."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{Missing brace")

        validator = LaTeXValidator()
        result = validator.validate_content(test_file.read_text())

        config = FixerConfig(create_backup=True, backup_dir=str(temp_dir / ".backup"))
        fixer = LaTeXFixer(config=config)

        # Initially no backup
        assert fixer.get_last_backup() is None

        # Fix file
        _, _, backup_metadata = fixer.fix_file(test_file, result.errors)

        # Verify last backup is tracked
        assert fixer.get_last_backup() == backup_metadata
        assert fixer.get_last_backup().original_path == test_file

    @pytest.mark.integration
    @pytest.mark.validation
    def test_backup_with_no_changes_made(self, temp_dir):
        """Test backup behavior when no fixes are needed."""
        test_file = temp_dir / "valid.tex"
        test_file.write_text(r"\textbf{valid content}")

        validator = LaTeXValidator()
        result = validator.validate_content(test_file.read_text())

        config = FixerConfig(create_backup=True, backup_dir=str(temp_dir / ".backup"))
        fixer = LaTeXFixer(config=config)

        # Fix file (no errors to fix)
        _, changes, backup_metadata = fixer.fix_file(test_file, result.errors)

        # Backup should still be created
        assert backup_metadata is not None

        # But no changes should be made
        assert len(changes) == 0

        # File should remain unchanged
        assert test_file.read_text() == r"\textbf{valid content}"
