"""
Email Utilities Module

This module provides functions for handling and processing email-related data:
- Email header parsing and decoding
- Email address extraction and validation
- Date parsing and formatting
- Character set handling and encoding conversion

These utilities help to properly extract, normalize, and validate email data
for further analysis.
"""

import re
import email
import email.header
import email.utils
import datetime
from typing import List, Tuple, Optional, Dict, Any, Union
import logging

# Regular expression for validating email addresses
# This follows RFC 5322 with some practical limitations
# Ensures:
# - Username contains valid characters
# - Domain doesn't start or end with hyphen
# - Domain has at least one dot and valid TLD
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?')

def decode_header(header_value: str) -> str:
    """
    Decode email header value, handling multiple encodings and charsets.
    
    Args:
        header_value: The raw header value string to decode
        
    Returns:
        Decoded and normalized header string
    """
    if not header_value:
        return ""
    
    try:
        decoded_header = ""
        for decoded_part, charset in email.header.decode_header(header_value):
            if isinstance(decoded_part, bytes):
                if charset:
                    # Use specified charset
                    try:
                        decoded_header += decoded_part.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        # Fallback to utf-8 or latin-1 if the specified charset fails
                        try:
                            decoded_header += decoded_part.decode('utf-8')
                        except UnicodeDecodeError:
                            decoded_header += decoded_part.decode('latin-1', errors='replace')
                else:
                    # Try utf-8 first, then latin-1 as fallback
                    try:
                        decoded_header += decoded_part.decode('utf-8')
                    except UnicodeDecodeError:
                        decoded_header += decoded_part.decode('latin-1', errors='replace')
            else:
                # Already a string
                decoded_header += decoded_part
        
        return decoded_header.strip()
    except Exception as e:
        logging.warning(f"Error decoding header '{header_value}': {str(e)}")
        # Return original if decoding fails
        return header_value

def normalize_header_value(value: Optional[str]) -> str:
    """
    Normalize header value by decoding and cleaning up whitespace.
    
    Args:
        value: The header value to normalize
        
    Returns:
        Normalized header value as string
    """
    if not value:
        return ""
    
    # Decode the header value
    decoded = decode_header(value)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', decoded)
    
    return normalized.strip()

def normalize_header(header_name: str) -> str:
    """
    Normalizes email header names to a standard format.
    
    Args:
        header_name (str): The header name to normalize
    
    Returns:
        str: Normalized header name
    """
    if not header_name:
        return ""
    
    # First normalize the value
    normalized = normalize_header_value(header_name)
    
    # Convert to title case with hyphen handling
    parts = normalized.split('-')
    normalized_parts = [part.capitalize() for part in parts]
    
    return '-'.join(normalized_parts)

def extract_email_addresses(text: str) -> List[str]:
    """
    Extract email addresses from a string.
    
    Args:
        text: Text containing email addresses
        
    Returns:
        List of extracted email addresses
    """
    if not text:
        return []
    
    # First try email.utils parser for structured format
    parsed_addresses = []
    
    # Handle comma-separated address lists
    for part in text.split(','):
        try:
            # Parse using email.utils for RFC-compliant addresses
            for name, addr in email.utils.getaddresses([part]):
                if addr and '@' in addr:
                    parsed_addresses.append(addr.lower())
        except Exception:
            pass
    
    # If nothing was found, use regex as fallback
    if not parsed_addresses:
        parsed_addresses = [email.lower() for email in EMAIL_REGEX.findall(text)]
    
    # Filter valid emails and remove duplicates while preserving order
    unique_addresses = []
    for addr in parsed_addresses:
        if addr not in unique_addresses and validate_email(addr):
            unique_addresses.append(addr)
    
    return unique_addresses

