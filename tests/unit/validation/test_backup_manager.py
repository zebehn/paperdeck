"""Unit tests for backup manager."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from paperdeck.validation.backup_manager import BackupManager, BackupMetadata


class TestBackupManager:
    """Tests for BackupManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def backup_manager(self, temp_dir):
        """Create BackupManager instance with temp backup directory."""
        backup_dir = temp_dir / ".backup"
        return BackupManager(backup_dir=str(backup_dir))

    @pytest.mark.unit
    @pytest.mark.validation
    def test_create_backup_manager(self, backup_manager):
        """Test BackupManager initialization."""
        assert backup_manager is not None
        assert backup_manager.backup_dir.exists()
        assert backup_manager.backup_dir.is_dir()

    @pytest.mark.unit
    @pytest.mark.validation
    def test_compute_file_hash(self, backup_manager, temp_dir):
        """Test SHA256 hash computation."""
        # Create test file
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{test content}")

        # Compute hash
        file_hash = backup_manager.compute_file_hash(test_file)

        # Verify hash format (SHA256 = 64 hex characters)
        assert len(file_hash) == 64
        assert all(c in '0123456789abcdef' for c in file_hash)

        # Same content should produce same hash
        file_hash2 = backup_manager.compute_file_hash(test_file)
        assert file_hash == file_hash2

    @pytest.mark.unit
    @pytest.mark.validation
    def test_compute_hash_consistency(self, backup_manager, temp_dir):
        """Test hash changes when content changes."""
        test_file = temp_dir / "test.tex"
        test_file.write_text("content1")
        hash1 = backup_manager.compute_file_hash(test_file)

        test_file.write_text("content2")
        hash2 = backup_manager.compute_file_hash(test_file)

        assert hash1 != hash2

    @pytest.mark.unit
    @pytest.mark.validation
    def test_create_backup(self, backup_manager, temp_dir):
        """Test creating a backup of a file."""
        # Create test file
        test_file = temp_dir / "test.tex"
        original_content = r"\textbf{original content}"
        test_file.write_text(original_content)

        # Create backup
        metadata = backup_manager.create_backup(test_file)

        # Verify metadata
        assert metadata is not None
        assert metadata.original_path == test_file
        assert metadata.backup_path.exists()
        assert metadata.file_hash is not None
        assert metadata.timestamp is not None

        # Verify backup content matches original
        backup_content = metadata.backup_path.read_text()
        assert backup_content == original_content

    @pytest.mark.unit
    @pytest.mark.validation
    def test_backup_naming_convention(self, backup_manager, temp_dir):
        """Test backup file naming includes timestamp and hash."""
        test_file = temp_dir / "document.tex"
        test_file.write_text("content")

        metadata = backup_manager.create_backup(test_file)

        # Backup filename should include original name and timestamp
        backup_name = metadata.backup_path.name
        assert "document" in backup_name
        assert backup_name.endswith(".tex")

    @pytest.mark.unit
    @pytest.mark.validation
    def test_multiple_backups_same_file(self, backup_manager, temp_dir):
        """Test creating multiple backups of same file."""
        test_file = temp_dir / "test.tex"
        test_file.write_text("version1")

        metadata1 = backup_manager.create_backup(test_file)

        # Modify file and create another backup
        test_file.write_text("version2")
        metadata2 = backup_manager.create_backup(test_file)

        # Should have different backup paths
        assert metadata1.backup_path != metadata2.backup_path

        # Both backups should exist
        assert metadata1.backup_path.exists()
        assert metadata2.backup_path.exists()

        # Content should be preserved
        assert metadata1.backup_path.read_text() == "version1"
        assert metadata2.backup_path.read_text() == "version2"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_restore_from_backup(self, backup_manager, temp_dir):
        """Test restoring a file from backup."""
        test_file = temp_dir / "test.tex"
        original_content = "original content"
        test_file.write_text(original_content)

        # Create backup
        metadata = backup_manager.create_backup(test_file)

        # Modify original file
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Restore from backup
        backup_manager.restore_backup(metadata)

        # File should be restored to original content
        assert test_file.read_text() == original_content

    @pytest.mark.unit
    @pytest.mark.validation
    def test_validate_backup_integrity(self, backup_manager, temp_dir):
        """Test backup integrity validation using hash."""
        test_file = temp_dir / "test.tex"
        test_file.write_text("content")

        metadata = backup_manager.create_backup(test_file)

        # Verify backup is valid
        assert backup_manager.validate_backup(metadata) is True

        # Corrupt backup file
        metadata.backup_path.write_text("corrupted")

        # Should detect corruption
        assert backup_manager.validate_backup(metadata) is False

    @pytest.mark.unit
    @pytest.mark.validation
    def test_list_backups(self, backup_manager, temp_dir):
        """Test listing all backups for a file."""
        test_file = temp_dir / "test.tex"
        test_file.write_text("version1")

        metadata1 = backup_manager.create_backup(test_file)

        test_file.write_text("version2")
        metadata2 = backup_manager.create_backup(test_file)

        # List backups
        backups = backup_manager.list_backups(test_file)

        # Should find both backups
        assert len(backups) >= 2
        backup_paths = [b.backup_path for b in backups]
        assert metadata1.backup_path in backup_paths
        assert metadata2.backup_path in backup_paths

    @pytest.mark.unit
    @pytest.mark.validation
    def test_cleanup_old_backups(self, backup_manager, temp_dir):
        """Test cleaning up old backups."""
        test_file = temp_dir / "test.tex"

        # Create multiple backups
        for i in range(5):
            test_file.write_text(f"version{i}")
            backup_manager.create_backup(test_file)

        # Cleanup keeping only last 3
        backup_manager.cleanup_old_backups(test_file, keep_count=3)

        # Should only have 3 backups remaining
        remaining = backup_manager.list_backups(test_file)
        assert len(remaining) == 3

    @pytest.mark.unit
    @pytest.mark.validation
    def test_backup_nonexistent_file_raises_error(self, backup_manager, temp_dir):
        """Test backing up nonexistent file raises error."""
        nonexistent = temp_dir / "nonexistent.tex"

        with pytest.raises(FileNotFoundError):
            backup_manager.create_backup(nonexistent)


class TestBackupMetadata:
    """Tests for BackupMetadata dataclass."""

    @pytest.mark.unit
    @pytest.mark.validation
    def test_metadata_creation(self, tmp_path):
        """Test creating backup metadata."""
        original = tmp_path / "original.tex"
        backup = tmp_path / ".backup" / "backup.tex"

        metadata = BackupMetadata(
            original_path=original,
            backup_path=backup,
            file_hash="abc123",
            timestamp=datetime.now().isoformat()
        )

        assert metadata.original_path == original
        assert metadata.backup_path == backup
        assert metadata.file_hash == "abc123"
        assert metadata.timestamp is not None

    @pytest.mark.unit
    @pytest.mark.validation
    def test_metadata_to_dict(self, tmp_path):
        """Test converting metadata to dictionary."""
        metadata = BackupMetadata(
            original_path=tmp_path / "test.tex",
            backup_path=tmp_path / "backup.tex",
            file_hash="hash123",
            timestamp="2024-01-01T12:00:00"
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert "original_path" in data
        assert "backup_path" in data
        assert "file_hash" in data
        assert "timestamp" in data
