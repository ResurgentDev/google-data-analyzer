#!/usr/bin/env python3
"""
Report Utilities Module

This module provides utilities for handling report generation and JSON serialization.
It includes:
- Functions for generating JSON reports
- Functions for serializing Python objects to JSON-compatible formats
- Functions for handling special data types like datetime and Counter
- Report file handling and management utilities
"""

import os
import json
import datetime
import logging
from collections import Counter, defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """
    Converts Python objects to JSON-serializable format.
    
    Handles special types like:
    - Counter objects
    - defaultdict objects
    - datetime objects
    - nested dictionaries and lists
    
    Args:
        obj: The object to convert
            
    Returns:
        object: JSON-serializable version of the object
    """
    if isinstance(obj, dict):
        # Convert defaultdict to regular dict
        if isinstance(obj, defaultdict):
            obj = dict(obj)
                
        # Process each key-value pair
        return {k: make_json_serializable(v) for k, v in obj.items()}
            
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
            
    elif isinstance(obj, Counter):
        return dict(obj)
            
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
            
    else:
        return obj


def format_size(size_bytes):
    """
    Formats a byte size into a human-readable string.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def generate_report(report_data, output_path=None):
    """
    Generates a JSON report and optionally saves it to a file.
    
    Args:
        report_data (dict): The report data to serialize
        output_path (str, optional): Path to save the JSON report
        
    Returns:
        dict: The serialized report data
    """
    # Add timestamp to report
    report_data["generated_at"] = datetime.datetime.now().isoformat()
    
    # Convert to JSON-serializable format
    serializable_report = make_json_serializable(report_data)
    
    # Output to file if path provided
    if output_path:
        save_report_to_file(serializable_report, output_path)
                
    return serializable_report


def save_report_to_file(report_data, output_path):
    """
    Saves a report to a file.
    
    Args:
        report_data (dict): The report data to save
        output_path (str): Path to save the JSON report
        
    Returns:
        bool: True if the save was successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving report to {output_path}: {str(e)}")
        return False


