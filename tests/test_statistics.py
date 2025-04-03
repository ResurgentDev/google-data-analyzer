#!/usr/bin/env python3
"""
Tests for the statistics module.

This module contains tests for all the statistical analysis functions in the statistics module,
including basic statistics calculations, email count statistics, header statistics,
content size statistics, attachment statistics, time-based statistics, and size comparisons.
"""

import pytest
from collections import Counter, defaultdict
from datetime import datetime
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module to be tested
from statistics import (
    calculate_mean, calculate_median, calculate_mode,
    format_size, email_count_stats, sender_stats, recipient_stats,
    body_size_stats, attachment_stats, missing_header_stats,
    date_distribution_stats, size_comparison_stats, calculate_parsed_data_size,
    calculate_statistics
)


# Basic statistical calculations tests
class TestBasicStatistics:
    """Tests for basic statistical calculation functions."""

    def test_calculate_mean(self):
        """Test the calculate_mean function."""
        # Test with regular data
        assert calculate_mean([1, 2, 3, 4, 5]) == 3.0

        # Test with negative numbers
        assert calculate_mean([10, -10, 5, -5]) == 0.0

        # Test with empty list
        assert calculate_mean([]) == 0

        # Test with decimal values
        assert calculate_mean([1.5, 2.5, 3.5]) == 2.5

    def test_calculate_median(self):
        """Test the calculate_median function."""
        # Test with odd number of elements
        assert calculate_median([1, 2, 3, 4, 5]) == 3.0

        # Test with even number of elements
        assert calculate_median([1, 2, 3, 4]) == 2.5

        # Test with unordered list
        assert calculate_median([5, 2, 1, 3, 4]) == 3.0

        # Test with empty list
        assert calculate_median([]) == 0

    def test_calculate_mode(self):
        """Test the calculate_mode function."""
        # Test with numeric data
        assert calculate_mode([1, 2, 2, 3, 4, 2, 5]) == 2

        # Test with string data
        assert calculate_mode(["apple", "banana", "apple", "cherry"]) == "apple"

        # Test with empty list
        assert calculate_mode([]) is None

        # Test with all unique values (should return first value)
        # This behavior depends on the Counter implementation
        result = calculate_mode([1, 2, 3, 4, 5])
        assert result in [1, 2, 3, 4, 5]  # One of these will be returned as mode

    def test_format_size(self):
        """Test the format_size function."""
        # Test bytes
        assert format_size(500) == "500.00 B"

        # Test kilobytes
        assert format_size(1500) == "1.46 KB"

        # Test megabytes
        assert format_size(1500000) == "1.43 MB"

        # Test gigabytes
        assert format_size(1500000000) == "1.40 GB"

        # Test terabytes
        assert format_size(1500000000000) == "1.36 TB"

        # Test 0 bytes
        assert format_size(0) == "0.00 B"


# Email count statistics tests
class TestEmailCountStatistics:
    """Tests for email count statistics functions."""

    def test_email_count_stats(self):
        """Test the email_count_stats function."""
        # Test with regular count
        assert email_count_stats(100) == {"email_count": 100}

        # Test with zero
        assert email_count_stats(0) == {"email_count": 0}


# Fixtures for header statistics tests
@pytest.fixture
def from_addresses_fixture():
    """Fixture for from addresses counter."""
    counter = Counter()
    counter["user1@example.com"] = 10
    counter["user2@example.com"] = 5
    counter["user3@example.com"] = 3
    counter["user4@example.com"] = 1
    return counter


@pytest.fixture
def to_addresses_fixture():
    """Fixture for to addresses counter."""
    counter = Counter()
    counter["recipient1@example.com"] = 8
    counter["recipient2@example.com"] = 7
    counter["recipient3@example.com"] = 3
    return counter


