#!/usr/bin/env python3
"""
Tests for the report utilities module.

These tests verify the functionality of the report_utils.py module, including:
- JSON serialization
- Report generation
- Report file handling
- Report summary generation
- Character set handling
- Edge cases and error conditions

IMPORTANT: Use pytest-mock for all mocking needs, NOT unittest.mock!

"""

import os
import json
import datetime
import pytest
from unittest.mock import patch, mock_open, MagicMock
from collections import Counter, defaultdict
from io import StringIO

from src.report_utils import (
    make_json_serializable,
    format_size,
    generate_report,
    save_report_to_file,
    load_report_from_file,
    create_report_summary,
    generate_csv_report,
    update_report_with_visualizations,
    merge_reports
)


@pytest.fixture
def sample_datetime():
    """Fixture for a sample datetime object."""
    return datetime.datetime(2023, 5, 15, 10, 30, 45)


@pytest.fixture
def sample_counter():
    """Fixture for a sample Counter object."""
    return Counter({'item1': 10, 'item2': 5, 'item3': 3})


@pytest.fixture
def sample_defaultdict():
    """Fixture for a sample defaultdict object."""
    d = defaultdict(list)
    d['key1'] = [1, 2, 3]
    d['key2'] = [4, 5, 6]
    return d


@pytest.fixture
def sample_report_data(sample_datetime, sample_counter, sample_defaultdict):
    """Fixture for sample report data with various data types."""
    return {
        "metadata": {
            "generated_at": sample_datetime,
            "version": "1.0"
        },
        "statistics": {
            "total_emails": 150,
            "average_size": 1024.5,
            "email_counts": sample_counter,
            "domain_counts": {
                "example.com": 45,
                "gmail.com": 35,
                "yahoo.com": 25
            },
            "detailed_counts": sample_defaultdict
        },
        "content_analysis": {
            "subjects": ["Hello", "Meeting", "Report"],
            "dates": [
                sample_datetime - datetime.timedelta(days=5),
                sample_datetime - datetime.timedelta(days=3),
                sample_datetime
            ],
            "sizes": [512, 1024, 2048]
        }
    }


class TestJSONSerialization:
    """Tests for JSON serialization functionality."""
    def test_make_json_serializable_datetime(self, sample_datetime):
        """Test make_json_serializable correctly serializes datetime objects."""
        result = make_json_serializable(sample_datetime)
        
        # Check that datetime was converted to ISO format string
        assert isinstance(result, str)
        assert result == sample_datetime.isoformat()
    
    def test_make_json_serializable_counter(self, sample_counter):
        """Test make_json_serializable correctly serializes Counter objects."""
        result = make_json_serializable(sample_counter)
        
        # Check that Counter was converted to dict
        assert isinstance(result, dict)
        assert result == dict(sample_counter)
    
    def test_make_json_serializable_defaultdict(self, sample_defaultdict):
        """Test make_json_serializable correctly serializes defaultdict objects."""
        result = make_json_serializable(sample_defaultdict)
        
        # Check that defaultdict was converted to dict
        assert isinstance(result, dict)
        assert result == dict(sample_defaultdict)
        assert result == dict(sample_defaultdict)
    
    def test_make_json_serializable_nested(self, sample_report_data):
        """Test make_json_serializable correctly converts complex nested data types."""
        result = make_json_serializable(sample_report_data)
        
        # Check that the result can be JSON serialized without errors
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Check that complex types were properly converted
        assert isinstance(result["metadata"]["generated_at"], str)
        assert isinstance(result["statistics"]["email_counts"], dict)
        assert isinstance(result["statistics"]["detailed_counts"], dict)
        assert isinstance(result["content_analysis"]["dates"][0], str)
    
    def test_format_size_bytes(self):
        """Test format_size correctly formats byte values."""
        result = format_size(512)
        assert result == "512.00 B"
    
    def test_format_size_kilobytes(self):
        """Test format_size correctly formats kilobyte values."""
        result = format_size(1536)  # 1.5 KB
        assert result == "1.50 KB"
    
    def test_format_size_megabytes(self):
        """Test format_size correctly formats megabyte values."""
        result = format_size(1048576 * 2.5)  # 2.5 MB
        assert result == "2.50 MB"
        
    def test_format_size_gigabytes(self):
        """Test format_size correctly formats gigabyte values."""
        result = format_size(1073741824 * 3.25)  # 3.25 GB
        assert result == "3.25 GB"


