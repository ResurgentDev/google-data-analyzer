#!/usr/bin/env python3
"""
Tests for the email visualization module.

These tests verify the functionality of the visualizer.py module, including:
- Bar chart creation
- Line plot creation
- Pie chart creation
- Chart formatting and styling
- Error handling
"""

import os
import datetime
import pytest
from unittest.mock import patch, MagicMock
from collections import Counter
import matplotlib.pyplot as plt

from src.visualizer import (
    create_top_senders_chart,
    create_top_recipients_chart,
    create_email_distribution_chart,
    create_attachment_types_chart,
    create_body_size_comparison_chart,
    create_email_domain_distribution_chart,
    create_weekday_distribution_chart,
    create_all_visualizations
)


@pytest.fixture
def sample_from_data():
    """Fixture for sample 'from' email address data."""
    return Counter({
        'user1@example.com': 15,
        'user2@example.com': 12,
        'user3@gmail.com': 10,
        'user4@gmail.com': 8,
        'user5@yahoo.com': 7,
        'user6@example.org': 5,
        'user7@example.com': 4,
        'user8@outlook.com': 3,
        'user9@hotmail.com': 2,
        'user10@example.net': 1
    })


@pytest.fixture
def sample_to_data():
    """Fixture for sample 'to' email address data."""
    return Counter({
        'recipient1@example.com': 20,
        'recipient2@gmail.com': 15,
        'recipient3@example.org': 12,
        'recipient4@example.com': 10,
        'recipient5@yahoo.com': 8,
        'recipient6@outlook.com': 6,
        'recipient7@hotmail.com': 4,
        'recipient8@example.net': 3,
        'recipient9@gmail.com': 2,
        'recipient10@example.com': 1
    })


@pytest.fixture
def sample_date_distribution():
    """Fixture for sample date distribution data."""
    return {
        '2023-01': 10,
        '2023-02': 15,
        '2023-03': 25,
        '2023-04': 20,
        '2023-05': 30,
        '2023-06': 18,
        '2023-07': 22,
        '2023-08': 28,
    }


@pytest.fixture
def sample_attachment_counts():
    """Fixture for sample attachment type counts."""
    return Counter({
        'pdf': 25,
        'docx': 18,
        'xlsx': 15,
        'jpg': 12,
        'png': 10,
        'txt': 8,
        'zip': 6,
        'pptx': 5,
        'html': 4,
        'csv': 3,
        'json': 2,
        'xml': 1
    })


@pytest.fixture
def sample_dates():
    """Fixture for sample email dates."""
    # Create dates across different days of the week
    start_date = datetime.datetime(2023, 1, 1)  # Sunday
    dates = []
    
    # Add varying counts for each day of the week
    for i in range(100):
        # Create a date offset from start date
        offset = i % 14  # Cycle through two weeks
        date = start_date + datetime.timedelta(days=offset)
        dates.append(date)
    
    # Add extra emails for certain days to create variation
    for _ in range(10):  # More emails on Monday
        dates.append(start_date + datetime.timedelta(days=1))
    
    for _ in range(5):  # More emails on Thursday
        dates.append(start_date + datetime.timedelta(days=4))
    
    return dates


@pytest.fixture
def sample_body_sizes():
    """Fixture for sample email body sizes."""
    plain_sizes = [500, 1200, 800, 1500, 750, 950, 1100, 600, 900, 1300]
    html_sizes = [2200, 3500, 2800, 4000, 3200, 2500, 3800, 3000, 4200, 3600]
    return plain_sizes, html_sizes


@pytest.fixture
def sample_report_data(sample_from_data, sample_to_data, sample_date_distribution, 
                       sample_attachment_counts, sample_body_sizes):
    """Fixture for a complete sample report data structure."""
    plain_sizes, html_sizes = sample_body_sizes
    return {
        "headers": {
            "from": dict(sample_from_data),
            "to": dict(sample_to_data),
            "date_distribution": sample_date_distribution
        },
        "content": {
            "attachments": {
                "counts_by_type": dict(sample_attachment_counts)
            },
            "body_sizes": {
                "plain_text": plain_sizes,
                "html": html_sizes
            }
        }
    }


