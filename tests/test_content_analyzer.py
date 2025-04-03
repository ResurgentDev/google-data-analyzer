#!/usr/bin/env python3
"""
Tests for the content_analyzer module.

These tests cover the functionality of the content_analyzer module, including:
- Analyzing plain text content
- Analyzing HTML content
- Analyzing multipart messages
- Handling attachments
- Size calculations
- Content type detection
- Character set handling
"""

import os
import email
import pytest
from collections import Counter, defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.header import Header

# Import the module to test
from src.content_analyzer import (
    analyze_content,
    get_filename_from_part,
    decode_header_value,
    format_size,
    extract_content_type,
    extract_content_charset,
    is_attachment,
    get_attachment_details,
    calculate_total_content_size,
    extract_text_content,
    extract_html_content,
    get_all_attachments
)


# Test Fixtures for different types of email content
@pytest.fixture
def plain_text_email():
    """Creates a simple plain text email."""
    msg = MIMEText("This is a plain text email for testing.")
    msg["Subject"] = "Plain Text Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def html_email():
    """Creates a simple HTML email."""
    html_content = """
    <html>
    <body>
        <h1>Test HTML Email</h1>
        <p>This is an <b>HTML</b> email for testing.</p>
    </body>
    </html>
    """
    msg = MIMEText(html_content, "html")
    msg["Subject"] = "HTML Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def multipart_email():
    """Creates a multipart email with text and HTML parts."""
    msg = MIMEMultipart("alternative")
    text_part = MIMEText("This is the plain text version.", "plain")
    html_part = MIMEText("<p>This is the <b>HTML</b> version.</p>", "html")
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    msg["Subject"] = "Multipart Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def email_with_attachment():
    """Creates an email with a text attachment."""
    msg = MIMEMultipart()
    msg.attach(MIMEText("Email with attachment for testing.", "plain"))
    
    # Create a text attachment
    attachment = MIMEText("This is a text file attachment.", "plain")
    attachment.add_header("Content-Disposition", "attachment", filename="test.txt")
    msg.attach(attachment)
    
    msg["Subject"] = "Attachment Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def email_with_multiple_attachments():
    """Creates an email with multiple attachments of different types."""
    msg = MIMEMultipart()
    msg.attach(MIMEText("Email with multiple attachments.", "plain"))
    
    # Text file attachment
    text_attach = MIMEText("This is a text file attachment.", "plain")
    text_attach.add_header("Content-Disposition", "attachment", filename="test.txt")
    msg.attach(text_attach)
    
    # PDF attachment (simulated)
    pdf_content = b"%PDF-1.5\nSome binary content to simulate a PDF file."
    pdf_attach = MIMEApplication(pdf_content, _subtype="pdf")
    pdf_attach.add_header("Content-Disposition", "attachment", filename="test.pdf")
    msg.attach(pdf_attach)
    
    # Image attachment (simulated)
    img_content = b"Simulated JPEG image content"
    img_attach = MIMEImage(img_content, _subtype="jpeg")
    img_attach.add_header("Content-Disposition", "attachment", filename="image.jpg")
    msg.attach(img_attach)
    
    msg["Subject"] = "Multiple Attachments Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def email_with_encoded_headers():
    """Creates an email with encoded headers and filename."""
    msg = MIMEMultipart()
    msg.attach(MIMEText("Email with encoded headers and filename.", "plain"))
    
    # Add attachment with encoded filename
    attachment = MIMEText("Content of the file with non-ASCII name.", "plain")
    filename = Header("Тестовый_файл.txt", "utf-8").encode()  # Russian text for "Test_file.txt"
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)
    
    # Set encoded subject
    msg["Subject"] = Header("Тестовый Email", "utf-8").encode()  # Russian text for "Test Email"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


@pytest.fixture
def email_with_non_standard_charset():
    """Creates an email with non-standard charset."""
    # Create text with ISO-8859-1 encoding (Latin-1)
    text = "This contains special characters like é, ñ, and ü."
    part = MIMEText(text.encode("iso-8859-1"), "plain", "iso-8859-1")
    
    msg = MIMEMultipart()
    msg.attach(part)
    
    msg["Subject"] = "Charset Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    return msg