class TestReportGeneration:
    """Tests for report generation functionality."""
    
    def test_generate_report(self, sample_report_data):
        """Test generate_report creates a properly structured report with timestamp."""
        # Create report without specifying output path
        result = generate_report(sample_report_data)
        
        # Verify result is a dict
        assert isinstance(result, dict)
        
        # Verify timestamp was added
        assert "generated_at" in result
        
        # Verify all expected sections are present
        assert "metadata" in result
        assert "statistics" in result
        assert "content_analysis" in result
    
    @patch("src.report_utils.save_report_to_file")
    def test_generate_report_with_output_path(self, mock_save, sample_report_data):
        """Test generate_report with output path saves to file."""
        output_path = "test_output.json"
        
        # Call generate_report with an output path
        result = generate_report(sample_report_data, output_path=output_path)
        
        # Verify save_report_to_file was called with correct args
        mock_save.assert_called_once()
        
        # Verify returned data is same as what would be saved
        assert isinstance(result, dict)
        assert "generated_at" in result


class TestReportFileHandling:
    """Tests for report file handling functionality."""
    
    @patch("builtins.open", new_callable=mock_open)
    def test_save_report_to_file(self, mock_file, sample_report_data):
        """Test save_report_to_file correctly writes to a file."""
        filepath = "test_report.json"
        
        # Call the function
        result = save_report_to_file(sample_report_data, filepath)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(filepath, 'w', encoding='utf-8')
        
        # Verify data was written to the file (json.dump was called)
        mock_file().write.assert_called()
        
        # Verify function returned True on success
        assert result is True
    
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_save_report_to_file_error(self, mock_file, sample_report_data):
        """Test save_report_to_file handles file write errors."""
        filepath = "test_report.json"
        
        # Call the function, which should handle the IOError
        result = save_report_to_file(sample_report_data, filepath)
        
        # Verify function returned False on error
        assert result is False
    
    @patch("os.path.dirname")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_report_to_file_creates_directory(self, mock_file, mock_makedirs, mock_dirname, sample_report_data):
        """Test save_report_to_file creates directory if needed."""
        filepath = "reports/nested/dir/test_report.json"
        directory = "reports/nested/dir"
        
        # Configure mocks
        mock_dirname.return_value = directory
        
        # Call the function
        result = save_report_to_file(sample_report_data, filepath)
        
        # Verify directory was created
        mock_dirname.assert_called_once_with(os.path.abspath(filepath))
        mock_makedirs.assert_called_once_with(directory, exist_ok=True)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(filepath, 'w', encoding='utf-8')
        
        # Verify result is True
        assert result is True
        
    @patch("builtins.open", new_callable=mock_open, read_data='{"test": "data"}')
    def test_load_report_from_file(self, mock_file):
        """Test load_report_from_file correctly loads from a file."""
        filepath = "test_report.json"
        
        # Call the function
        result = load_report_from_file(filepath)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(filepath, 'r', encoding='utf-8')
        
        # Verify result contains expected data
        assert result == {"test": "data"}
    
    @patch("builtins.open", side_effect=IOError("File not found"))
    def test_load_report_from_file_error(self, mock_file):
        """Test load_report_from_file handles file read errors."""
        filepath = "nonexistent_file.json"
        
        # Call the function, which should handle the IOError
        result = load_report_from_file(filepath)
        
        # Verify function returned None on error
        assert result is None
    
    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    def test_load_report_from_file_invalid_json(self, mock_file):
        """Test load_report_from_file handles invalid JSON data."""
        filepath = "invalid_json.json"
        
        # Call the function, which should handle the JSON parsing error
        result = load_report_from_file(filepath)
        
        # Verify function returned None on error
        assert result is None


