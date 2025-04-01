#!/usr/bin/env python3
"""
mbox_report_to_md.py
A script to convert mbox_analyzer JSON reports to markdown format.

Usage:
    python mbox_report_to_md.py input.json [output.md]
"""

import json
import argparse
import sys
import os
from datetime import datetime
import re
from typing import Dict, List, Any, Tuple, Optional


def format_size(size_bytes: int) -> str:
    """Convert size in bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_count(count: int) -> str:
    """Format count with thousands separator."""
    return f"{count:,}"


def create_table(headers: List[str], rows: List[List[str]]) -> str:
    """Create a markdown table with given headers and rows."""
    # Create the header row
    table = "| " + " | ".join(headers) + " |\n"
    # Create the separator row
    table += "| " + " | ".join(["---" for _ in headers]) + " |\n"
    # Add data rows
    for row in rows:
        table += "| " + " | ".join([str(cell) for cell in row]) + " |\n"
    
    return table


def get_top_items(items, count: int = 5, sort_by_count: bool = True) -> List[Tuple[str, int]]:
    """
    Get the top N items from a dictionary or list by value.
    
    Handles multiple input formats:
    - Dictionary: {"address@email.com": 123}
    - Dictionary with string values: {"address@email.com": "123"}
    - List of dicts: [{"address": "email@example.com", "count": 123}]
    """
    # Handle empty inputs
    if not items:
        return []
    
    # Case 1: List of dictionaries with address/count keys
    if isinstance(items, list):
        # Try to extract address and count from each dict
        sorted_items = []
        for item in items:
            if isinstance(item, dict) and "address" in item and "count" in item:
                # Ensure count is an integer
                try:
                    count_value = int(item["count"])
                    sorted_items.append((item["address"], count_value))
                except (ValueError, TypeError):
                    # Skip items with invalid counts
                    continue
        
        # Sort by count
        sorted_items = sorted(sorted_items, key=lambda x: x[1], reverse=sort_by_count)
    
    # Case 2: Dictionary mapping addresses to counts
    elif isinstance(items, dict):
        sorted_items = []
        for key, value in items.items():
            # Ensure we're dealing with an integer value
            try:
                count_value = int(value) if isinstance(value, (str, int)) else 0
                sorted_items.append((key, count_value))
            except (ValueError, TypeError):
                # Skip items with invalid counts
                continue
        
        # Sort by count
        sorted_items = sorted(sorted_items, key=lambda x: x[1], reverse=sort_by_count)
    
    else:
        # Unhandled input type
        return []
    
    return sorted_items[:count]


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely perform division, returning default value if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def process_report(report_data: Dict[str, Any]) -> str:
    """Process JSON report data and convert to markdown."""
    markdown = "# MBOX Analysis Report\n\n"
    
    # Add timestamp
    now = datetime.now()
    markdown += f"*Generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Extract key data with safety checks
    # Extract key data with safety checks
    file_metadata = report_data.get("file_metadata", {}) or {}
    content = report_data.get("content", {}) or {}
    statistics = report_data.get("statistics", {}) or {}
    # Section 1: Overview
    markdown += "## Overview\n\n"
    markdown += f"- **File Name**: {os.path.basename(file_metadata.get('file_path', 'Unknown'))}\n"
    markdown += f"- **File Size**: {format_size(file_metadata.get('file_size', 0))}\n"
    
    # Date range from statistics
    first_month = statistics.get("first_month", "")
    last_month = statistics.get("last_month", "")
    if first_month and last_month:
        markdown += f"- **Date Range**: {first_month} to {last_month}\n"
    
    markdown += f"- **Total Emails**: {format_count(file_metadata.get('email_count', 0))}\n\n"
    
    # Section 2: Email Statistics
    markdown += "## Email Statistics\n\n"
    
    # Basic stats
    markdown += "### Basic Statistics\n\n"
    
    # Get unique senders and recipients from statistics
    unique_senders = statistics.get("unique_senders", 0)
    unique_recipients = statistics.get("unique_recipients", 0)
    
    markdown += f"- **Unique Senders**: {format_count(unique_senders)}\n"
    markdown += f"- **Unique Recipients**: {format_count(unique_recipients)}\n"
    
    # Get time span in months from statistics
    time_span = statistics.get("time_span_months", 0)
    if time_span:
        markdown += f"- **Time Span**: {time_span} months\n"
    
    # Most active months from statistics
    # Handle active months and date distribution
    markdown += "\n### Most Active Months\n\n"
    
    # Get the busiest month directly from statistics
    busiest_month = statistics.get("busiest_month", "")
    busiest_month_count = statistics.get("busiest_month_count", 0)
    
    # Safety check: ensure we have valid busiest month data
    if busiest_month and isinstance(busiest_month, str) and busiest_month_count and isinstance(busiest_month_count, (int, str)):
        # Convert count to int if it's a string
        if isinstance(busiest_month_count, str):
            try:
                busiest_month_count = int(busiest_month_count)
            except (ValueError, TypeError):
                busiest_month_count = 0
        
        markdown += f"**Busiest Month**: {busiest_month} with {format_count(busiest_month_count)} emails\n\n"
    
    # Get the monthly distribution
    date_distribution = statistics.get("date_distribution", {})
    if date_distribution and isinstance(date_distribution, dict):
        # Safety check: ensure the dictionary is not empty
        if len(date_distribution) > 0:
            # Convert any string counts to integers for proper sorting
            normalized_distribution = {}
            for month, count in date_distribution.items():
                try:
                    if isinstance(count, str):
                        normalized_distribution[month] = int(count)
                    elif isinstance(count, int):
                        normalized_distribution[month] = count
                except (ValueError, TypeError):
                    # Skip invalid counts
                    continue
            
            # Get top months from the normalized distribution
            top_months = get_top_items(normalized_distribution, 3)
            
            month_rows = []
            for month, count in top_months:
                month_rows.append([month, format_count(count)])
            
            if month_rows:
                markdown += create_table(["Month", "Email Count"], month_rows)
                markdown += "\n"
    
    # Add total time span information if available
    total_months = statistics.get("total_months", 0)
    if total_months and isinstance(total_months, (int, str)):
        # Convert to int if it's a string
        if isinstance(total_months, str):
            try:
                total_months = int(total_months)
            except (ValueError, TypeError):
                total_months = 0
        
        if total_months > 0:
            markdown += f"**Total Time Span**: {format_count(total_months)} months\n\n"
    
    # Section 3: Top Senders/Recipients
    markdown += "## Top Senders and Recipients\n\n"
    
    # Top senders from statistics
    top_senders = statistics.get("top_senders", [])
    if top_senders:
        markdown += "### Top 10 Senders\n\n"
        
        sender_rows = []
        # When top_senders is already in the expected array format, use it directly
        if isinstance(top_senders, list) and all(isinstance(item, dict) and "address" in item and "count" in item 
                                                for item in top_senders[:10] if isinstance(item, dict)):
            # Take up to 10 items directly from the array
            sorted_senders = sorted(top_senders, key=lambda x: int(x.get("count", 0)) 
                                    if isinstance(x.get("count"), (int, str)) else 0, reverse=True)[:10]
            
            for item in sorted_senders:
                try:
                    count_value = int(item["count"]) if isinstance(item["count"], (int, str)) else 0
                    sender_rows.append([item["address"], format_count(count_value)])
                except (KeyError, ValueError, TypeError):
                    # Skip malformed items
                    continue
        else:
            # Fallback to the helper function for other formats
            for sender, count in get_top_items(top_senders, 10):
                sender_rows.append([sender, format_count(count)])
        
        markdown += create_table(["Email Address", "Count"], sender_rows)
        markdown += "\n"
    
    # Top recipients from statistics
    top_recipients = statistics.get("top_recipients", [])
    if top_recipients:
        markdown += "### Top 10 Recipients\n\n"
        
        recipient_rows = []
        # When top_recipients is already in the expected array format, use it directly
        if isinstance(top_recipients, list) and all(isinstance(item, dict) and "address" in item and "count" in item 
                                                   for item in top_recipients[:10] if isinstance(item, dict)):
            # Take up to 10 items directly from the array
            sorted_recipients = sorted(top_recipients, key=lambda x: int(x.get("count", 0)) 
                                      if isinstance(x.get("count"), (int, str)) else 0, reverse=True)[:10]
            
            for item in sorted_recipients:
                try:
                    count_value = int(item["count"]) if isinstance(item["count"], (int, str)) else 0
                    recipient_rows.append([item["address"], format_count(count_value)])
                except (KeyError, ValueError, TypeError):
                    # Skip malformed items
                    continue
        else:
            # Fallback to the helper function for other formats
            for recipient, count in get_top_items(top_recipients, 10):
                recipient_rows.append([recipient, format_count(count)])
        
        markdown += create_table(["Email Address", "Count"], recipient_rows)
        markdown += "\n"
    
    # Section 4: Content Analysis
    markdown += "## Content Analysis\n\n"
    
    # Email bodies
    body_sizes = content.get("body_sizes", {})
    plain_text = body_sizes.get("plain_text", []) if isinstance(body_sizes, dict) else []
    html = body_sizes.get("html", []) if isinstance(body_sizes, dict) else []
    
    markdown += "### Email Body Statistics\n\n"
    
    body_rows = []
    if plain_text:
        count = len(plain_text)
        total_size = sum(plain_text)
        # Calculate average size safely
        avg_size = safe_division(total_size, count)
        
        body_rows.append(["Plain Text", 
                         format_count(count), 
                         format_size(avg_size), 
                         format_size(total_size)])
    
    if html:
        count = len(html)
        total_size = sum(html)
        # Calculate average size safely
        avg_size = safe_division(total_size, count)
            
        body_rows.append(["HTML", 
                         format_count(count), 
                         format_size(avg_size), 
                         format_size(total_size)])
    
    markdown += create_table(["Format", "Count", "Average Size", "Total Size"], body_rows)
    markdown += "\n"
    
    # Missing headers
    missing_headers = statistics.get("missing_headers", {})
    if missing_headers and isinstance(missing_headers, dict):
        markdown += "### Missing Headers\n\n"
        
        missing_rows = []
        for header, count in missing_headers.items():
            if isinstance(count, int) and count > 0:
                missing_rows.append([header, format_count(count)])
        
        if missing_rows:
            markdown += create_table(["Header", "Count"], missing_rows)
        else:
            markdown += "*No missing headers found.*\n"
        markdown += "\n"
    
    # Section 5: Attachment Analysis
    # Section 5: Attachment Analysis
    markdown += "## Attachment Analysis\n\n"
    
    # Safely extract attachment data with proper type checking
    attachments = content.get("attachments", {})
    if not isinstance(attachments, dict):
        attachments = {}
    
    # Extract and validate counts_by_type (dictionary of extension -> count)
    counts_by_type = attachments.get("counts_by_type", {})
    if not isinstance(counts_by_type, dict):
        counts_by_type = {}
    
    # Extract and validate sizes_by_type (dictionary of extension -> list of sizes)
    sizes_by_type = attachments.get("sizes_by_type", {})
    if not isinstance(sizes_by_type, dict):
        sizes_by_type = {}
    
    # Safely calculate total attachments with type checking
    total_attachments = 0
    for ext, count in counts_by_type.items():
        # Ensure count is an integer
        if isinstance(count, (int, float)):
            total_attachments += int(count)
        elif isinstance(count, str):
            try:
                total_attachments += int(count)
            except (ValueError, TypeError):
                pass
    
    if counts_by_type and total_attachments > 0:
        markdown += f"**Total Attachments**: {format_count(total_attachments)}\n\n"
        markdown += "### Top Attachment Types\n\n"
        
        # Get top attachment types using the helper function that handles type conversion
        top_types = get_top_items(counts_by_type, 10)
        
        type_rows = []
        for file_type, count in top_types:
            # Ensure count is a valid integer
            if not isinstance(count, int):
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    # Skip items with invalid counts
                    continue
            
            # Get total size for this type if available
            total_size = 0
            if file_type in sizes_by_type and isinstance(sizes_by_type[file_type], list):
                total_size = sum(sizes_by_type[file_type])
            
            type_rows.append([
                file_type,
                format_count(count),
                format_size(total_size)
            ])
        
        if type_rows:
            markdown += create_table(["File Type", "Count", "Total Size"], type_rows)
        else:
            markdown += "*No attachment type information available.*\n"
        
        markdown += "\n"
        
        # Add additional statistics about attachments if available
        largest_attachment = statistics.get("largest_attachment", {})
        if isinstance(largest_attachment, dict) and "size" in largest_attachment and "type" in largest_attachment:
            # Safely extract size and type with type checking
            size = largest_attachment.get("size", 0)
            attachment_type = largest_attachment.get("type", "Unknown")
            
            # Ensure size is a number
            if isinstance(size, str):
                try:
                    size = int(size)
                except (ValueError, TypeError):
                    size = 0
            
            if size > 0:
                markdown += f"**Largest Attachment**: {format_size(size)} ({attachment_type})\n\n"
    # Section 6: File Size Information
    markdown += "## File Size Information\n\n"
    
    size_comparison = statistics.get("size_comparison", {})
    
    # Use human-readable values directly from size_comparison
    original_size_human = size_comparison.get("original_file_size_human", "0 bytes")
    parsed_size_human = size_comparison.get("parsed_data_size_human", "0 bytes")
    size_diff_human = size_comparison.get("difference_human", "0 bytes")
    
    # Get percentage values directly from size_comparison
    diff_percentage = size_comparison.get("difference_percentage", 0)
    parsed_percentage = 100 - diff_percentage if diff_percentage is not None else 0
    
    # Format the size information rows using direct values from size_comparison
    size_rows = [
        ["Original .mbox File", original_size_human, "100%"],
        ["Parsed Data", parsed_size_human, f"{parsed_percentage:.1f}%"],
        ["Size Difference", size_diff_human, f"{diff_percentage:.1f}%"]
    ]
    
    # Add additional size statistics if available
    compression_ratio = size_comparison.get("compression_ratio")
    if compression_ratio:
        size_rows.append(["Compression Ratio", "N/A", f"{compression_ratio:.1f}x"])
    
    markdown += create_table(["Component", "Size", "Percentage"], size_rows)
    markdown += "\n"
    
    # Add explanatory text about size differences
    markdown += "### Understanding File Size Differences\n\n"
    markdown += "These values represent the comparison between the original .mbox file size and the size of the parsed data extracted during analysis:\n\n"
    markdown += "* **Original .mbox File**: The total size of the raw .mbox file on disk\n"
    markdown += "* **Parsed Data**: The size of the actual email content after parsing (bodies, attachments, etc.)\n"
    markdown += "* **Size Difference**: How much smaller the parsed data is compared to the original file\n\n"
    
    markdown += "#### Common Reasons for Size Differences:\n\n"
    markdown += "* **Email Encoding and Compression**: MIME encoding adds overhead to the raw file size\n"
    markdown += "* **Removal of Duplicate Content**: Duplicate message parts and redundant data are not included in parsed size\n"
    markdown += "* **Parsing Efficiency**: The parser extracts only relevant content, skipping transport encoding overhead\n"
    markdown += "* **Header Normalization**: Email headers are processed and normalized during parsing\n"
    markdown += "* **MIME Structure Overhead**: MIME boundaries and multipart structure markers add size to the original file\n"
    markdown += "* **Metadata Storage**: Internal metadata used by mail clients that isn't part of the actual message content\n\n"
    
    # Add parsing statistics if available
    parsing_stats = statistics.get("parsing_stats", {})
    if parsing_stats:
        markdown += "\n### Parsing Statistics\n\n"
        
        parsing_rows = []
        total_emails = file_metadata.get("email_count", 0)
        
        failed_emails = parsing_stats.get("failed_emails", 0)
        if total_emails > 0 and failed_emails > 0:
            failure_rate = (failed_emails / total_emails) * 100
            parsing_rows.append(["Failed Emails", format_count(failed_emails), f"{failure_rate:.1f}%"])
        
        parsing_errors = parsing_stats.get("parsing_errors", {})
        for error_type, count in parsing_errors.items():
            if count > 0:
                error_rate = (count / total_emails) * 100 if total_emails > 0 else 0
                parsing_rows.append([f"{error_type.replace('_', ' ').title()}", 
                                    format_count(count), 
                                    f"{error_rate:.1f}%"])
        
        if parsing_rows:
            markdown += create_table(["Issue", "Count", "Percentage"], parsing_rows)
            markdown += "\n"
    
    markdown += "### Potential Data Loss Areas\n\n"
    markdown += "While size differences are normal, some actual data may not be represented in the parsed content:\n\n"
    markdown += "- Attachments that couldn't be properly processed or extracted\n"
    markdown += "- Corrupted message parts that were skipped during parsing\n"
    markdown += "- Non-standard email formats that the parser couldn't fully interpret\n"
    markdown += "- Custom headers or metadata not included in standard processing\n\n"
    
    # Footer
    markdown += "---\n"
    markdown += "*This report was generated using the mbox_report_to_md.py script.*\n"
    
    return markdown


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Convert mbox analyzer JSON report to Markdown.')
    parser.add_argument('input_file', help='Path to the JSON report file')
    parser.add_argument('output_file', nargs='?', help='Path to save the markdown output (default: report.md)')
    
    args = parser.parse_args()
    
    # Default output file
    output_file = args.output_file or 'report.md'
    
    # Check if input file exists
    if not os.path.isfile(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read JSON report
        with open(args.input_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Validate required keys exist
        if not isinstance(report_data, dict):
            raise ValueError("Invalid report format: expected a JSON object")
            
        # Process report and generate markdown
        markdown = process_report(report_data)
        
        # Write markdown to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Markdown report successfully written to '{output_file}'")
        
    except json.JSONDecodeError:
        print(f"Error: The file '{args.input_file}' is not a valid JSON file.", file=sys.stderr)
        sys.exit(2)
    except ZeroDivisionError:
        print(f"Error: Division by zero encountered during report processing.", file=sys.stderr)
        sys.exit(3)
    except KeyError as e:
        print(f"Error: Missing required key in JSON data: {str(e)}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(5)


if __name__ == '__main__':
    main()