# Tests for analyze_content function
def test_analyze_plain_text_content(plain_text_email):
    """Test analyzing plain text email content."""
    plain_text_size, html_size, attachment_info = analyze_content(plain_text_email, 0)
    
    # Check sizes
    assert plain_text_size > 0, "Plain text size should be greater than 0"
    assert html_size == 0, "HTML size should be 0 for plain text email"
    
    # Check attachment info
    assert isinstance(attachment_info["counts_by_type"], Counter)
    assert isinstance(attachment_info["sizes_by_type"], defaultdict)
    assert sum(attachment_info["counts_by_type"].values()) == 0, "No attachments expected"


def test_analyze_html_content(html_email):
    """Test analyzing HTML email content."""
    plain_text_size, html_size, attachment_info = analyze_content(html_email, 0)
    
    # Check sizes
    assert plain_text_size == 0, "Plain text size should be 0 for HTML email"
    assert html_size > 0, "HTML size should be greater than 0"
    
    # Check attachment info
    assert sum(attachment_info["counts_by_type"].values()) == 0, "No attachments expected"


def test_analyze_multipart_content(multipart_email):
    """Test analyzing multipart email content."""
    plain_text_size, html_size, attachment_info = analyze_content(multipart_email, 0)
    
    # Check sizes
    assert plain_text_size > 0, "Plain text size should be greater than 0"
    assert html_size > 0, "HTML size should be greater than 0"
    
    # Check attachment info
    assert sum(attachment_info["counts_by_type"].values()) == 0, "No attachments expected"


def test_analyze_email_with_attachment(email_with_attachment):
    """Test analyzing email with attachment."""
    plain_text_size, html_size, attachment_info = analyze_content(email_with_attachment, 0)
    
    # Check content sizes
    assert plain_text_size > 0, "Plain text size should be greater than 0"
    
    # Check attachment info
    assert sum(attachment_info["counts_by_type"].values()) == 1, "Expected 1 attachment"
    assert ".txt" in attachment_info["counts_by_type"], "Expected .txt attachment"
    assert attachment_info["counts_by_type"][".txt"] == 1, "Expected 1 .txt attachment"
    assert len(attachment_info["sizes_by_type"][".txt"]) == 1, "Expected 1 size for .txt"
    assert attachment_info["sizes_by_type"][".txt"][0] > 0, "Attachment size should be > 0"


def test_analyze_email_with_multiple_attachments(email_with_multiple_attachments):
    """Test analyzing email with multiple attachments."""
    plain_text_size, html_size, attachment_info = analyze_content(email_with_multiple_attachments, 0)
    
    # Check content sizes
    assert plain_text_size > 0, "Plain text size should be greater than 0"
    
    # Check attachment counts
    attachment_counts = attachment_info["counts_by_type"]
    assert sum(attachment_counts.values()) == 3, "Expected 3 attachments"
    assert attachment_counts[".txt"] == 1, "Expected 1 .txt attachment"
    assert attachment_counts[".pdf"] == 1, "Expected 1 .pdf attachment"
    assert attachment_counts[".jpg"] == 1, "Expected 1 .jpg attachment"
    
    # Check attachment sizes
    attachment_sizes = attachment_info["sizes_by_type"]
    assert len(attachment_sizes[".txt"]) == 1, "Expected 1 size for .txt"
    assert len(attachment_sizes[".pdf"]) == 1, "Expected 1 size for .pdf"
    assert len(attachment_sizes[".jpg"]) == 1, "Expected 1 size for .jpg"


# Tests for filename extraction
def test_get_filename_from_part(email_with_attachment):
    """Test extracting filename from a message part."""
    # Get the attachment part
    for part in email_with_attachment.walk():
        if part.get_filename():
            filename = get_filename_from_part(part)
            assert filename == "test.txt", f"Expected 'test.txt', got '{filename}'"
            return
    
    pytest.fail("No attachment part found with filename")


def test_get_filename_from_encoded_part(email_with_encoded_headers):
    """Test extracting encoded filename from a message part."""
    # Get the attachment part with encoded filename
    for part in email_with_encoded_headers.walk():
        if part.get_filename():
            filename = get_filename_from_part(part)
            assert "Тестовый_файл.txt" in filename, "Expected Cyrillic filename"
            return
    
    pytest.fail("No attachment part found with encoded filename")