# Header statistics tests
class TestHeaderStatistics:
    """Tests for header statistics functions."""

    def test_sender_stats(self, from_addresses_fixture):
        """Test the sender_stats function."""
        result = sender_stats(from_addresses_fixture)

        # Test the structure of the result
        assert "top_senders" in result
        assert "unique_senders" in result
        assert "most_frequent_sender" in result
        assert "most_frequent_sender_count" in result

        # Test the values
        assert result["unique_senders"] == 4
        assert result["most_frequent_sender"] == "user1@example.com"
        assert result["most_frequent_sender_count"] == 10
        assert len(result["top_senders"]) == 4  # All senders included as there are only 4

        # Test with empty counter
        empty_result = sender_stats(Counter())
        assert empty_result == {}

    def test_recipient_stats(self, to_addresses_fixture):
        """Test the recipient_stats function."""
        result = recipient_stats(to_addresses_fixture)

        # Test the structure of the result
        assert "top_recipients" in result
        assert "unique_recipients" in result
        assert "most_frequent_recipient" in result
        assert "most_frequent_recipient_count" in result

        # Test the values
        assert result["unique_recipients"] == 3
        assert result["most_frequent_recipient"] == "recipient1@example.com"
        assert result["most_frequent_recipient_count"] == 8
        assert len(result["top_recipients"]) == 3  # All recipients included as there are only 3

        # Test with empty counter
        empty_result = recipient_stats(Counter())
        assert empty_result == {}

    def test_missing_header_stats(self):
        """Test the missing_header_stats function."""
        # Create a Counter for missing headers
        missing_headers = Counter({"from": 5, "date": 3, "subject": 2})
        
        result = missing_header_stats(missing_headers)
        
        # Test the structure
        assert "total_count" in result
        assert "by_type" in result
        
        # Test the values
        assert result["total_count"] == 10
        assert len(result["by_type"]) == 3
        
        # Verify the first item (most common)
        assert result["by_type"][0]["header"] == "from"
        assert result["by_type"][0]["count"] == 5
        
        # Test with empty counter
        empty_result = missing_header_stats(Counter())
        assert empty_result == {}


# Fixtures for content statistics tests
@pytest.fixture
def body_sizes_fixture():
    """Fixture for body sizes list."""
    return [1000, 2000, 3000, 4000, 5000]


# Content size statistics tests
class TestContentSizeStatistics:
    """Tests for content size statistics functions."""

    def test_body_size_stats(self, body_sizes_fixture):
        """Test the body_size_stats function."""
        result = body_size_stats(body_sizes_fixture, "plain_text")
        
        # Test the structure
        assert "count" in result
        assert "total_size" in result
        assert "total_size_human" in result
        assert "avg_size" in result
        assert "avg_size_human" in result
        assert "min_size" in result
        assert "min_size_human" in result
        assert "max_size" in result
        assert "max_size_human" in result
        assert "median_size" in result
        assert "median_size_human" in result
        
        # Test the values
        assert result["count"] == 5
        assert result["total_size"] == 15000
        assert result["total_size_human"] == "14.65 KB"
        assert result["avg_size"] == 3000
        assert result["avg_size_human"] == "2.93 KB"
        assert result["min_size"] == 1000
        assert result["min_size_human"] == "0.98 KB"
        assert result["max_size"] == 5000
        assert result["max_size_human"] == "4.88 KB"
        assert result["median_size"] == 3000
        assert result["median_size_human"] == "2.93 KB"
        
        # Test with empty list
        empty_result = body_size_stats([])
        assert empty_result == {}


# Fixtures for attachment statistics tests
@pytest.fixture
def attachment_counts_fixture():
    """Fixture for attachment counts counter."""
    return Counter({
        "pdf": 10,
        "doc": 7,
        "jpg": 5,
        "png": 3,
    })


@pytest.fixture
def attachment_sizes_fixture():
    """Fixture for attachment sizes by type."""
    return {
        "pdf": [1000000, 1500000, 2000000, 1200000, 1800000, 1300000, 2200000, 1400000, 1600000, 1900000],
        "doc": [800000, 900000, 850000, 950000, 750000, 880000, 820000],
        "jpg": [500000, 600000, 550000, 650000, 450000],
        "png": [300000, 350000, 400000]
    }


# Attachment statistics tests
class TestAttachmentStatistics:
    """Tests for attachment statistics functions."""

    def test_attachment_stats(self, attachment_counts_fixture, attachment_sizes_fixture):
        """Test the attachment_stats function."""
        result = attachment_stats(attachment_counts_fixture, attachment_sizes_fixture)
        
        # Test the structure
        assert "total_count" in result
        assert "unique_types" in result
        assert "by_type" in result
        
        # Test the values
        assert result["total_count"] == 25
        assert result["unique_types"] == 4
        assert len(result["by_type"]) == 4
        
        # Test the first type (most common)
        assert result["by_type"][0]["type"] == "pdf"
        assert result["by_type"][0]["count"] == 10
        assert round(result["by_type"][0]["percentage"], 1) == 40.0
        
        # Test with empty counter
        empty_result = attachment_stats(Counter(), {})
        assert empty_result == {}


# Fixtures for time-based statistics tests
@pytest.fixture
def date_distribution_fixture():
    """Fixture for date distribution data."""
    return {
        "2022-01": 10,
        "2022-02": 15,
        "2022-03": 20,
        "2022-04": 8,
        "2022-05": 12,
        "2022-06": 18
    }


