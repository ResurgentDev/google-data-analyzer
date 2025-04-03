import unittest
import email
from email.header import Header
from email.message import Message
from email.mime.text import MIMEText
from io import StringIO
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest

# Import the module under test
from src.email_utils import (
    decode_header,
    extract_email_addresses,
    validate_email,
    extract_subject_keywords,
    get_domain_from_email,
    parse_date,
    handle_character_set,
    normalize_header_value,
    get_sender,
    get_recipients
)


class TestHeaderDecoding(unittest.TestCase):
    """Tests for header decoding functionality."""

    def test_basic_header_decoding(self):
        """Test decoding a simple header value."""
        header_value = "Simple header"
        self.assertEqual(decode_header(header_value), "Simple header")

    def test_utf8_header_decoding(self):
        """Test decoding a UTF-8 encoded header."""
        header = Header("Café au lait", "utf-8")
        self.assertEqual(decode_header(header.encode()), "Café au lait")

    def test_iso_8859_1_header_decoding(self):
        """Test decoding an ISO-8859-1 encoded header."""
        header = Header("Caffè è buono", "iso-8859-1")
        self.assertEqual(decode_header(header.encode()), "Caffè è buono")

    def test_quoted_printable_header_decoding(self):
        """Test decoding a quoted-printable encoded header."""
        # Create a quoted-printable encoded header
        header = "=?utf-8?q?Caf=C3=A9_au_lait?="
        self.assertEqual(decode_header(header), "Café au lait")

    def test_base64_header_decoding(self):
        """Test decoding a base64 encoded header."""
        # Create a base64 encoded header
        header = "=?utf-8?b?Q2Fmw6kgYXUgbGFpdA==?="
        self.assertEqual(decode_header(header), "Café au lait")

    def test_mixed_encoding_header_decoding(self):
        """Test decoding a header with mixed encoding parts."""
        # A header with multiple encoded parts
        header = "=?utf-8?q?Caf=C3=A9?= =?iso-8859-1?q?_au_lait?="
        self.assertEqual(decode_header(header), "Café au lait")

    def test_empty_header_decoding(self):
        """Test decoding an empty header."""
        self.assertEqual(decode_header(""), "")

    def test_normalize_header(self):
        """Test normalizing header values."""
        headers = [
            "  Multiple    Spaces  ",
            "\tTabs\tand\tspaces\t",
            "\nNewlines\n\n"
        ]
        expected = [
            "Multiple Spaces",
            "Tabs and spaces",
            "Newlines"
        ]
        for header, expected_value in zip(headers, expected):
            self.assertEqual(normalize_header_value(header), expected_value)


