#!/usr/bin/env python3
"""
Tests for the statistics module.
IMPORTANT: Use pytest-mock for all mocking needs, NOT unittest.mock!
"""
import pytest
import sys
import os
from collections import Counter

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import from our local statistics module
from src.statistics import (
    calculate_mean, calculate_median, calculate_mode,
    format_size, email_count_stats, sender_stats,
    recipient_stats, body_size_stats, missing_header_stats,
    date_distribution_stats, size_comparison_stats, calculate_parsed_data_size,
    attachment_stats, calculate_statistics
)

# Basic Statistical Functions Tests
def test_calculate_mean():
    """Test mean calculation with various inputs."""
    assert calculate_mean([1, 2, 3, 4, 5]) == 3.0
    assert calculate_mean([]) == 0
    assert calculate_mean([1]) == 1.0
    assert calculate_mean([-1, 1]) == 0.0

def test_calculate_median():
    """Test median calculation."""
    # Test empty list
    assert calculate_median([]) == 0
    
    # Test odd number of values
    assert calculate_median([2]) == 2
    assert calculate_median([1, 2, 3]) == 2
    
    # Test even number of values
    assert calculate_median([1, 2]) == 1.5
    assert calculate_median([1, 2, 3, 4]) == 2.5

def test_calculate_mode():
    """Test mode calculation."""
    assert calculate_mode([1, 2, 2, 3]) == 2
    assert calculate_mode([]) is None
    assert calculate_mode(['a', 'b', 'a']) == 'a'

def test_format_size():
    """Test size formatting."""
    assert format_size(0) == "0.00 B"
    assert format_size(1023) == "1023.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1024 * 1024) == "1.00 MB"

# Email Statistics Tests
def test_email_count_stats():
    """Test email count statistics."""
    assert email_count_stats(100) == {"email_count": 100}
    assert email_count_stats(0) == {"email_count": 0}

def test_sender_stats():
    """Test sender statistics calculation."""
    # Empty case
    assert sender_stats(Counter()) == {}
    
    # Normal case
    senders = Counter({
        "user1@example.com": 10,
        "user2@example.com": 5
    })
    result = sender_stats(senders)
    assert result["unique_senders"] == 2
    assert result["most_frequent_sender"] == "user1@example.com"
    assert result["most_frequent_sender_count"] == 10

def test_recipient_stats():
    """Test recipient statistics calculation."""
    # Empty case
    assert recipient_stats(Counter()) == {}
    
    # Normal case
    recipients = Counter({
        "recipient1@example.com": 10,
        "recipient2@example.com": 5
    })
    result = recipient_stats(recipients)
    assert result["unique_recipients"] == 2
    assert result["most_frequent_recipient"] == "recipient1@example.com"
    assert result["most_frequent_recipient_count"] == 10

def test_body_size_stats():
    """Test body size statistics."""
    sizes = [1000, 2000, 3000]
    result = body_size_stats(sizes)
    assert result["count"] == 3
    assert result["total_size"] == 6000
    assert result["avg_size"] == 2000
    assert result["min_size"] == 1000
    assert result["max_size"] == 3000

def test_missing_header_stats():
    """Test missing header statistics."""
    headers = Counter({"subject": 5, "date": 3})
    result = missing_header_stats(headers)
    assert result["total_count"] == 8
    assert len(result["by_type"]) == 2

def test_date_distribution_stats():
    """Test date distribution statistics."""
    dates = {
        "2023-01": 10,
        "2023-02": 20
    }
    result = date_distribution_stats(dates)
    assert result["first_month"] == "2023-01"
    assert result["last_month"] == "2023-02"
    assert result["busiest_month"] == "2023-02"

def test_size_comparison_stats():
    """Test size comparison statistics."""
    result = size_comparison_stats(1000, 800)
    assert result["original_file_size"] == 1000
    assert result["parsed_data_size"] == 800
    assert result["difference"] == 200
    assert result["difference_percentage"] == 20.0

def test_calculate_parsed_data_size():
    """Test parsed data size calculation."""
    body_sizes = {
        "plain_text": [100, 200],
        "html": [300, 400]
    }
    attachment_sizes = {
        ".txt": [500, 600]
    }
    total = calculate_parsed_data_size(body_sizes, attachment_sizes)
    assert total == 2100  # Sum of all sizes

def test_attachment_stats():
    """Test attachment statistics calculation."""
    # Empty case
    assert attachment_stats(Counter(), {}) == {}
    
    # Normal case
    counts = Counter({".pdf": 2, ".txt": 1})
    sizes = {
        ".pdf": [1000, 2000],
        ".txt": [500]
    }
    result = attachment_stats(counts, sizes)
    
    assert result["total_count"] == 3
    assert result["unique_types"] == 2
    assert len(result["by_type"]) == 2
    
    # Check PDF stats (most common)
    pdf_stats = next(item for item in result["by_type"] if item["type"] == ".pdf")
    assert pdf_stats["count"] == 2
    assert pdf_stats["percentage"] == pytest.approx(66.67, rel=0.01)
    assert pdf_stats["total_size"] == 3000

def test_calculate_statistics():
    """Test full statistics calculation."""
    report_data = {
        "file_metadata": {
            "email_count": 100,
            "file_size": 10000
        },
        "headers": {
            "from": Counter({"user@example.com": 5}),
            "to": Counter({"recipient@example.com": 3}),
            "missing_headers": Counter({"subject": 2}),
            "date_distribution": {"2023-01": 10}
        },
        "content": {
            "body_sizes": {
                "plain_text": [100, 200],
                "html": [300]
            },
            "attachments": {
                "counts_by_type": Counter({".txt": 1}),
                "sizes_by_type": {".txt": [1000]}
            }
        }
    }
    
    result = calculate_statistics(report_data)
    
    # Check presence of all major sections
    assert "email_count" in result
    assert "top_senders" in result
    assert "top_recipients" in result
    assert "plain_text_body" in result
    assert "html_body" in result
    assert "attachments" in result
    assert "missing_headers" in result
    assert "date_distribution" in result
    assert "size_comparison" in result

    # Verify some key values
    assert result["email_count"] == 100
    assert result["unique_senders"] == 1
    assert result["unique_recipients"] == 1