# Time-based statistics tests
class TestTimeBasedStatistics:
    """Tests for time-based statistics functions."""

    def test_date_distribution_stats(self, date_distribution_fixture):
        """Test the date_distribution_stats function."""
        result = date_distribution_stats(date_distribution_fixture)
        
        # Test the structure
        assert "first_month" in result
        assert "last_month" in result
        assert "total_months" in result
        assert "busiest_month" in result
        assert "busiest_month_count" in result
        assert "monthly_average" in result
        assert "monthly_median" in result
        
        # Test the values
        assert result["first_month"] == "2022-01"
        assert result["last_month"] == "2022-06"
        assert result["total_months"] == 6
        assert result["busiest_month"] == "2022-03"
        assert result["busiest_month_count"] == 20
        assert result["monthly_average"] == (10 + 15 + 20 + 8 + 12 + 18) / 6
        assert result["monthly_median"] == 13.5  # Median of [8, 10, 12, 15, 18, 20]
        
        # Test with empty dict
        empty_result = date_distribution_stats({})
        assert empty_result == {}


# Size comparison statistics tests
class TestSizeComparisonStatistics:
    """Tests for size comparison statistics functions."""

    def test_size_comparison_stats(self):
        """Test the size_comparison_stats function."""
        original_size = 10000000  # 10 MB
        parsed_data_size = 7500000  # 7.5 MB
        
        result = size_comparison_stats(original_size, parsed_data_size)
        
        # Test the structure
        assert "original_file_size" in result
        assert "original_file_size_human" in result
        assert "parsed_data_size" in result
        assert "parsed_data_size_human" in result
        assert "difference" in result
        assert "difference_human" in result
        assert "difference_percentage" in result
        
        # Test the values
        assert result["original_file_size"] == 10000000
        assert result["original_file_size_human"] == "9.54 MB"
        assert result["parsed_data_size"] == 7500000
        assert result["parsed_data_size_human"] == "7.15 MB"
        assert result["difference"] == 2500000
        assert result["difference_human"] == "2.38 MB"
        assert result["difference_percentage"] == 25.0

        # Test with zero original size
        zero_result = size_comparison_stats(0, 0)
        assert zero_result["difference_percentage"] == 0


# Fixtures for parsed data size tests
@pytest.fixture
def body_sizes_dict_fixture():
    """Fixture for body sizes dictionary."""
    return {
        "plain_text": [1000, 2000, 3000],
        "html": [5000, 6000, 7000]
    }


@pytest.fixture
def attachment_sizes_dict_fixture():
    """Fixture for attachment sizes dictionary."""
    return {
        "pdf": [10000, 20000],
        "doc": [15000, 25000],
        "jpg": [5000, 8000]
    }


# Parsed data size tests
class TestParsedDataSize:
    """Tests for parsed data size calculation functions."""

    def test_calculate_parsed_data_size(self, body_sizes_dict_fixture, attachment_sizes_dict_fixture):
        """Test the calculate_parsed_data_size function."""
        result = calculate_parsed_data_size(body_sizes_dict_fixture, attachment_sizes_dict_fixture)
        
        # Calculate expected total
        expected = sum(body_sizes_dict_fixture["plain_text"]) + sum(body_sizes_dict_fixture["html"])
        expected += sum([sum(sizes) for sizes in attachment_sizes_dict_fixture.values()])
        
        # Verify the result
        assert result == expected
        
        # Test with empty dictionaries
        assert calculate_parsed_data_size({}, {}) == 0
        
        # Test with missing keys
        assert calculate_parsed_data_size({"other_format": [1000]}, {}) == 0
        
        # Test with some empty lists
        assert calculate_parsed_data_size(
            {"plain_text": [], "html": [1000]},
            {"pdf": [2000]}
        ) == 3000


# Fixtures for calculate_statistics tests
@pytest.fixture
def mock_report_data():
    """Fixture for a complete mock report data structure."""
    return {
        "file_metadata": {
            "email_count": 100,
            "file_size": 1000000
        },
        "headers": {
            "from": Counter({
                "user1@example.com": 20,
                "user2@example.com": 15,
                "user3@example.com": 10
            }),
            "to": Counter({
                "recipient1@example.com": 25,
                "recipient2@example.com": 20,
                "recipient3@example.com": 15
            }),
            "missing_headers": Counter({
                "subject": 5,
                "date": 3
            }),
            "date_distribution": {
                "2022-01": 30,
                "2022-02": 40,
                "2022-03": 30
            }
        },
        "content": {
            "body_sizes": {
                "plain_text": [1000, 2000, 3000],
                "html": [5000, 6000, 7000]
            },
            "attachments": {
                "counts_by_type": Counter({
                    "pdf": 10,
                    "doc": 5,
                    "jpg": 3
                }),
                "sizes_by_type": {
                    "pdf": [10000, 20000, 15000, 18000, 12000, 16000, 14000, 19000, 11000, 17000],
                    "doc": [8000, 9000, 11000, 7000, 10000],
                    "jpg": [5000, 6000, 4000]
                }
            }
        }
    }