def validate_email(email_addr: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email_addr: Email address to validate
        
    Returns:
        True if the email address is valid, False otherwise
    """
    if not email_addr:
        return False
    
    # Basic format check with regex
    if not EMAIL_REGEX.fullmatch(email_addr):
        return False
    
    # Additional validations
    if email_addr.count('@') != 1:
        return False
    
    # Split into username and domain parts
    username, domain = email_addr.split('@')
    
    # Check username part
    if not username:
        return False
    
    # Check for domain part
    if not domain or '.' not in domain:
        return False
    
    # Check for domains starting or ending with hyphen
    domain_parts = domain.split('.')
    for part in domain_parts:
        if not part:  # Empty part (e.g., test@domain..com)
            return False
        if part.startswith('-') or part.endswith('-'):
            return False
    
    # Check TLD is at least 2 chars and not all numeric
    tld = domain_parts[-1]
    if len(tld) < 2 or tld.isdigit():
        return False
    
    # Check domain format
    if len(domain_parts) < 2:  # Must have at least one dot
        return False
    
    return True

def get_domain_from_email(email_addr: str) -> str:
    """
    Extract domain part from an email address.
    
    Args:
        email_addr: Email address to extract domain from
        
    Returns:
        Domain part of the email address
        
    Raises:
        ValueError: If the email address is invalid
    """
    if not email_addr:
        raise ValueError("Email address cannot be empty")
    
    # Validate email using validate_email function
    if not validate_email(email_addr):
        raise ValueError(f"Invalid email address format: {email_addr}")
    
    # At this point, we know the email is valid and contains '@'
    username, domain = email_addr.split('@')
    return domain.lower()

def extract_subject_keywords(subject: str, min_length: int = 3) -> List[str]:
    """
    Extract meaningful keywords from an email subject line.
    
    Args:
        subject: Email subject line
        min_length: Minimum keyword length to consider
        
    Returns:
        List of extracted keywords
    """
    if not subject:
        return []
    
    # Normalize and decode subject
    normalized_subject = normalize_header_value(subject)
    
    # Remove common prefixes like Re:, Fwd:, etc.
    clean_subject = re.sub(r'^(re|fwd|fw):\s*', '', normalized_subject, flags=re.IGNORECASE)
    
    # Split into words and filter common words/short words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'nor', 'on', 'at', 'to', 'from', 
                    'by', 'in', 'of', 'with', 'about', 'as', 'into', 'like', 'through', 'after', 
                    'over', 'between', 'out', 'up', 'down', 'off', 'above', 'under'}
    
    words = re.findall(r'\b[a-z0-9]+\b', clean_subject.lower())
    keywords = [word for word in words if len(word) >= min_length and word not in common_words]
    
    return keywords

def parse_date(date_str: str) -> datetime.datetime:
    """
    Parse date string from email headers into datetime object.
    
    Args:
        date_str: Date string from email header
        
    Returns:
        Naive datetime object (without timezone info) after converting to UTC
        if the input had timezone information.
    
    Raises:
        ValueError: If the date string cannot be parsed
    """
    if not date_str:
        raise ValueError("Empty date string")
    
    # Normalize date string (clean up multiple spaces)
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    
    # Track if original string had timezone info
    has_timezone = any(x in date_str for x in ['+', '-', 'GMT', 'UTC', 'EST', 'EDT', 'PST', 'PDT', 'Z'])
    
    # Try email.utils parser first (handles RFC 2822 format)
    try:
        timestamp = email.utils.parsedate_to_datetime(date_str)
        # Convert to UTC if it has timezone info
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(datetime.timezone.utc)
            # Always strip timezone info for RFC 2822 dates
            timestamp = timestamp.replace(tzinfo=None)
        return timestamp
    except (TypeError, ValueError):
        pass
    
    # Try additional date formats
    date_formats = [
        # Standard formats
        '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
        '%d %b %Y %H:%M:%S %z',      # Common variant
        '%a, %d %b %Y %H:%M:%S',     # Without timezone
        '%d %b %Y %H:%M:%S',         # Without day and timezone
        '%d-%b-%Y %H:%M:%S',         # Dash format
        '%Y-%m-%d %H:%M:%S',         # ISO-like format
        '%m/%d/%Y %H:%M:%S',         # US format
        '%d/%m/%Y %H:%M:%S',         # European format
    ]
    
    # Try each format
    for fmt in date_formats:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            # Check if format has timezone
            format_has_timezone = '%z' in fmt
            
            # Handle timezone based on format and original string
            if format_has_timezone and dt.tzinfo is not None:
                # Convert to UTC
                dt = dt.astimezone(datetime.timezone.utc)
                # Strip timezone info for ISO dates
                dt = dt.replace(tzinfo=None)
            elif not format_has_timezone and dt.tzinfo is None:
                # No timezone in format or parsed datetime, keep as-is
                pass
            elif not format_has_timezone and dt.tzinfo is not None:
                # Format doesn't have timezone but datetime does (unusual)
                # Convert to UTC and strip timezone info
                dt = dt.astimezone(datetime.timezone.utc)
                dt = dt.replace(tzinfo=None)
            
            return dt
        except ValueError:
            continue
    
    # If all else fails, try a more lenient approach with dateutil
    try:
        from dateutil import parser
        dt = parser.parse(date_str)
        
        # Handle timezone based on parsed result and original string
        if dt.tzinfo is not None:
            # Convert to UTC
            dt = dt.astimezone(datetime.timezone.utc)
            # Always strip timezone info after conversion to UTC
            dt = dt.replace(tzinfo=None)
        
        return dt
    except ImportError:
        pass
    except ValueError as e:
        # Let this propagate to show specific parsing error
        raise ValueError(f"Failed to parse date: {date_str}. Error: {str(e)}")
    
    # If we get here, all parsing attempts failed
    raise ValueError(f"Unrecognized date format: {date_str}")

def handle_character_set(content: Union[bytes, str], charset: str = None, target_charset: str = None) -> str:
    """
    Handle character set conversion for email content.
    
    Args:
        content: Content to decode, can be bytes or string
        charset: Source character set to use for decoding (if content is bytes)
        target_charset: Target character set for conversion (if different from source)
        
    Returns:
        Decoded string in the target character set
    """
    if not content:
        return ""
    
    # If content is already a string, no need for initial decoding
    if isinstance(content, str):
        decoded_text = content
    else:
        # If content is bytes, decode it
        if charset:
            try:
                decoded_text = content.decode(charset)
            except (UnicodeDecodeError, LookupError):
                # Fallback if specified charset fails
                pass
            else:
                # If successful, skip to charset conversion step
                if target_charset:
                    return _convert_charset(decoded_text, target_charset)
                return decoded_text
        
        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-16', 'ascii']
        
        for encoding in encodings:
            try:
                decoded_text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:  # No break occurred, all decoding attempts failed
            # Last resort: force latin-1 (which never fails)
            decoded_text = content.decode('latin-1', errors='replace')
    
    # Convert charset if needed
    if target_charset:
        return _convert_charset(decoded_text, target_charset)
    
    return decoded_text

def _convert_charset(text: str, target_charset: str) -> str:
    """
    Convert a string to a different character set.
    
    Args:
        text: String to convert
        target_charset: Target character set
        
    Returns:
        String encoded in the target character set and then decoded back to unicode
    """
    if not text or not target_charset:
        return text
    
    try:
        # Encode to bytes in the target charset, then decode back to string
        return text.encode(target_charset, errors='replace').decode(target_charset, errors='replace')
    except (UnicodeEncodeError, UnicodeDecodeError, LookupError) as e:
        logging.warning(f"Error converting charset to {target_charset}: {str(e)}")
        return text  # Return original if conversion fails

def get_sender(message: email.message.Message) -> str:
    """
    Extract the sender's email address from an email message.
    
    Args:
        message: Email message object
        
    Returns:
        Sender's email address or empty string if not found
    """
    if not message:
        return ""
    
    # Try From header first
    from_header = message.get('From', '')
    if from_header:
        addresses = extract_email_addresses(from_header)
        if addresses:
            return addresses[0]
    
    # Fallback to Sender header
    sender_header = message.get('Sender', '')
    if sender_header:
        addresses = extract_email_addresses(sender_header)
        if addresses:
            return addresses[0]
    
    # Fallback to Return-Path header
    return_path = message.get('Return-Path', '')
    if return_path:
        addresses = extract_email_addresses(return_path)
        if addresses:
            return addresses[0]
    
    return ""

def get_recipients(message: email.message.Message) -> List[str]:
    """
    Extract all recipient email addresses from an email message.
    
    Args:
        message: Email message object
        
    Returns:
        List of recipient email addresses
    """
    if not message:
        return []
    
    recipients = []
    
    # Check all recipient headers
    for header in ['To', 'Cc', 'Bcc']:
        header_value = message.get(header, '')
        if header_value:
            recipients.extend(extract_email_addresses(header_value))
    
    # Remove duplicates while preserving order
    unique_recipients = []
    for recipient in recipients:
        if recipient not in unique_recipients:
            unique_recipients.append(recipient)
    
    return unique_recipients

def get_header_addresses(header_value: str) -> List[Tuple[str, str]]:
    """
    Parse a header value containing email addresses into (name, address) tuples.
    
    Args:
        header_value: Header value containing addresses
        
    Returns:
        List of (name, address) tuples
    """
    if not header_value:
        return []
    
    try:
        # Parse addresses using email.utils
        parsed = email.utils.getaddresses([header_value])
        
        # Decode names and normalize addresses
        result = []
        for name, addr in parsed:
            if addr:  # Only include if there's an actual address
                decoded_name = decode_header(name)
                result.append((decoded_name, addr.lower()))
        
        return result
    except Exception as e:
        logging.warning(f"Error parsing header addresses '{header_value}': {str(e)}")
        return []

def parse_address(address_string: str) -> Tuple[str, str]:
    """
    Parses an email address string into name and address components.
    
    Args:
        address_string: String containing an email address with optional display name
    
    Returns:
        tuple: (name, email_address)
    """
    if not address_string:
        return ("", "")
    
    name, email_address = email.utils.parseaddr(address_string)
    
    # Decode the name if needed
    if name:
        name = decode_header(name)
        
    return (name, email_address)

def extract_message_id(message: email.message.Message) -> str:
    """
    Extract Message-ID from an email message.
    
    Args:
        message: Email message object
        
    Returns:
        Message-ID string or empty string if not found
    """
    if not message:
        return ""
    
    message_id = message.get('Message-ID', '')
    if not message_id:
        message_id = message.get('Message-Id', '')  # Alternative capitalization
    
    # Clean up
    message_id = message_id.strip()
    if message_id.startswith('<') and message_id.endswith('>'):
        message_id = message_id[1:-1]  # Remove angle brackets
    
    return message_id

def get_reply_to(message: email.message.Message) -> List[str]:
    """
    Extract Reply-To addresses from an email message.
    
    Args:
        message: Email message object
        
    Returns:
        List of Reply-To email addresses
    """
    if not message:
        return []
    
    reply_to = message.get('Reply-To', '')
    if not reply_to:
        return []
    
    return extract_email_addresses(reply_to)

def is_auto_reply(message: email.message.Message) -> bool:
    """
    Determine if a message is an automatic reply based on headers.
    
    Args:
        message: Email message object
        
    Returns:
        True if the message appears to be an auto-reply, False otherwise
    """
    if not message:
        return False
    
    # Check for common auto-reply indicators in headers
    auto_reply_headers = [
        ('Auto-Submitted', lambda v: v.lower() != 'no'),
        ('X-Auto-Response-Suppress', lambda v: True),
        ('Precedence', lambda v: v.lower() in ['auto_reply', 'auto-reply', 'bulk', 'junk']),
        ('X-Autoreply', lambda v: True),
        ('X-AutoReply', lambda v: True),
        ('X-Autorespond', lambda v: True)
    ]
    
    for header, test_func in auto_reply_headers:
        if header in message and test_func(message[header]):
            return True
    
    # Check common subject prefixes
    subject = normalize_header_value(message.get('Subject', ''))
    auto_subject_prefixes = ['auto:', 'automatic reply:', 'out of office:', 'autoreply:',
                             'auto response:', 'vacation response:']
    
    for prefix in auto_subject_prefixes:
        if subject.lower().startswith(prefix):
            return True
    
    return False

def get_header_charsets(message):
    """
    Extracts character sets used in all headers of an email message.
    
    Args:
        message: Email message object
        
    Returns:
        set: Set of character sets used in the message headers
    """
    charsets = set()
    
    for header, value in message.items():
        parts = email.header.decode_header(value)
        for part, charset in parts:
            if charset:
                charsets.add(charset.lower())
    
    return charsets

