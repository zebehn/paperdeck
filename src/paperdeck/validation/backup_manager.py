"""Backup management for LaTeX files before applying fixes.

This module provides functionality to create, validate, and restore backups
of LaTeX files before applying automatic fixes.
"""

import hashlib
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class BackupMetadata:
    """Metadata for a backup file.

    Attributes:
        original_path: Path to the original file
        backup_path: Path to the backup file
        file_hash: SHA256 hash of the original file content
        timestamp: ISO format timestamp of when backup was created
    """

    original_path: Path
    backup_path: Path
    file_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation of metadata
        """
        return {
            "original_path": str(self.original_path),
            "backup_path": str(self.backup_path),
            "file_hash": self.file_hash,
            "timestamp": self.timestamp
        }


class BackupManager:
    """Manages backups of LaTeX files.

    Creates SHA256-based backups before applying fixes, validates backup
    integrity, and provides restoration capabilities.
    """

    def __init__(self, backup_dir: str = ".backup"):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups (default: .backup)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal SHA256 hash string (64 characters)

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def create_backup(self, file_path: Path) -> BackupMetadata:
        """Create a backup of the specified file.

        Args:
            file_path: Path to file to backup

        Returns:
            BackupMetadata object with backup information

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup nonexistent file: {file_path}")

        # Compute hash before backup
        file_hash = self.compute_file_hash(file_path)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        original_name = file_path.stem
        original_ext = file_path.suffix

        backup_filename = f"{original_name}_{timestamp}{original_ext}"
        backup_path = self.backup_dir / backup_filename

        # Copy file to backup location
        shutil.copy2(file_path, backup_path)

        # Create metadata
        metadata = BackupMetadata(
            original_path=file_path,
            backup_path=backup_path,
            file_hash=file_hash,
            timestamp=datetime.now().isoformat()
        )

        return metadata

    def validate_backup(self, metadata: BackupMetadata) -> bool:
        """Validate backup integrity using hash.

        Args:
            metadata: Backup metadata to validate

        Returns:
            True if backup is valid, False otherwise
        """
        if not metadata.backup_path.exists():
            return False

        try:
            # Compute hash of backup file
            backup_hash = self.compute_file_hash(metadata.backup_path)

            # Compare with stored hash
            return backup_hash == metadata.file_hash
        except Exception:
            return False

    def restore_backup(self, metadata: BackupMetadata) -> None:
        """Restore a file from backup.

        Args:
            metadata: Backup metadata

        Raises:
            FileNotFoundError: If backup file does not exist
            ValueError: If backup fails integrity check
        """
        if not metadata.backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {metadata.backup_path}")

        # Validate backup before restoring
        if not self.validate_backup(metadata):
            raise ValueError(f"Backup integrity check failed: {metadata.backup_path}")

        # Restore backup to original location
        shutil.copy2(metadata.backup_path, metadata.original_path)

    def list_backups(self, file_path: Path) -> List[BackupMetadata]:
        """List all backups for a specific file.

        Args:
            file_path: Path to original file

        Returns:
            List of BackupMetadata objects for this file, sorted by timestamp (newest first)
        """
        backups = []
        original_name = file_path.stem
        original_ext = file_path.suffix

        # Find all backup files matching the pattern
        pattern = f"{original_name}_*{original_ext}"

        for backup_file in self.backup_dir.glob(pattern):
            try:
                # Extract timestamp from filename
                # Format: originalname_YYYYMMDD_HHMMSS_ffffff.ext
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    # Reconstruct timestamp (approximate)
                    timestamp = datetime.now().isoformat()  # Placeholder

                    # Compute hash
                    file_hash = self.compute_file_hash(backup_file)

                    metadata = BackupMetadata(
                        original_path=file_path,
                        backup_path=backup_file,
                        file_hash=file_hash,
                        timestamp=timestamp
                    )
                    backups.append(metadata)
            except Exception:
                # Skip invalid backup files
                continue

        # Sort by modification time (newest first)
        backups.sort(key=lambda m: m.backup_path.stat().st_mtime, reverse=True)

        return backups

    def cleanup_old_backups(self, file_path: Path, keep_count: int = 5) -> int:
        """Clean up old backups, keeping only the most recent N backups.

        Args:
            file_path: Path to original file
            keep_count: Number of most recent backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups(file_path)

        # Keep only the most recent N backups
        to_delete = backups[keep_count:]

        deleted_count = 0
        for metadata in to_delete:
            try:
                metadata.backup_path.unlink()
                deleted_count += 1
            except Exception:
                # Skip files that can't be deleted
                continue

        return deleted_count