# Tests for header value decoding
def test_decode_header_value():
    """Test decoding various header values."""
    # Test plain ASCII
    assert decode_header_value("Simple text") == "Simple text"
    
    # Test encoded header
    encoded_header = Header("Тестовый Email", "utf-8").encode()
    decoded = decode_header_value(encoded_header)
    assert "Тестовый Email" in decoded, "Expected Cyrillic text in decoded header"
    
    # Test empty header
    assert decode_header_value("") == ""
    assert decode_header_value(None) == ""


# Tests for size formatting
def test_format_size():
    """Test formatting byte sizes to human-readable format."""
    assert format_size(0) == "0.00 B"
    assert format_size(1023) == "1023.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1024 * 1024) == "1.00 MB"
    assert format_size(1024 * 1024 * 1024) == "1.00 GB"
    assert format_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"


# Tests for content type extraction
def test_extract_content_type(plain_text_email, html_email):
    """Test extracting content type from message parts."""
    assert extract_content_type(plain_text_email) == "text/plain"
    assert extract_content_type(html_email) == "text/html"


# Tests for charset extraction
def test_extract_content_charset(email_with_non_standard_charset):
    """Test extracting charset from message parts."""
    # Find the part with the non-standard charset
    for part in email_with_non_standard_charset.walk():
        if not part.is_multipart():
            charset = extract_content_charset(part)
            assert charset.lower() == "iso-8859-1", f"Expected 'iso-8859-1', got '{charset}'"
            return
    
    pytest.fail("No part found with non-standard charset")


# Tests for attachment detection
def test_is_attachment(email_with_attachment):
    """Test detecting if a part is an attachment."""
    # Find an attachment part
    attachment_found = False
    for part in email_with_attachment.walk():
        if not part.is_multipart() and part.get_filename():
            attachment_found = True
            assert is_attachment(part), "Part with filename should be detected as attachment"
    
    assert attachment_found, "No attachment part found"


# Tests for attachment details
def test_get_attachment_details(email_with_attachment):
    """Test getting detailed information about an attachment."""
    # Find an attachment part
    for part in email_with_attachment.walk():
        if not part.is_multipart() and part.get_filename():
            details = get_attachment_details(part)
            
            # Check expected fields
            assert details["filename"] == "test.txt"
            assert details["size"] > 0
            assert "size_human" in details
            assert details["content_type"] == "text/plain"
            assert details["extension"] == ".txt"
            assert "disposition" in details
            return
    
    pytest.fail("No attachment part found")


# Tests for content size calculations
def test_calculate_total_content_size():
    """Test calculating total content size from different components."""
    plain_text_sizes = [100, 200, 300]
    html_sizes = [500, 700]
    attachment_sizes = {
        ".txt": [150, 250],
        ".pdf": [2000],
        ".jpg": [1500, 1800]
    }
    
    total_size = calculate_total_content_size(plain_text_sizes, html_sizes, attachment_sizes)
    expected_size = sum(plain_text_sizes) + sum(html_sizes) + \
                   sum(attachment_sizes[".txt"]) + \
                   sum(attachment_sizes[".pdf"]) + \
                   sum(attachment_sizes[".jpg"])
    
    assert total_size == expected_size, f"Expected {expected_size}, got {total_size}"


# Tests for text content extraction
def test_extract_text_content(plain_text_email, multipart_email):
    """Test extracting plain text content from emails."""
    # Test with plain text email
    text_content = extract_text_content(plain_text_email)
    assert text_content == "This is a plain text email for testing."
    
    # Test with multipart email (should extract the plain text part)
    text_content = extract_text_content(multipart_email)
    assert text_content == "This is the plain text version."
    
    # Test with a message that has no text content
    msg = MIMEMultipart()
    msg.attach(MIMEImage(b"fake image data", _subtype="jpeg"))
    assert extract_text_content(msg) == "", "Should return empty string when no text content"


def test_extract_html_content(html_email, multipart_email):
    """Test extracting HTML content from emails."""
    # Test with HTML email
    html_content = extract_html_content(html_email)
    assert "<h1>Test HTML Email</h1>" in html_content
    assert "<b>HTML</b>" in html_content
    
    # Test with multipart email (should extract the HTML part)
    html_content = extract_html_content(multipart_email)
    assert "<b>HTML</b>" in html_content
    
    # Test with a message that has no HTML content
    msg = MIMEMultipart()
    msg.attach(MIMEText("Plain text only", "plain"))
    assert extract_html_content(msg) == "", "Should return empty string when no HTML content"