class TestReportSummary:
    """Tests for report summary generation."""
    
    @pytest.fixture
    def sample_report_with_metadata(self):
        """Fixture for sample report with file metadata."""
        return {
            "file_metadata": {
                "file_path": "/path/to/test_mbox.mbox",
                "file_size_human": "15.75 MB",
                "email_count": 120
            },
            "generated_at": "2023-05-15T10:30:45"
        }
    
    @pytest.fixture
    def sample_report_with_statistics(self):
        """Fixture for sample report with statistics."""
        return {
            "file_metadata": {
                "file_path": "/path/to/test_mbox.mbox",
                "file_size_human": "15.75 MB",
                "email_count": 120
            },
            "statistics": {
                "unique_senders": 45,
                "unique_recipients": 78,
                "top_senders": [
                    {"address": "user1@example.com", "count": 25},
                    {"address": "user2@example.com", "count": 18},
                    {"address": "user3@example.com", "count": 15},
                    {"address": "user4@example.com", "count": 12},
                    {"address": "user5@example.com", "count": 10},
                    {"address": "user6@example.com", "count": 8}
                ],
                "attachments": {
                    "total_count": 45,
                    "unique_types": 8,
                    "by_type": [
                        {"type": "application/pdf", "count": 15, "total_size_human": "25.5 MB", "avg_size_human": "1.7 MB"},
                        {"type": "image/jpeg", "count": 12, "total_size_human": "8.3 MB", "avg_size_human": "691.7 KB"},
                        {"type": "application/zip", "count": 8, "total_size_human": "54.2 MB", "avg_size_human": "6.8 MB"}
                    ]
                }
            },
            "visualizations": [
                "/path/to/viz/senders_bar_chart.png",
                "/path/to/viz/email_timeline.png",
                "/path/to/viz/attachment_types_pie.png"
            ],
            "generated_at": "2023-05-15T10:30:45"
        }
    
    def test_create_report_summary_minimal(self, sample_report_with_metadata):
        """Test create_report_summary with minimal report data."""
        summary = create_report_summary(sample_report_with_metadata)
        
        # Verify it's a non-empty string
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Verify it contains expected sections
        assert "=== Email Analysis Report Summary ===" in summary
        assert "File Information:" in summary
        assert "/path/to/test_mbox.mbox" in summary
        assert "15.75 MB" in summary
        assert "Emails: 120" in summary
        assert "Report generated at: 2023-05-15T10:30:45" in summary
    
    def test_create_report_summary_complete(self, sample_report_with_statistics):
        """Test create_report_summary with complete report data."""
        summary = create_report_summary(sample_report_with_statistics)
        
        # Verify it contains all expected sections
        assert "=== Email Analysis Report Summary ===" in summary
        assert "File Information:" in summary
        assert "Key Statistics:" in summary
        assert "Unique senders: 45" in summary
        assert "Unique recipients: 78" in summary
        
        # Verify top senders info
        assert "Top Senders:" in summary
        assert "user1@example.com: 25 emails" in summary
        assert "user2@example.com: 18 emails" in summary
        
        # Verify attachment info
        assert "Attachments:" in summary
        assert "Total: 45" in summary
        assert "Unique types: 8" in summary
        
        # Verify attachment types info
        assert "Top Attachment Types:" in summary
        assert "application/pdf: 15 files" in summary
        assert "image/jpeg: 12 files" in summary
        
        # Verify visualizations info
        assert "Visualizations:" in summary
        assert "senders_bar_chart.png" in summary
        assert "attachment_types_pie.png" in summary
    
    def test_create_report_summary_empty(self):
        """Test create_report_summary with empty report data."""
        summary = create_report_summary({})
        
        # Verify it still produces a summary with header
        assert isinstance(summary, str)
        assert "=== Email Analysis Report Summary ===" in summary
        
        # Verify it doesn't contain sections that require data
        assert "File Information:" not in summary
        assert "Key Statistics:" not in summary
    
    def test_create_report_summary_missing_sections(self):
        """Test create_report_summary with missing sections."""
        # Report with only generated_at timestamp
        report = {"generated_at": "2023-05-15T10:30:45"}
        summary = create_report_summary(report)
        
        # Verify it produces a summary with header and timestamp
        assert "=== Email Analysis Report Summary ===" in summary
        assert "Report generated at: 2023-05-15T10:30:45" in summary
        
        # Verify it doesn't contain sections that require data
        assert "File Information:" not in summary
        assert "Key Statistics:" not in summary