class TestEmailAddressExtraction(unittest.TestCase):
    """Tests for email address extraction and validation."""

    def test_simple_address_extraction(self):
        """Test extracting a simple email address."""
        from_header = "John Doe <john.doe@example.com>"
        self.assertEqual(extract_email_addresses(from_header), ["john.doe@example.com"])

    def test_multiple_address_extraction(self):
        """Test extracting multiple email addresses."""
        to_header = "John <john@example.com>, Jane <jane@example.com>, bob@example.com"
        self.assertEqual(
            extract_email_addresses(to_header),
            ["john@example.com", "jane@example.com", "bob@example.com"]
        )

    def test_address_extraction_with_display_names(self):
        """Test extracting addresses with display names containing special characters."""
        cc_header = '"Doe, John" <john.doe@example.com>, "O\'Reilly, Jane" <jane.oreilly@example.com>'
        self.assertEqual(
            extract_email_addresses(cc_header),
            ["john.doe@example.com", "jane.oreilly@example.com"]
        )

    def test_empty_address_extraction(self):
        """Test extracting from an empty header."""
        self.assertEqual(extract_email_addresses(""), [])

    def test_invalid_address_extraction(self):
        """Test extracting from headers with invalid addresses."""
        invalid_headers = [
            "John Doe without.an.email",
            "<invalid@>",
            "@missinguser.com"
        ]
        for header in invalid_headers:
            self.assertEqual(extract_email_addresses(header), [])

    def test_email_validation(self):
        """Test validating email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "user-name@example.org",
            "user_name@example.net"
        ]
        invalid_emails = [
            "user@.com",
            "user@com",
            "@example.com",
            "user@example.",
            "user@-example.com",
            "user@example-.com"
        ]
        
        for email_addr in valid_emails:
            self.assertTrue(validate_email(email_addr))
            
        for email_addr in invalid_emails:
            self.assertFalse(validate_email(email_addr))

    def test_get_sender(self):
        """Test getting sender from an email message."""
        msg = Message()
        msg['From'] = 'John Doe <john.doe@example.com>'
        self.assertEqual(get_sender(msg), 'john.doe@example.com')

    def test_get_recipients(self):
        """Test getting recipients from an email message."""
        msg = Message()
        msg['To'] = 'John <john@example.com>, Jane <jane@example.com>'
        msg['Cc'] = 'Bob <bob@example.com>'
        msg['Bcc'] = 'Alice <alice@example.com>'
        
        recipients = get_recipients(msg)
        self.assertIn('john@example.com', recipients)
        self.assertIn('jane@example.com', recipients)
        self.assertIn('bob@example.com', recipients)
        self.assertIn('alice@example.com', recipients)
        self.assertEqual(len(recipients), 4)


class TestSubjectKeywordExtraction(unittest.TestCase):
    """Tests for subject keyword extraction."""

    def test_basic_keyword_extraction(self):
        """Test extracting keywords from a simple subject."""
        subject = "Project Meeting Notes"
        self.assertEqual(
            extract_subject_keywords(subject),
            ["project", "meeting", "notes"]
        )

    def test_keyword_extraction_with_stopwords(self):
        """Test keyword extraction with stopwords removed."""
        subject = "Re: The Project Meeting Notes from Yesterday"
        # Assuming stopwords like "re", "the", "from" are removed
        self.assertEqual(
            extract_subject_keywords(subject),
            ["project", "meeting", "notes", "yesterday"]
        )

    def test_keyword_extraction_with_special_chars(self):
        """Test keyword extraction with special characters."""
        subject = "Project-Meeting: Notes & Updates (2023)"
        self.assertEqual(
            extract_subject_keywords(subject),
            ["project", "meeting", "notes", "updates", "2023"]
        )

    def test_empty_subject_keyword_extraction(self):
        """Test keyword extraction from an empty subject."""
        self.assertEqual(extract_subject_keywords(""), [])

    def test_short_word_removal(self):
        """Test that very short words are filtered out."""
        subject = "A big test of the email system"
        # Assuming words with less than 3 characters are removed
        self.assertEqual(
            extract_subject_keywords(subject),
            ["big", "test", "email", "system"]
        )


class TestDomainHandling(unittest.TestCase):
    """Tests for domain handling functionality."""

    def test_simple_domain_extraction(self):
        """Test extracting domain from a simple email address."""
        self.assertEqual(get_domain_from_email("user@example.com"), "example.com")

    def test_subdomain_extraction(self):
        """Test extracting domain with subdomains."""
        self.assertEqual(get_domain_from_email("user@mail.example.co.uk"), "mail.example.co.uk")

    def test_no_domain_handling(self):
        """Test handling emails without a domain."""
        with self.assertRaises(ValueError):
            get_domain_from_email("invalid_email")

    def test_empty_email_domain_handling(self):
        """Test handling empty email strings."""
        with self.assertRaises(ValueError):
            get_domain_from_email("")


class TestDateParsing(unittest.TestCase):
    """Tests for date parsing functionality."""

    def test_rfc2822_date_parsing(self):
        """Test parsing RFC 2822 formatted dates."""
        date_string = "Mon, 15 Aug 2023 09:30:45 -0400"
        expected_date = datetime(2023, 8, 15, 13, 30, 45)  # Converted to UTC
        self.assertEqual(parse_date(date_string), expected_date)

    def test_iso_date_parsing(self):
        """Test parsing ISO formatted dates."""
        date_string = "2023-08-15T09:30:45+00:00"
        expected_date = datetime(2023, 8, 15, 9, 30, 45)
        self.assertEqual(parse_date(date_string), expected_date)

    def test_ambiguous_date_parsing(self):
        """Test parsing ambiguous date formats."""
        # This could be MM/DD/YYYY or DD/MM/YYYY
        date_string = "08/15/2023 09:30:45"
        expected_date = datetime(2023, 8, 15, 9, 30, 45)
        self.assertEqual(parse_date(date_string), expected_date)

    def test_invalid_date_handling(self):
        """Test handling invalid date strings."""
        invalid_dates = [
            "Not a date",
            "2023-13-40",  # Invalid month and day
            ""  # Empty string
        ]
        for date_string in invalid_dates:
            with self.assertRaises(ValueError):
                parse_date(date_string)

    def test_date_parsing_with_named_month(self):
        """Test parsing dates with named months."""
        date_string = "15 August 2023 09:30:45"
        expected_date = datetime(2023, 8, 15, 9, 30, 45)
        self.assertEqual(parse_date(date_string), expected_date)


class TestCharacterSetHandling(unittest.TestCase):
    """Tests for character set handling functionality."""

    def test_utf8_character_set(self):
        """Test handling UTF-8 character set."""
        text = "Café au lait"
        charset = "utf-8"
        self.assertEqual(handle_character_set(text, charset), "Café au lait")

    def test_latin1_character_set(self):
        """Test handling ISO-8859-1 (Latin1) character set."""
        # This is the Latin1 encoding of "Café"
        text = b"Caf\xe9".decode("latin1")
        charset = "iso-8859-1"
        self.assertEqual(handle_character_set(text, charset), "Café")

    def test_unknown_character_set(self):
        """Test handling unknown character sets."""
        text = "Some text"
        charset = "unknown-charset"
        # Should default to UTF-8 or a fallback mechanism
        self.assertEqual(handle_character_set(text, charset), "Some text")

    def test_character_set_conversion(self):
        """Test converting between character sets."""
        # Create text in one encoding and convert to another
        original_text = "Café"
        charset_from = "utf-8"
        charset_to = "iso-8859-1"
        
        # Simulate conversion
        converted = handle_character_set(original_text, charset_from, target_charset=charset_to)
        
        # Convert back to verify
        result = handle_character_set(converted, charset_to, target_charset="utf-8")
        self.assertEqual(result, original_text)


@pytest.fixture
def sample_email_message():
    """Fixture providing a sample email message for testing."""
    msg = MIMEText("This is a test email body")
    msg['Subject'] = "=?utf-8?q?Test_Email_Subject_with_Caf=C3=A9?="
    msg['From'] = "John Doe <john.doe@example.com>"
    msg['To'] = "Jane Smith <jane.smith@example.org>, team@example.com"
    msg['Cc'] = "boss@example.com"
    msg['Date'] = "Mon, 15 Aug 2023 09:30:45 -0400"
    return msg


@pytest.mark.parametrize("header_value,expected", [
    ("Simple ASCII", "Simple ASCII"),
    ("=?utf-8?q?Caf=C3=A9?=", "Café"),
    ("=?iso-8859-1?q?Caf=E9?=", "Café"),
    ("=?utf-8?b?Q2Fmw6k=?=", "Café"),
    ("Mixed: =?utf-8?q?Caf=C3=A9?= au lait", "Mixed: Café au lait"),
])
def test_parametrized_header_decoding(header_value, expected):
    """Parametrized test for header decoding with different encodings."""
    assert decode_header(header_value) == expected


def test_integration_with_sample_email(sample_email_message):
    """Integration test using a sample email message."""
    # Test subject decoding
    assert decode_header(sample_email_message['Subject']) == "Test Email Subject with Café"
    
    # Test sender extraction
    assert get_sender(sample_email_message) == "john.doe@example.com"
    
    # Test recipient extraction
    recipients = get_recipients(sample_email_message)
    assert "jane.smith@example.org" in recipients
    assert "team@example.com" in recipients
    assert "boss@example.com" in recipients
    
    # Test date parsing
    parsed_date = parse_date(sample_email_message['Date'])
    assert parsed_date.year == 2023
    assert parsed_date.month == 8
    assert parsed_date.day == 15


if __name__ == "__main__":
    unittest.main()