class TestBarChartCreation:
    """Tests for bar chart creation functionality."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_top_senders_chart(self, mock_savefig, sample_from_data, tmp_path):
        """Test creating a bar chart of top senders."""
        # Set up test
        output_path = os.path.join(tmp_path, "top_senders.png")
        
        # Run the function
        result = create_top_senders_chart(sample_from_data, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties (this doesn't check the actual rendering)
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 12  # Width
        assert fig.get_size_inches()[1] == 6   # Height
        
        # Close the figure to avoid resource leaks
        plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_top_recipients_chart(self, mock_savefig, sample_to_data, tmp_path):
        """Test creating a bar chart of top recipients."""
        # Set up test
        output_path = os.path.join(tmp_path, "top_recipients.png")
        
        # Run the function
        result = create_top_recipients_chart(sample_to_data, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 12
        assert fig.get_size_inches()[1] == 6
        
        # Close the figure
        plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_weekday_distribution_chart(self, mock_savefig, sample_dates, tmp_path):
        """Test creating a bar chart of email distribution by weekday."""
        # Set up test
        output_path = os.path.join(tmp_path, "weekday_distribution.png")
        
        # Run the function
        result = create_weekday_distribution_chart(sample_dates, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 10
        assert fig.get_size_inches()[1] == 6
        
        # Close the figure
        plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_body_size_comparison_chart(self, mock_savefig, sample_body_sizes, tmp_path):
        """Test creating a bar chart comparing plain text and HTML body sizes."""
        # Set up test
        output_path = os.path.join(tmp_path, "body_size_comparison.png")
        plain_sizes, html_sizes = sample_body_sizes
        
        # Run the function
        result = create_body_size_comparison_chart(plain_sizes, html_sizes, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 10
        assert fig.get_size_inches()[1] == 6
        
        # Close the figure
        plt.close()


class TestLinePlotCreation:
    """Tests for line plot creation functionality."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_email_distribution_chart(self, mock_savefig, sample_date_distribution, tmp_path):
        """Test creating a line plot of email distribution over time."""
        # Set up test
        output_path = os.path.join(tmp_path, "email_distribution.png")
        
        # Run the function
        result = create_email_distribution_chart(sample_date_distribution, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 12
        assert fig.get_size_inches()[1] == 6
        
        # Close the figure
        plt.close()


class TestPieChartCreation:
    """Tests for pie chart creation functionality."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_attachment_types_chart(self, mock_savefig, sample_attachment_counts, tmp_path):
        """Test creating a pie chart of attachment types."""
        # Set up test
        output_path = os.path.join(tmp_path, "attachment_types.png")
        
        # Run the function
        result = create_attachment_types_chart(sample_attachment_counts, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 10
        assert fig.get_size_inches()[1] == 8
        
        # Close the figure
        plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_email_domain_distribution_chart(self, mock_savefig, sample_from_data, tmp_path):
        """Test creating a pie chart of email domain distribution."""
        # Set up test
        output_path = os.path.join(tmp_path, "email_domains.png")
        
        # Run the function
        result = create_email_domain_distribution_chart(sample_from_data, output_path)
        
        # Verify results
        assert mock_savefig.called
        assert result == output_path
        
        # Check figure properties
        fig = plt.gcf()
        assert fig.get_size_inches()[0] == 10
        assert fig.get_size_inches()[1] == 8
        
        # Close the figure
        plt.close()


class TestChartFormatting:
    """Tests for chart formatting and styling functionality."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_chart_title_and_labels(self, mock_savefig, sample_from_data, tmp_path):
        """Test that charts have proper titles and labels."""
        output_path = os.path.join(tmp_path, "test_chart.png")
        
        with patch('matplotlib.pyplot.title') as mock_title, \
             patch('matplotlib.pyplot.xlabel') as mock_xlabel, \
             patch('matplotlib.pyplot.ylabel') as mock_ylabel:
            
            create_top_senders_chart(sample_from_data, output_path)
            
            # Check that title was set
            mock_title.assert_called_with('Top 10 Email Senders')
            
            plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_figure_size_setting(self, mock_savefig, sample_from_data, sample_date_distribution, tmp_path):
        """Test that figures are created with the expected size."""
        output_path = os.path.join(tmp_path, "test_chart.png")
        
        with patch('matplotlib.pyplot.figure') as mock_figure:
            create_top_senders_chart(sample_from_data, output_path)
            mock_figure.assert_called_with(figsize=(12, 6))
            plt.close()
            
            mock_figure.reset_mock()
            
            create_email_distribution_chart(sample_date_distribution, output_path)
            mock_figure.assert_called_with(figsize=(12, 6))
            plt.close()
    
    @patch('matplotlib.pyplot.savefig')
    def test_legend_handling(self, mock_savefig, sample_body_sizes, tmp_path):
        """Test that charts include legends when appropriate."""
        output_path = os.path.join(tmp_path, "test_chart.png")
        plain_sizes, html_sizes = sample_body_sizes
        
        with patch('matplotlib.axes.Axes.legend') as mock_legend:
            create_body_size_comparison_chart(plain_sizes, html_sizes, output_path)
            
            # Check that legend was added
            assert mock_legend.called
            plt.close()


class TestErrorHandling:
    """Tests for error handling in visualization functions."""
    
    def test_empty_data(self, tmp_path):
        """Test visualization functions properly handle empty data."""
        output_path = os.path.join(tmp_path, "test_chart.png")
        
        # Test with empty Counter
        result = create_top_senders_chart(Counter(), output_path)
        assert result is None
        
        # Test with empty date distribution
        result = create_email_distribution_chart({}, output_path)
        assert result is None
        
        # Test with empty attachment counts
        result = create_attachment_types_chart(Counter(), output_path)
        assert result is None
        
        # Test with empty body sizes
        result = create_body_size_comparison_chart([], [], output_path)
        assert result is None
    
    def test_filesystem_errors(self, tmp_path):
        """Test visualization functions properly handle filesystem errors."""
        # Use a directory path as output file to cause an error
        invalid_path = str(tmp_path)  # This is a directory, not a file
        
        # pytest's tmp_path is created automatically, so we need to patch savefig
        # to simulate a filesystem error
        
        with patch('matplotlib.pyplot.savefig', side_effect=PermissionError("Permission denied")):
            result = create_top_senders_chart(Counter({'user@example.com': 10}), invalid_path)
            assert result is None
            
            result = create_top_recipients_chart(Counter({'user@example.com': 10}), invalid_path)
            assert result is None
            
            result = create_email_distribution_chart({'2023-01': 10}, invalid_path)
            assert result is None
            
            result = create_attachment_types_chart(Counter({'pdf': 5}), invalid_path)
            assert result is None
    
    def test_invalid_data_types(self, tmp_path):
        """Test visualization functions properly handle invalid data types."""
        output_path = os.path.join(tmp_path, "test_chart.png")
        
        # Test with invalid type for from_data
        with pytest.raises(Exception):
            create_top_senders_chart("invalid_data", output_path)
        
        # Test with invalid type for to_data
        with pytest.raises(Exception):
            create_top_recipients_chart("invalid_data", output_path)
        
        # Test with invalid type for date_distribution
        with pytest.raises(Exception):
            create_email_distribution_chart("invalid_data", output_path)
        
        # Test with invalid type for attachment_counts
        with pytest.raises(Exception):
            create_attachment_types_chart("invalid_data", output_path)
        
        # Test with invalid type for body sizes
        with pytest.raises(Exception):
            create_body_size_comparison_chart("invalid_plain", "invalid_html", output_path)
        
        # Test with invalid type for date_data
        with pytest.raises(Exception):
            create_weekday_distribution_chart("invalid_data", output_path)
            
        # Test with invalid type for from_data in domain distribution
        with pytest.raises(Exception):
            create_email_domain_distribution_chart("invalid_data", output_path)


class TestCreateAllVisualizations:
    """Tests for the create_all_visualizations function."""
    
    @patch('src.visualizer.create_top_senders_chart')
    @patch('src.visualizer.create_top_recipients_chart')
    @patch('src.visualizer.create_email_distribution_chart')
    @patch('src.visualizer.create_attachment_types_chart')
    @patch('src.visualizer.create_body_size_comparison_chart')
    @patch('src.visualizer.create_email_domain_distribution_chart')
    def test_create_all_visualizations(self, mock_domain, mock_body, mock_attachment, 
                                       mock_distribution, mock_recipients, mock_senders,
                                       sample_report_data, tmp_path):
        """Test that create_all_visualizations calls all individual visualization functions."""
        # Configure mocks to return successful paths
        mock_senders.return_value = os.path.join(tmp_path, 'top_senders.png')
        mock_recipients.return_value = os.path.join(tmp_path, 'top_recipients.png')
        mock_distribution.return_value = os.path.join(tmp_path, 'email_by_month.png')
        mock_attachment.return_value = os.path.join(tmp_path, 'attachment_types.png')
        mock_body.return_value = os.path.join(tmp_path, 'body_size_comparison.png')
        mock_domain.return_value = os.path.join(tmp_path, 'email_domains.png')
        
        # Run the function
        result = create_all_visualizations(sample_report_data, str(tmp_path))
        
        # Verify all visualization functions were called
        assert mock_senders.called
        assert mock_recipients.called
        assert mock_distribution.called
        assert mock_attachment.called
        assert mock_body.called
        assert mock_domain.called
        
        # Verify the result contains all expected paths
        assert len(result) == 6
        assert os.path.join(tmp_path, 'top_senders.png') in result
        assert os.path.join(tmp_path, 'email_domains.png') in result
    
    @patch('os.makedirs')
    def test_create_all_visualizations_directory_creation(self, mock_makedirs, sample_report_data, tmp_path):
        """Test that create_all_visualizations creates output directory if it doesn't exist."""
        with patch('src.visualizer.create_top_senders_chart', return_value=None):
            # Run the function
            create_all_visualizations(sample_report_data, str(tmp_path))
            
            # Verify makedirs was called with exist_ok=True
            mock_makedirs.assert_called_once_with(str(tmp_path), exist_ok=True)
    
    def test_create_all_visualizations_empty_data(self, tmp_path):
        """Test create_all_visualizations with empty data."""
        # Run with empty report data
        result = create_all_visualizations({}, str(tmp_path))
        
        # Should return an empty list
        assert result == []
        
        # Run with minimal/incomplete report data
        result = create_all_visualizations({"headers": {}}, str(tmp_path))
        assert result == []

    def test_create_all_visualizations_error_handling(self, tmp_path):
        """Test create_all_visualizations error handling."""
        # Simulate an exception in the function
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            # Run the function
            result = create_all_visualizations({"headers": {"from": {"user@example.com": 10}}}, str(tmp_path))
            
            # Should return an empty list on error
            assert result == []