class TestCSVReport:
    """Tests for CSV report generation."""
    
    @pytest.fixture
    def sample_report_for_csv(self):
        """Fixture for sample report suitable for CSV conversion."""
        return {
            "file_metadata": {
                "file_path": "/path/to/test_mbox.mbox",
                "file_size_human": "15.75 MB",
                "email_count": 120
            },
            "statistics": {
                "top_senders": [
                    {"address": "user1@example.com", "count": 25},
                    {"address": "user2@example.com", "count": 18}
                ],
                "attachments": {
                    "by_type": [
                        {"type": "application/pdf", "count": 15, "total_size_human": "25.5 MB", "avg_size_human": "1.7 MB"},
                        {"type": "image/jpeg", "count": 12, "total_size_human": "8.3 MB", "avg_size_human": "691.7 KB"}
                    ]
                }
            },
            "generated_at": "2023-05-15T10:30:45"
        }
    
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_csv_report_success(self, mock_file, sample_report_for_csv):
        """Test generate_csv_report successfully creates a CSV file."""
        output_path = "test_report.csv"
        
        # Call the function
        result = generate_csv_report(sample_report_for_csv, output_path)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(output_path, 'w', newline='', encoding='utf-8')
        
        # Verify data was written to the file
        mock_file().write.assert_called()
        
        # Verify function returned True on success
        assert result is True
    
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_generate_csv_report_file_error(self, mock_file, sample_report_for_csv):
        """Test generate_csv_report handles file write errors."""
        output_path = "test_report.csv"
        
        # Call the function, which should handle the IOError
        result = generate_csv_report(sample_report_for_csv, output_path)
        
        # Verify function returned False on error
        assert result is False
    
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_csv_report_content(self, mock_file, sample_report_for_csv):
        """Test generate_csv_report writes expected content to CSV file."""
        output_path = "test_report.csv"
        
        # Capture csv.writer calls
        csv_writer_mock = MagicMock()
        
        with patch('csv.writer', return_value=csv_writer_mock):
            result = generate_csv_report(sample_report_for_csv, output_path)
        
        # Verify writer was called with expected rows
        assert csv_writer_mock.writerow.call_count >= 10  # At least 10 calls for headers and data
        
        # Verify it writes metadata
        csv_writer_mock.writerow.assert_any_call(['Email Analysis Report'])
        csv_writer_mock.writerow.assert_any_call(['Generated', '2023-05-15T10:30:45'])
        
        # Verify it writes file info
        csv_writer_mock.writerow.assert_any_call(['File Information'])
        csv_writer_mock.writerow.assert_any_call(['Path', '/path/to/test_mbox.mbox'])
        
        # Verify it writes top senders
        csv_writer_mock.writerow.assert_any_call(['Top Senders'])
        csv_writer_mock.writerow.assert_any_call(['Email Address', 'Count'])
        
        # Verify function returned True
        assert result is True
    
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_csv_report_missing_data(self, mock_file):
        """Test generate_csv_report handles missing data sections."""
        # Report with minimal data
        minimal_report = {
            "generated_at": "2023-05-15T10:30:45"
        }
        output_path = "test_report.csv"
        
        # Call function with minimal report
        result = generate_csv_report(minimal_report, output_path)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(output_path, 'w', newline='', encoding='utf-8')
        
        # Verify function returned True even with minimal data
        assert result is True