# Calculate statistics tests
class TestCalculateStatistics:
    """Tests for calculate_statistics function."""

    def test_calculate_statistics(self, mock_report_data):
        """Test the calculate_statistics function with a complete dataset."""
        result = calculate_statistics(mock_report_data)
        
        # Test that all expected sections are present
        assert "email_count" in result
        assert "top_senders" in result
        assert "unique_senders" in result
        assert "top_recipients" in result
        assert "unique_recipients" in result
        assert "plain_text_body" in result
        assert "html_body" in result
        assert "attachments" in result
        assert "missing_headers" in result
        assert "date_distribution" in result
        assert "size_comparison" in result
        
        # Test some specific values
        assert result["email_count"] == 100
        assert result["unique_senders"] == 3
        assert result["most_frequent_sender"] == "user1@example.com"
        assert result["most_frequent_sender_count"] == 20
        assert result["unique_recipients"] == 3
        assert result["most_frequent_recipient"] == "recipient1@example.com"
        assert result["most_frequent_recipient_count"] == 25
        
        # Check plain text body statistics
        assert result["plain_text_body"]["count"] == 3
        assert result["plain_text_body"]["total_size"] == 6000
        assert result["plain_text_body"]["avg_size"] == 2000
        
        # Check HTML body statistics
        assert result["html_body"]["count"] == 3
        assert result["html_body"]["total_size"] == 18000
        assert result["html_body"]["avg_size"] == 6000
        
        # Check attachment statistics
        assert result["attachments"]["total_count"] == 18  # 10 + 5 + 3
        assert result["attachments"]["unique_types"] == 3
        assert len(result["attachments"]["by_type"]) == 3
        
        # Check date distribution statistics
        assert result["date_distribution"]["first_month"] == "2022-01"
        assert result["date_distribution"]["last_month"] == "2022-03"
        assert result["date_distribution"]["busiest_month"] == "2022-02"
        assert result["date_distribution"]["busiest_month_count"] == 40
        
        # Check size comparison statistics
        assert result["size_comparison"]["original_file_size"] == 1000000
        parsed_data_size = 6000 + 18000  # plain text + html
        parsed_data_size += sum([sum(sizes) for sizes in mock_report_data["content"]["attachments"]["sizes_by_type"].values()])
        assert result["size_comparison"]["parsed_data_size"] == parsed_data_size
    
    def test_calculate_statistics_with_missing_data(self):
        """Test calculate_statistics with partial or missing data."""
        # Test with empty report
        empty_result = calculate_statistics({})
        assert empty_result == {}
        
        # Test with only email count
        partial_result1 = calculate_statistics({"file_metadata": {"email_count": 50}})
        assert "email_count" in partial_result1
        assert partial_result1["email_count"] == 50
        
        # Test with only header data
        partial_result2 = calculate_statistics({
            "headers": {
                "from": Counter({"user@example.com": 10})
            }
        })
        assert "top_senders" in partial_result2
        assert "unique_senders" in partial_result2
        
        # Test with only content data
        partial_result3 = calculate_statistics({
            "content": {
                "body_sizes": {
                    "plain_text": [1000, 2000]
                }
            }
        })
        assert "plain_text_body" in partial_result3
        assert partial_result3["plain_text_body"]["count"] == 2

    def test_calculate_statistics_edge_cases(self):
        """Test calculate_statistics with edge cases."""
        # Test with zero values
        zero_result = calculate_statistics({
            "file_metadata": {
                "email_count": 0,
                "file_size": 0
            },
            "headers": {
                "from": Counter(),
                "to": Counter()
            },
            "content": {
                "body_sizes": {
                    "plain_text": [],
                    "html": []
                },
                "attachments": {
                    "counts_by_type": Counter(),
                    "sizes_by_type": {}
                }
            }
        })
        
        # Should have email_count but other sections should be empty or missing
        assert "email_count" in zero_result
        assert zero_result["email_count"] == 0
        assert "top_senders" not in zero_result
        assert "top_recipients" not in zero_result
        assert "plain_text_body" not in zero_result
        assert "html_body" not in zero_result
        assert "attachments" not in zero_result