def test_extract_text_content_with_encoding(email_with_non_standard_charset):
    """Test extracting text content with different character encodings."""
    text_content = extract_text_content(email_with_non_standard_charset)
    assert "special characters" in text_content
    assert "é" in text_content
    assert "ñ" in text_content
    assert "ü" in text_content


def test_get_all_attachments(email_with_multiple_attachments):
    """Test getting all attachments from an email."""
    attachments = get_all_attachments(email_with_multiple_attachments)
    
    # Verify we got all three attachments
    assert len(attachments) == 3, "Expected 3 attachments"
    
    # Check that we have the correct file types
    attachment_names = [a["filename"] for a in attachments]
    attachment_types = [a["content_type"] for a in attachments]
    attachment_extensions = [a["extension"] for a in attachments]
    
    assert "test.txt" in attachment_names
    assert "test.pdf" in attachment_names
    assert "image.jpg" in attachment_names
    
    assert "text/plain" in attachment_types
    assert "application/pdf" in attachment_types
    assert "image/jpeg" in attachment_types
    
    assert ".txt" in attachment_extensions
    assert ".pdf" in attachment_extensions
    assert ".jpg" in attachment_extensions
    
    # Verify each attachment has all the required fields
    for attachment in attachments:
        assert "filename" in attachment
        assert "size" in attachment
        assert "size_human" in attachment
        assert "content_type" in attachment
        assert "extension" in attachment
        assert "disposition" in attachment
        assert attachment["size"] > 0


def test_get_all_attachments_no_attachments(plain_text_email):
    """Test getting attachments from an email with no attachments."""
    attachments = get_all_attachments(plain_text_email)
    assert len(attachments) == 0, "Expected no attachments"


def test_get_all_attachments_single_part(email_with_encoded_headers):
    """Test getting attachments from a single part message."""
    # Extract just the attachment part
    for part in email_with_encoded_headers.walk():
        if is_attachment(part):
            # Create a new message with just this part
            content = part.get_payload(decode=True)
            msg = MIMEText(content, _subtype="plain")
            for header, value in part.items():
                msg[header] = value
            
            # Test get_all_attachments with this single part
            attachments = get_all_attachments(msg)
            assert len(attachments) == 1, "Expected 1 attachment"
            assert "Тестовый_файл.txt" in attachments[0]["filename"]
            break


def test_analyze_content_with_errors():
    """Test error handling in analyze_content function."""
    # Create a problematic message that will cause errors
    msg = MIMEMultipart()
    msg.attach(MIMEText("Test content", "plain"))
    
    # Add a part with invalid payload that will cause decode error
    bad_part = email.message.Message()
    bad_part.add_header("Content-Type", "image/jpeg")
    bad_part.add_header("Content-Disposition", "attachment", filename="bad.jpg")
    # Set a payload that will cause an error when decoded
    bad_part.set_payload("not base64 content but will try to decode as such")
    msg.attach(bad_part)
    
    # Using pytest.raises to check that the exception is properly raised
    with pytest.raises(Exception) as excinfo:
        analyze_content(msg, 999)
    
    # Check that the error message contains the message index
    assert "999" in str(excinfo.value) or "999" in excinfo.traceback[-1].line


def test_decode_header_value_with_errors():
    """Test error handling in header decoding."""
    # Create a deliberately malformed header that would cause error
    malformed_header = b"=?invalid-encoding?B?invalid_base64_data?="
    
    # Should handle the error and return a fallback string
    result = decode_header_value(malformed_header)
    assert isinstance(result, str), "Result should be a string even with errors"
    assert result, "Result should not be empty"


def test_charset_fallback_handling():
    """Test handling of fallback charset when decoding content."""
    # Create a message with invalid charset
    text = "Content with special chars: éñü"
    msg = MIMEText(text.encode("utf-8"))
    msg.set_param("charset", "invalid-charset")
    
    # Extract content - should fall back to utf-8
    content = extract_text_content(msg)
    assert "éñü" in content, "Special characters should be preserved with charset fallback"