class TestReportMerging:
    """Tests for report merging functionality."""
    
    @pytest.fixture
    def sample_reports(self):
        """Fixture for multiple sample reports to merge."""
        report1 = {
            "file_metadata": {
                "file_path": "/path/to/report1.mbox",
                "file_size_human": "10.5 MB",
                "email_count": 100
            },
            "statistics": {
                "unique_senders": 30,
                "unique_recipients": 45,
                "total_size_bytes": 10500000
            },
            "generated_at": "2023-05-10T10:30:45"
        }
        
        report2 = {
            "file_metadata": {
                "file_path": "/path/to/report2.mbox",
                "file_size_human": "15.2 MB",
                "email_count": 150
            },
            "statistics": {
                "unique_senders": 40,
                "unique_recipients": 60,
                "total_size_bytes": 15200000
            },
            "generated_at": "2023-05-12T14:25:10"
        }
        
        return [report1, report2]
    
    def test_merge_reports_success(self, sample_reports):
        """Test merge_reports successfully combines multiple reports."""
        # Call the function
        merged = merge_reports(sample_reports)
        
        # Verify merged report has source information
        assert "merged_report" in merged
        assert merged["merged_report"]["source_count"] == 2
        assert len(merged["merged_report"]["source_files"]) == 2
        assert "/path/to/report1.mbox" in merged["merged_report"]["source_files"]
        assert "/path/to/report2.mbox" in merged["merged_report"]["source_files"]
        
        # Verify merged report has timestamps
        assert "generated_at" in merged
        assert "merged_at" in merged
        
        # Verify statistics were merged
        assert merged["statistics"]["total_size_bytes"] == 25700000  # sum of both reports
    
    def test_merge_reports_empty_list(self):
        """Test merge_reports handles empty list of reports."""
        result = merge_reports([])
        assert result == {}
    
    def test_merge_reports_single_report(self, sample_reports):
        """Test merge_reports with a single report."""
        # Call with just the first report
        result = merge_reports([sample_reports[0]])
        
        # Verify it's a copy of the original with merged_report metadata added
        assert "merged_report" in result
        assert result["merged_report"]["source_count"] == 1
        assert result["file_metadata"]["file_path"] == "/path/to/report1.mbox"
        assert len(result["merged_report"]["source_files"]) == 1
        assert result["merged_report"]["source_files"][0] == "/path/to/report1.mbox"
        
        # Verify timestamps were updated
        assert "generated_at" in result
        assert "merged_at" in result


