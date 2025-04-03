#!/usr/bin/env python3
"""
Content Analyzer Module

This module provides functions for analyzing email content, including:
- Extracting and analyzing plain text and HTML content
- Analyzing and processing email attachments
- Calculating content sizes
- Handling MIME types and content disposition

The module is designed to work with email.message.Message objects from the Python standard library.
"""

import os
import re
import email
import logging
from collections import Counter, defaultdict


# Configure logging
logger = logging.getLogger(__name__)


def analyze_content(message, report, msg_idx):
    """
    Analyzes body content and attachments of an email message and updates the report dictionary.
    
    Args:
        message (email.message.Message): The email message to analyze
        report (dict): The report dictionary to update with content analysis
        msg_idx (int): Index of the message in the mailbox
    """
    # Initialize content containers
    plain_text_size = 0
    html_size = 0
    attachment_counts = Counter()
    attachment_sizes = defaultdict(list)
    
    try:
        # Handle single part messages
        if not message.is_multipart():
            content_type = message.get_content_type()
            content = message.get_payload(decode=True)
            content_size = len(content) if content else 0
            
            if content_type == 'text/plain':
                plain_text_size += content_size
            elif content_type == 'text/html':
                html_size += content_size
            else:
                # Treat as attachment
                filename = get_filename_from_part(message)
                if filename:
                    extension = os.path.splitext(filename)[1].lower()
                    attachment_counts[extension or 'unknown'] += 1
                    attachment_sizes[extension or 'unknown'].append(content_size)
        
        # Handle multipart messages
        else:
            for part in message.walk():
                if part.is_multipart():
                    continue
                
                content_type = part.get_content_type()
                content = part.get_payload(decode=True)
                content_size = len(content) if content else 0
                
                # Check for main body parts
                if content_type == 'text/plain':
                    plain_text_size += content_size
                elif content_type == 'text/html':
                    html_size += content_size
                
                # Check for attachments
                filename = get_filename_from_part(part)
                disposition = part.get('Content-Disposition', '')
                
                if filename or 'attachment' in disposition:
                    extension = os.path.splitext(filename)[1].lower() if filename else ''
                    attachment_counts[extension or 'unknown'] += 1
                    attachment_sizes[extension or 'unknown'].append(content_size)
                    
    except Exception as e:
        logger.warning(f"Error analyzing content in message {msg_idx}: {str(e)}")
        raise
    
    # Update the report dictionary with content analysis
    if 'content' not in report:
        report['content'] = {
            "body_sizes": {
                "plain_text": [],
                "html": []
            },
            "attachments": {
                "counts_by_type": Counter(),
                "sizes_by_type": defaultdict(list)
            }
        }
    
    # Add body sizes - append to lists
    if plain_text_size > 0:
        report['content']['body_sizes']['plain_text'].append(plain_text_size)
    if html_size > 0:
        report['content']['body_sizes']['html'].append(html_size)
    
    # Add attachment info - update counters and lists
    for ext, count in attachment_counts.items():
        report['content']['attachments']['counts_by_type'][ext] += count
    
    for ext, sizes in attachment_sizes.items():
        report['content']['attachments']['sizes_by_type'][ext].extend(sizes)


def get_filename_from_part(part):
    """
    Extracts filename from a message part.
    
    Args:
        part (email.message.Message): Email message part
        
    Returns:
        str: Filename or empty string
    """
    filename = part.get_filename()
    if filename:
        filename = decode_header_value(filename)
    return filename or ""


def decode_header_value(header_value):
    """
    Decodes email header values properly.
    
    Args:
        header_value: The email header value to decode
        
    Returns:
        str: Decoded header value
    """
    if not header_value:
        return ""
    
    try:
        decoded_parts = []
        for part, encoding in email.header.decode_header(header_value):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_parts.append(part.decode(encoding))
                    except (LookupError, UnicodeDecodeError):
                        decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        return ' '.join(decoded_parts)
    except Exception as e:
        logger.warning(f"Error decoding header: {str(e)}")
        return str(header_value)


