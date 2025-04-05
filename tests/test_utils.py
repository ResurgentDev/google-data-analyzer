"""
IMPORTANT: Use pytest-mock for all mocking needs, NOT unittest.mock!
"""
import os
import pytest
from pathlib import Path
from datetime import datetime
from src.utils import backup_file, clean_text, is_spam

@pytest.fixture
def test_file(tmp_path):
    # Create a temporary test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")
    return str(file_path)

class TestBackupFile:
    def test_backup_with_default_archive(self, test_file, tmp_path):
        # Test backup creation in default archive directory
        os.chdir(tmp_path)  # Change to temp directory for relative paths
        result = backup_file(test_file)
        
        assert os.path.exists(result)
        assert result.startswith(str(tmp_path / "archives"))
        assert result.endswith(".bak")
        
    def test_backup_with_custom_archive(self, test_file, tmp_path):
        # Test backup creation in custom archive directory
        custom_archive = tmp_path / "custom_archive"
        result = backup_file(test_file, str(custom_archive))
        
        assert os.path.exists(result)
        assert str(custom_archive) in result
        assert result.endswith(".bak")
        
    def test_missing_source_file(self, tmp_path):
        # Test handling of non-existent source file
        non_existent = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError) as exc_info:
            backup_file(str(non_existent))
        assert "Source file not found" in str(exc_info.value)
        
    def test_creates_archive_dir(self, test_file, tmp_path):
        # Test automatic creation of archive directory
        archive_dir = tmp_path / "new_archive"
        assert not archive_dir.exists()
        
        result = backup_file(test_file, str(archive_dir))
        
        assert archive_dir.exists()
        assert os.path.exists(result)
        
    def test_invalid_archive_permissions(self, test_file, tmp_path):
        # Test handling of invalid permissions
        # Skip on Windows as permission handling differs
        if os.name != 'nt':
            no_access_dir = tmp_path / "no_access"
            no_access_dir.mkdir()
            os.chmod(no_access_dir, 0o000)
            
            with pytest.raises(PermissionError):
                backup_file(test_file, str(no_access_dir))
            
            # Cleanup
            os.chmod(no_access_dir, 0o700)

class TestCleanText:
    def test_unusual_terminators(self):
        text = "Hello\rWorld\r\nTest"
        assert clean_text(text) == "Hello World Test"
        
    def test_multiple_terminators(self):
        text = "Hello\r\r\nWorld\n\rTest"
        assert clean_text(text) == "Hello World Test"
        
    def test_whitespace_handling(self):
        text = "  Hello    World  \n  Test  "
        assert clean_text(text) == "Hello World Test"
        
    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

class TestIsSpam:
    def test_single_spam_keyword(self):
        subject = {"subject": "Get Rich Quick!"}
        assert is_spam(subject) is True
        
    def test_multiple_spam_keywords(self):
        subject = {"subject": "Free Money Fast Cash Now!"}
        assert is_spam(subject) is True
        
    def test_non_spam_subject(self):
        subject = {"subject": "Regular Business Meeting"}
        assert is_spam(subject) is False
        
    def test_empty_subject(self):
        assert is_spam({}) is False
        assert is_spam({"subject": ""}) is False
        assert is_spam({"subject": None}) is False

