import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_file(filepath: str, archive_dir: str = "archives") -> str:
    """
    Create a backup of the specified file in the archive directory.
    
    Args:
        filepath: Path to the file to backup
        archive_dir: Directory where backups will be stored (default: 'archives')
        
    Returns:
        str: Full path to the created backup file
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        PermissionError: If there are insufficient permissions
    """
    # Convert to absolute Path objects for better path handling
    source_path = Path(filepath).resolve()
    archive_path = Path(archive_dir).resolve()
    
    # Check if source file exists
    if not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {filepath}")
    
    # Create archive directory if it doesn't exist
    archive_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for the backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{source_path.name}.{timestamp}.bak"
    backup_path = archive_path / backup_filename
    
    # Create the backup
    shutil.copy2(source_path, backup_path)
    
    return str(backup_path)

# utils.py - Created 09.03.2025

def clean_text(text: str) -> str:
    """
    Clean text by normalizing line endings and whitespace.
    
    Args:
        text: The text to clean
        
    Returns:
        str: The cleaned text
    """
    if text is None:
        return ""
    
    # Replace all types of line endings with spaces
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    
    # Normalize whitespace
    words = text.split()
    return ' '.join(words)

def is_spam(message: dict) -> bool:
    """
    Check if a message is spam based on its subject.
    
    Args:
        message: Dictionary containing message details with optional 'subject' key
        
    Returns:
        bool: True if the message is considered spam, False otherwise
    """
    if not message or 'subject' not in message or not message['subject']:
        return False
        
    subject = message['subject'].lower()
    spam_keywords = {'get rich', 'quick', 'free money', 'fast cash'}
    
    # Check for individual words and phrases
    words = set(subject.split())
    for keyword in spam_keywords:
        if keyword in subject or keyword.replace(' ', '') in ''.join(words):
            return True
    
    return False