class TestReportVisualization:
    """Tests for report visualization functionality."""
    
    @pytest.fixture
    def sample_report(self):
        """Fixture for a sample report without visualizations."""
        return {
            "file_metadata": {
                "file_path": "/path/to/test.mbox",
                "file_size_human": "12.5 MB",
                "email_count": 120
            },
            "statistics": {
                "unique_senders": 35,
                "unique_recipients": 50
            },
            "generated_at": "2023-05-15T10:30:45"
        }
    
    @pytest.fixture
    def sample_visualizations(self):
        """Fixture for sample visualization file paths."""
        return [
            "/path/to/charts/senders_bar.png",
            "/path/to/charts/timeline.png",
            "/path/to/charts/attachments_pie.png"
        ]
    
    def test_update_report_with_visualizations_new(self, sample_report, sample_visualizations):
        """Test update_report_with_visualizations adds visualization paths to a report without existing visualizations."""
        # Call the function
        updated = update_report_with_visualizations(sample_report, sample_visualizations)
        
        # Verify the original report is not modified
        assert "visualizations" not in sample_report
        
        # Verify the updated report has visualizations
        assert "visualizations" in updated
        assert updated["visualizations"] == sample_visualizations
        assert len(updated["visualizations"]) == 3
        
        # Verify other report data is preserved
        assert updated["file_metadata"] == sample_report["file_metadata"]
        assert updated["statistics"] == sample_report["statistics"]
        assert updated["generated_at"] == sample_report["generated_at"]
    
    def test_update_report_with_visualizations_replace(self, sample_report, sample_visualizations):
        """Test update_report_with_visualizations replaces existing visualization paths."""
        # Add existing visualizations to the report
        report_with_viz = sample_report.copy()
        report_with_viz["visualizations"] = ["/path/to/old_viz.png"]
        
        # Call the function
        updated = update_report_with_visualizations(report_with_viz, sample_visualizations)
        
        # Verify the updated report has the new visualizations
        assert updated["visualizations"] == sample_visualizations
        assert "/path/to/old_viz.png" not in updated["visualizations"]
    
    def test_update_report_with_visualizations_empty_list(self, sample_report):
        """Test update_report_with_visualizations with an empty visualization list."""
        # Call the function with empty list
        updated = update_report_with_visualizations(sample_report, [])
        
        # Verify the updated report has an empty visualizations list
        assert "visualizations" in updated
        assert updated["visualizations"] == []
    
    def test_update_report_with_absolute_paths(self, sample_report):
        """Test update_report_with_visualizations with absolute file paths."""
        # Absolute paths on different platforms
        absolute_paths = [
            "/absolute/path/to/chart1.png",  # Unix-like
            "C:\\Users\\User\\charts\\chart2.png",  # Windows
            "D:/visualization/chart3.png"  # Mixed format
        ]
        
        # Call the function
        updated = update_report_with_visualizations(sample_report, absolute_paths)
        
        # Verify all paths were included regardless of format
        assert updated["visualizations"] == absolute_paths
        assert len(updated["visualizations"]) == 3


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_make_json_serializable_circular_reference(self):
        """Test make_json_serializable with circular references."""
        # Create an object with a circular reference
        circular_dict = {}
        circular_dict["self"] = circular_dict
        
        # The function should raise RecursionError or similar
        with pytest.raises(Exception):
            make_json_serializable(circular_dict)
    
    def test_format_size_zero_bytes(self):
        """Test format_size with zero bytes."""
        result = format_size(0)
        assert result == "0.00 B"
    
    def test_format_size_negative_value(self):
        """Test format_size with negative value."""
        # Negative values might not be realistic but should be handled gracefully
        result = format_size(-100)
        assert "-" in result  # Should maintain the negative sign
        assert "B" in result  # Should still have the unit
    
    def test_generate_report_with_non_serializable_data(self):
        """Test generate_report with data that can't be directly serialized."""
        # Create a report with a complex object that isn't directly serializable
        class ComplexObject:
            def __str__(self):
                return "Complex Object"
        
        report_data = {
            "complex_object": ComplexObject()
        }
        
        # Should raise TypeError or similar
        with pytest.raises(Exception):
            generate_report(report_data)
    
    def test_load_report_from_file_empty_file(self):
        """Test load_report_from_file with an empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = load_report_from_file("empty_file.json")
            assert result is None
    
    def test_save_report_to_file_permission_error(self):
        """Test save_report_to_file with permission error during directory creation."""
        report_data = {"test": "data"}
        
        # Mock os.makedirs to raise PermissionError
        with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
            result = save_report_to_file(report_data, "/protected/path/report.json")
            assert result is False
    
    def test_merge_reports_with_incompatible_structure(self):
        """Test merge_reports with incompatible report structures."""
        report1 = {
            "file_metadata": {"file_path": "report1.mbox"},
            "statistics": {"count": 100}
        }
        
        report2 = {
            "different_structure": True,
            "some_data": [1, 2, 3]
        }
        
        # Should still work but may not merge all fields
        result = merge_reports([report1, report2])
        
        # Basic report structure should be maintained
        assert "file_metadata" in result
        assert "merged_report" in result
        assert result["merged_report"]["source_count"] == 2


def test_create_report_summary_with_unsafe_characters():
    """Test create_report_summary with potentially unsafe characters in data."""
    report_with_unsafe = {
        "file_metadata": {
            "file_path": "</script><script>alert('xss')</script>",
            "file_size_human": "10 MB",
            "email_count": 100
        },
        "generated_at": "2023-05-15T10:30:45"
    }
    
    summary = create_report_summary(report_with_unsafe)
    
    # Verify unsafe characters are included as-is (not sanitized in the summary)
    assert "</script><script>alert('xss')</script>" in summary


def test_load_report_from_file_corrupt_json():
    """Test load_report_from_file with corrupt JSON data."""
    with patch("builtins.open", mock_open(read_data="{\"valid\": true, invalid}")):
        result = load_report_from_file("corrupt.json")
        assert result is None


def test_update_report_with_visualizations_none_paths():
    """Test update_report_with_visualizations with None instead of a list."""
    report = {"test": "data"}
    
    # Should handle None gracefully or raise a specific error
    with pytest.raises(Exception):
        update_report_with_visualizations(report, None)


def test_generate_csv_report_with_special_characters():
    """Test generate_csv_report with special characters that might break CSV format."""
    report = {
        "file_metadata": {
            "file_path": "file,with,commas.mbox",
            "email_count": 100
        },
        "statistics": {
            "top_senders": [
                {"address": "user@example.com", "count": 10},
                {"address": "user,with,commas@example.com", "count": 5},
                {"address": "user\"with\"quotes@example.com", "count": 3}
            ]
        },
        "generated_at": "2023-05-15T10:30:45"
    }
    
    # Mock the open and csv.writer to capture written data
    csv_writer_mock = MagicMock()
    with patch("builtins.open", mock_open()), patch("csv.writer", return_value=csv_writer_mock):
        result = generate_csv_report(report, "special_chars.csv")
        
        # Verify it returned success
        assert result is True
        
        # Verify csv.writer was called
        assert csv_writer_mock.writerow.call_count > 0