def format_size(size_bytes):
    """
    Formats a byte size into a human-readable string.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def extract_content_type(part):
    """
    Extracts the content type from a message part.
    
    Args:
        part (email.message.Message): Email message part
        
    Returns:
        str: Content type (e.g., 'text/plain', 'image/jpeg')
    """
    return part.get_content_type()


def extract_content_charset(part):
    """
    Extracts the charset from a message part.
    
    Args:
        part (email.message.Message): Email message part
        
    Returns:
        str: Charset or None if not specified
    """
    content_type = part.get('Content-Type', '')
    match = re.search(r'charset="?([^";]+)"?', content_type)
    return match.group(1) if match else None


def is_attachment(part):
    """
    Determines if a message part is an attachment.
    
    Args:
        part (email.message.Message): Email message part
        
    Returns:
        bool: True if the part is an attachment, False otherwise
    """
    disposition = part.get('Content-Disposition', '')
    filename = get_filename_from_part(part)
    
    # If the part has a filename or has 'attachment' in its disposition, it's an attachment
    return bool(filename) or 'attachment' in disposition


def get_attachment_details(part):
    """
    Gets detailed information about an attachment.
    
    Args:
        part (email.message.Message): Email message part
        
    Returns:
        dict: Attachment details including filename, size, type, etc.
    """
    filename = get_filename_from_part(part)
    content = part.get_payload(decode=True)
    content_size = len(content) if content else 0
    content_type = extract_content_type(part)
    disposition = part.get('Content-Disposition', '')
    
    # Determine file extension
    extension = os.path.splitext(filename)[1].lower() if filename else ''
    
    # Try to infer MIME type if not provided
    if not content_type or content_type == 'application/octet-stream':
        import mimetypes
        guessed_type = mimetypes.guess_type(filename)[0] if filename else None
        if guessed_type:
            content_type = guessed_type
    
    return {
        "filename": filename,
        "size": content_size,
        "size_human": format_size(content_size),
        "content_type": content_type,
        "extension": extension,
        "disposition": disposition
    }


def calculate_total_content_size(plain_text_sizes, html_sizes, attachment_sizes):
    """
    Calculates the total size of the parsed content.
    
    Args:
        plain_text_sizes (list): List of plain text content sizes
        html_sizes (list): List of HTML content sizes
        attachment_sizes (dict): Dictionary of attachment sizes by type
        
    Returns:
        int: Total size in bytes of all parsed content
    """
    total_size = 0
    
    # Add plain text sizes
    total_size += sum(plain_text_sizes)
    
    # Add HTML sizes
    total_size += sum(html_sizes)
    
    # Add attachment sizes
    for sizes in attachment_sizes.values():
        total_size += sum(sizes)
        
    return total_size


def extract_text_content(message):
    """
    Extracts plain text content from an email message.
    
    Args:
        message (email.message.Message): The email message
        
    Returns:
        str: Extracted plain text content
    """
    if not message.is_multipart():
        if message.get_content_type() == 'text/plain':
            payload = message.get_payload(decode=True)
            if payload:
                charset = extract_content_charset(message) or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except LookupError:
                    return payload.decode('utf-8', errors='replace')
        return ""
    
    # For multipart messages, find the text/plain part
    for part in message.walk():
        if not part.is_multipart() and part.get_content_type() == 'text/plain':
            payload = part.get_payload(decode=True)
            if payload:
                charset = extract_content_charset(part) or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except LookupError:
                    return payload.decode('utf-8', errors='replace')
    
    return ""


def extract_html_content(message):
    """
    Extracts HTML content from an email message.
    
    Args:
        message (email.message.Message): The email message
        
    Returns:
        str: Extracted HTML content
    """
    if not message.is_multipart():
        if message.get_content_type() == 'text/html':
            payload = message.get_payload(decode=True)
            if payload:
                charset = extract_content_charset(message) or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except LookupError:
                    return payload.decode('utf-8', errors='replace')
        return ""
    
    # For multipart messages, find the text/html part
    for part in message.walk():
        if not part.is_multipart() and part.get_content_type() == 'text/html':
            payload = part.get_payload(decode=True)
            if payload:
                charset = extract_content_charset(part) or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except LookupError:
                    return payload.decode('utf-8', errors='replace')
    
    return ""


def get_all_attachments(message):
    """
    Gets all attachments from an email message.
    
    Args:
        message (email.message.Message): The email message
        
    Returns:
        list: List of attachment details dictionaries
    """
    attachments = []
    
    if not message.is_multipart():
        # Check if single part message is an attachment
        if is_attachment(message):
            attachments.append(get_attachment_details(message))
        return attachments
    
    # For multipart messages, look at each part
    for part in message.walk():
        if not part.is_multipart() and is_attachment(part):
            attachments.append(get_attachment_details(part))
            
    return attachments