def load_report_from_file(input_path):
    """
    Loads a report from a JSON file.
    
    Args:
        input_path (str): Path to the JSON report file
        
    Returns:
        dict: The loaded report data, or None if loading failed
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        logger.info(f"Report loaded from {input_path}")
        return report_data
    except Exception as e:
        logger.error(f"Error loading report from {input_path}: {str(e)}")
        return None


def create_report_summary(report_data):
    """
    Creates a simple text summary of the report data.
    
    Args:
        report_data (dict): The report data to summarize
        
    Returns:
        str: A text summary of the report
    """
    summary = []
    summary.append("=== Email Analysis Report Summary ===\n")
    
    # Add file metadata if available
    if "file_metadata" in report_data:
        metadata = report_data["file_metadata"]
        summary.append("File Information:")
        if "file_path" in metadata:
            summary.append(f"- File: {metadata.get('file_path', 'Unknown')}")
        if "file_size_human" in metadata:
            summary.append(f"- Size: {metadata.get('file_size_human', 'Unknown')}")
        if "email_count" in metadata:
            summary.append(f"- Emails: {metadata.get('email_count', 0)}")
        summary.append("")
    
    # Add statistics if available
    if "statistics" in report_data:
        stats = report_data["statistics"]
        summary.append("Key Statistics:")
        
        if "unique_senders" in stats:
            summary.append(f"- Unique senders: {stats.get('unique_senders', 0)}")
        if "unique_recipients" in stats:
            summary.append(f"- Unique recipients: {stats.get('unique_recipients', 0)}")
        
        # Add top senders if available
        if "top_senders" in stats and stats["top_senders"]:
            summary.append("\nTop Senders:")
            for sender in stats["top_senders"][:5]:  # Show top 5
                summary.append(f"- {sender['address']}: {sender['count']} emails")
        
        # Add attachment info if available
        if "attachments" in stats:
            att_stats = stats["attachments"]
            summary.append(f"\nAttachments:")
            summary.append(f"- Total: {att_stats.get('total_count', 0)}")
            summary.append(f"- Unique types: {att_stats.get('unique_types', 0)}")
            
            # Show top attachment types if available
            if "by_type" in att_stats and att_stats["by_type"]:
                summary.append("\nTop Attachment Types:")
                for att_type in att_stats["by_type"][:3]:  # Show top 3
                    summary.append(f"- {att_type['type']}: {att_type['count']} files ({att_type['total_size_human']})")
    
    # Add visualizations info if available
    if "visualizations" in report_data and report_data["visualizations"]:
        summary.append("\nVisualizations:")
        for viz_path in report_data["visualizations"]:
            summary.append(f"- {os.path.basename(viz_path)}")
    
    # Add generation time
    if "generated_at" in report_data:
        summary.append(f"\nReport generated at: {report_data['generated_at']}")
    
    return "\n".join(summary)


def generate_csv_report(report_data, output_path):
    """
    Generates a CSV report for key statistics.
    
    Args:
        report_data (dict): The report data
        output_path (str): Path to save the CSV report
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Write metadata
            writer = csv.writer(csvfile)
            writer.writerow(['Email Analysis Report'])
            writer.writerow(['Generated', report_data.get('generated_at', 'Unknown')])
            writer.writerow([])
            
            # Write file metadata
            if "file_metadata" in report_data:
                metadata = report_data["file_metadata"]
                writer.writerow(['File Information'])
                writer.writerow(['Path', metadata.get('file_path', 'Unknown')])
                writer.writerow(['Size', metadata.get('file_size_human', 'Unknown')])
                writer.writerow(['Email Count', metadata.get('email_count', 0)])
                writer.writerow([])
            
            # Write top senders
            if "statistics" in report_data and "top_senders" in report_data["statistics"]:
                top_senders = report_data["statistics"]["top_senders"]
                writer.writerow(['Top Senders'])
                writer.writerow(['Email Address', 'Count'])
                for sender in top_senders:
                    writer.writerow([sender['address'], sender['count']])
                writer.writerow([])
            
            # Write attachment statistics
            if "statistics" in report_data and "attachments" in report_data["statistics"]:
                attachments = report_data["statistics"]["attachments"]
                if "by_type" in attachments:
                    writer.writerow(['Attachment Types'])
                    writer.writerow(['Type', 'Count', 'Total Size', 'Average Size'])
                    for att_type in attachments["by_type"]:
                        writer.writerow([
                            att_type['type'], 
                            att_type['count'],
                            att_type['total_size_human'],
                            att_type['avg_size_human']
                        ])
        
        logger.info(f"CSV report saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating CSV report: {str(e)}")
        return False


def update_report_with_visualizations(report_data, visualization_files):
    """
    Updates a report with visualization file references.
    
    Args:
        report_data (dict): The report data to update
        visualization_files (list): List of paths to visualization files
        
    Returns:
        dict: The updated report data
    """
    # Make a copy to avoid modifying the original
    updated_report = report_data.copy()
    
    # Add or update visualizations list
    updated_report["visualizations"] = visualization_files
    
    return updated_report


def merge_reports(report_list):
    """
    Merges multiple reports into a single comprehensive report.
    
    Args:
        report_list (list): List of report dictionaries to merge
        
    Returns:
        dict: The merged report
    """
    if not report_list:
        return {}
    
    # Start with a copy of the first report
    merged_report = report_list[0].copy()
    
    # Set up merged metadata
    merged_report["merged_report"] = {
        "source_count": len(report_list),
        "source_files": []
    }
    
    # Process each additional report
    for i, report in enumerate(report_list):
        if i == 0:  # Skip the first one since we already used it as the base
            merged_report["merged_report"]["source_files"].append(
                report.get("file_metadata", {}).get("file_path", f"Report {i+1}")
            )
            continue
            
        # Add source file info
        merged_report["merged_report"]["source_files"].append(
            report.get("file_metadata", {}).get("file_path", f"Report {i+1}")
        )
        
        # Merge statistics if available
        # This is a simple merge - for a real implementation, you would
        # want to handle specific fields differently depending on their meaning
        if "statistics" in report and "statistics" in merged_report:
            # For this example, we're just adding numeric values
            for key, value in report["statistics"].items():
                if key in merged_report["statistics"]:
                    if isinstance(value, (int, float)) and isinstance(merged_report["statistics"][key], (int, float)):
                        merged_report["statistics"][key] += value
    
    # Update generation timestamp
    merged_report["generated_at"] = datetime.datetime.now().isoformat()
    merged_report["merged_at"] = datetime.datetime.now().isoformat()
    
    return merged_report

