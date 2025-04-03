#!/usr/bin/env python3
"""
MBOX File Analyzer

This script analyzes .mbox files and generates a comprehensive report including:
- File metadata analysis (file size, email count)
- Header analysis (From, To, CC, BCC, Subject, Date)
- Body and attachment analysis
- Content size comparison
- Statistical summary

Usage:
    python mbox_analyzer.py <path_to_mbox_file> [--output <output_file>] [--visualize] [--summary]

Arguments:
    path_to_mbox_file  : Path to the .mbox file to analyze
    --output           : Optional output file path for JSON report (default: stdout)
    --visualize        : Generate visualizations (requires matplotlib)
    --summary          : Generate a markdown summary alongside the JSON report

Example:
    python mbox_analyzer.py emails.mbox --output report.json --visualize
"""

import mailbox
import os
import sys
import json
import argparse
import datetime
import logging
from collections import Counter, defaultdict

# Import functionality from modular structure
from email_utils import decode_header, extract_email_addresses, extract_subject_keywords
from content_analyzer import analyze_content, format_size
from visualizer import create_all_visualizations
from report_utils import make_json_serializable, generate_report, update_report_with_visualizations


# Import markdown report generation functionality
try:
    from report_markdown import process_report
except ImportError:
    def process_report(report_data):
        logger.error("report_markdown.py module not found. Cannot generate markdown summary.")
        return None


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MboxAnalyzer:
    """Analyzes .mbox files and generates detailed reports on their contents."""

    def __init__(self, mbox_path):
        """
        Initialize the MboxAnalyzer with the path to the .mbox file.
        
        Args:
            mbox_path (str): Path to the .mbox file to analyze
        """
        self.mbox_path = mbox_path
        self.file_size = 0
        self.email_count = 0
        self.mbox = None
        self.report = {
            "file_metadata": {},
            "headers": {
                "from": Counter(),
                "to": Counter(),
                "cc": Counter(),
                "bcc": Counter(),
                "subject_keywords": Counter(),
                "date_distribution": defaultdict(int),
                "missing_headers": Counter()
            },
            "content": {
                "body_sizes": {
                    "plain_text": [],
                    "html": []
                },
                "attachments": {
                    "counts_by_type": Counter(),
                    "sizes_by_type": defaultdict(list)
                }
            },
            "size_comparison": {},
            "errors": []
        }
        
    def open_mbox(self):
        """
        Opens the .mbox file and performs initial analysis.
        
        Returns:
            bool: True if the file was opened successfully, False otherwise
        """
        try:
            # Get file metadata
            if not os.path.exists(self.mbox_path):
                raise FileNotFoundError(f"The file {self.mbox_path} does not exist")
                
            self.file_size = os.path.getsize(self.mbox_path)
            self.report["file_metadata"]["file_path"] = os.path.abspath(self.mbox_path)
            self.report["file_metadata"]["file_size"] = self.file_size
            self.report["file_metadata"]["file_size_human"] = self._format_size(self.file_size)
            
            # Open mailbox
            self.mbox = mailbox.mbox(self.mbox_path)
            self.email_count = len(self.mbox)
            self.report["file_metadata"]["email_count"] = self.email_count
            
            logger.info(f"Successfully opened mbox file: {self.mbox_path}")
            logger.info(f"File size: {self._format_size(self.file_size)}")
            logger.info(f"Email count: {self.email_count}")
            
            return True
        except Exception as e:
            logger.error(f"Error opening mbox file: {str(e)}")
            self.report["errors"].append({
                "type": "file_access_error",
                "message": str(e)
            })
            return False
    
    @staticmethod
    def _format_size(size_bytes):
        """
        Formats a byte size into a human-readable string.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        return format_size(size_bytes)
    
    def analyze_headers(self, message, msg_idx):
        """
        Analyzes headers of an email message.
        
        Args:
            message (mailbox.Message): The email message to analyze
            msg_idx (int): Index of the message in the mailbox
        """
        # Track missing headers
        required_headers = ['from', 'date', 'subject']
        for header in required_headers:
            if header not in message:
                self.report["headers"]["missing_headers"][header] += 1
        
        # Process From header
        if 'from' in message:
            from_value = decode_header(message['from'])
            from_addresses = extract_email_addresses(from_value)
            for addr in from_addresses:
                self.report["headers"]["from"][addr] += 1
        
        # Process To header
        if 'to' in message:
            to_value = decode_header(message['to'])
            to_addresses = extract_email_addresses(to_value)
            for addr in to_addresses:
                self.report["headers"]["to"][addr] += 1
        
        # Process CC header
        if 'cc' in message:
            cc_value = decode_header(message['cc'])
            cc_addresses = extract_email_addresses(cc_value)
            for addr in cc_addresses:
                self.report["headers"]["cc"][addr] += 1
        
        # Process BCC header
        if 'bcc' in message:
            bcc_value = decode_header(message['bcc'])
            bcc_addresses = extract_email_addresses(bcc_value)
            for addr in bcc_addresses:
                self.report["headers"]["bcc"][addr] += 1
        
        # Process Subject header
        if 'subject' in message:
            subject = decode_header(message['subject'])
            keywords = extract_subject_keywords(subject)
            for keyword in keywords:
                self.report["headers"]["subject_keywords"][keyword] += 1
        
        # Process Date header
        if 'date' in message:
            try:
                date_str = decode_header(message['date'])
                # Try to parse the date
                import email.utils
                date_tuple = email.utils.parsedate_tz(date_str)
                if date_tuple:
                    timestamp = email.utils.mktime_tz(date_tuple)
                    date = datetime.datetime.fromtimestamp(timestamp)
                    year_month = date.strftime('%Y-%m')
                    self.report["headers"]["date_distribution"][year_month] += 1
            except Exception as e:
                logger.warning(f"Error parsing date '{date_str}' in message {msg_idx}: {str(e)}")
    
    @staticmethod
    def _get_filename_from_part(part):
        """
        Extracts filename from a message part.

        Args:
            part: Email message part

        Returns:
            str: Filename or empty string
        """
        filename = None
        if part.get_filename():
            filename = part.get_filename()
        elif part.get_param('filename'):
            filename = part.get_param('filename')
        elif part.get_param('name'):
            filename = part.get_param('name')
        return filename or ""
    
    def calculate_statistics(self):
        """Calculates and adds statistical summaries to the report."""
        stats = {}
        
        # Email count statistics
        stats["email_count"] = self.email_count
        
        # From address statistics
        from_addresses = self.report["headers"]["from"]
        if from_addresses:
            stats["top_senders"] = [
                {"address": addr, "count": count} 
                for addr, count in from_addresses.most_common(10)
            ]
            stats["unique_senders"] = len(from_addresses)
        
        # To address statistics
        to_addresses = self.report["headers"]["to"]
        if to_addresses:
            stats["top_recipients"] = [
                {"address": addr, "count": count} 
                for addr, count in to_addresses.most_common(10)
            ]
            stats["unique_recipients"] = len(to_addresses)
        
        # Body size statistics
        plain_text_sizes = self.report["content"]["body_sizes"]["plain_text"]
        html_sizes = self.report["content"]["body_sizes"]["html"]
        
        if plain_text_sizes:
            stats["plain_text_body"] = {
                "count": len(plain_text_sizes),
                "total_size": sum(plain_text_sizes),
                "total_size_human": self._format_size(sum(plain_text_sizes)),
                "avg_size": sum(plain_text_sizes) / len(plain_text_sizes),
                "avg_size_human": self._format_size(sum(plain_text_sizes) / len(plain_text_sizes)),
                "min_size": min(plain_text_sizes),
                "min_size_human": self._format_size(min(plain_text_sizes)),
                "max_size": max(plain_text_sizes),
                "max_size_human": self._format_size(max(plain_text_sizes))
            }
        
        if html_sizes:
            stats["html_body"] = {
                "count": len(html_sizes),
                "total_size": sum(html_sizes),
                "total_size_human": self._format_size(sum(html_sizes)),
                "avg_size": sum(html_sizes) / len(html_sizes),
                "avg_size_human": self._format_size(sum(html_sizes) / len(html_sizes)),
                "min_size": min(html_sizes),
                "min_size_human": self._format_size(min(html_sizes)),
                "max_size": max(html_sizes),
                "max_size_human": self._format_size(max(html_sizes))
            }
            
        # Attachment statistics
        attachment_counts = self.report["content"]["attachments"]["counts_by_type"]
        attachment_sizes = self.report["content"]["attachments"]["sizes_by_type"]
        
        if attachment_counts:
            total_attachments = sum(attachment_counts.values())
            stats["attachments"] = {
                "total_count": total_attachments,
                "unique_types": len(attachment_counts),
                "by_type": []
            }
            
            for ext, count in attachment_counts.most_common():
                sizes = attachment_sizes.get(ext, [])
                total_size = sum(sizes) if sizes else 0
                
                stats["attachments"]["by_type"].append({
                    "type": ext,
                    "count": count,
                    "percentage": (count / total_attachments) * 100,
                    "total_size": total_size,
                    "total_size_human": self._format_size(total_size),
                    "avg_size": total_size / count if count > 0 else 0,
                    "avg_size_human": self._format_size(total_size / count) if count > 0 else "0 B"
                })
                
        # Missing headers statistics
        missing_headers = self.report["headers"]["missing_headers"]
        if missing_headers:
            stats["missing_headers"] = {
                "total_count": sum(missing_headers.values()),
                "by_type": [{"header": h, "count": c} for h, c in missing_headers.most_common()]
            }
            
        # Date distribution
        date_dist = self.report["headers"]["date_distribution"]
        if date_dist:
            stats["date_distribution"] = {
                "first_month": min(date_dist.keys()),
                "last_month": max(date_dist.keys()),
                "total_months": len(date_dist),
                "busiest_month": max(date_dist.items(), key=lambda x: x[1])[0],
                "busiest_month_count": max(date_dist.values())
            }
            
        # Size comparison
        parsed_data_size = self._calculate_parsed_data_size()
        stats["size_comparison"] = {
            "original_file_size": self.file_size,
            "original_file_size_human": self._format_size(self.file_size),
            "parsed_data_size": parsed_data_size,
            "parsed_data_size_human": self._format_size(parsed_data_size),
            "difference": self.file_size - parsed_data_size,
            "difference_human": self._format_size(self.file_size - parsed_data_size),
            "difference_percentage": ((self.file_size - parsed_data_size) / self.file_size) * 100 if self.file_size > 0 else 0
        }
        
        # Add stats to report
        self.report["statistics"] = stats
        
    def _calculate_parsed_data_size(self):
        """
        Calculates the total size of the parsed data.
        
        Returns:
            int: Size in bytes of all parsed content
        """
        total_size = 0
        
        # Add plain text sizes
        total_size += sum(self.report["content"]["body_sizes"]["plain_text"])
        
        # Add HTML sizes
        total_size += sum(self.report["content"]["body_sizes"]["html"])
        
        # Add attachment sizes
        for sizes in self.report["content"]["attachments"]["sizes_by_type"].values():
            total_size += sum(sizes)
            
        return total_size
    
    def analyze(self):
        """
        Analyzes the mbox file by processing each message.
        
        This method:
        - Processes each message in the mbox file
        - Calls analyze_headers() and analyze_content() for each message
        - Calculates statistics on the parsed data
        
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        try:
            if not self.open_mbox():
                return False
                
            logger.info(f"Beginning analysis of {self.email_count} emails")
            
            # Process each message
            for msg_idx, message in enumerate(self.mbox):
                try:
                    # Log progress for large mailboxes
                    if msg_idx % 100 == 0 and msg_idx > 0:
                        logger.info(f"Processed {msg_idx} emails...")
                    
                    # Analyze headers for this message
                    self.analyze_headers(message, msg_idx)
                    
                    # Analyze content for this message
                    analyze_content(message, self.report, msg_idx)
                    
                except Exception as e:
                    logger.warning(f"Error processing message {msg_idx}: {str(e)}")
                    self.report["errors"].append({
                        "type": "message_processing_error",
                        "message": str(e),
                        "message_index": msg_idx
                    })
            
            # Calculate statistics
            self.calculate_statistics()
            
            # Calculate content size comparison
            parsed_data_size = self._calculate_parsed_data_size()
            self.report["size_comparison"]["parsed_data_size"] = parsed_data_size
            self.report["size_comparison"]["parsed_data_size_human"] = format_size(parsed_data_size)
            self.report["size_comparison"]["parsed_to_file_ratio"] = parsed_data_size / self.file_size if self.file_size else 0
            
            logger.info("Analysis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            self.report["errors"].append({
                "type": "analysis_error",
                "message": str(e)
            })
            return False
    
    def create_visualizations(self, output_dir):
        """
        Creates visualizations based on the analysis data.
        
        Args:
            output_dir (str): Directory where visualization files will be saved
            
        Returns:
            list: Paths to the generated visualization files
        """
        try:
            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Call the modular visualization function
            visualization_files = create_all_visualizations(self.report, output_dir)
            
            logger.info(f"Created {len(visualization_files)} visualizations in {output_dir}")
            return visualization_files
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            return []
        
    def generate_report(self, output_path=None, visualize=False):
        """
        Generates a report of the analysis results.
        
        Args:
            output_path (str, optional): Path to save the JSON report
            visualize (bool): Whether to generate visualizations
            
        Returns:
            dict: The analysis report
        """
        # Add timestamp to report
        self.report["generated_at"] = datetime.datetime.now().isoformat()
        
        # Convert Counter objects to regular dictionaries for JSON serialization
        serializable_report = make_json_serializable(self.report)
        
        # Generate visualizations if requested
        # Generate visualizations if requested
        if visualize:
            viz_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "visualizations")
            visualization_files = self.create_visualizations(viz_dir)
            update_report_with_visualizations(self.report, visualization_files)
        # Output to file if path provided
        if output_path:
            # Ensure output goes to reports directory in project root
            report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
            os.makedirs(report_dir, exist_ok=True)
            full_output_path = os.path.join(report_dir, os.path.basename(output_path))
            try:
                with open(full_output_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_report, f, indent=2, ensure_ascii=False)
                logger.info(f"Report saved to {full_output_path}")
            except Exception as e:
                logger.error(f"Error saving report to {full_output_path}: {str(e)}")
                
        return serializable_report

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze .mbox files and generate comprehensive reports"
    )
    parser.add_argument("mbox_file", help="Path to the .mbox file to analyze")
    parser.add_argument(
        "--output", "-o", 
        help="Path to save the JSON report (default: stdout)"
    )
    parser.add_argument(
        "--visualize", "-v", 
        action="store_true", 
        help="Generate visualizations"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Generate a markdown summary alongside the JSON report"
    )
    
    args = parser.parse_args()
    
    # Visualization check will happen at runtime if requested
        
    # Check if the file exists
    if not os.path.exists(args.mbox_file):
        logger.error(f"File not found: {args.mbox_file}")
        sys.exit(1)
        
    # Check if the file is an .mbox file
    if not args.mbox_file.lower().endswith('.mbox'):
        logger.warning(f"Warning: {args.mbox_file} does not have a .mbox extension. The file may not be processed correctly.")
    
    # Create an instance of MboxAnalyzer
    analyzer = MboxAnalyzer(args.mbox_file)
    
    # Run the analysis
    success = analyzer.analyze()
    if not success:
        logger.error("Analysis failed. Please check the errors and try again.")
        sys.exit(2)
        
    # Generate and output the report
    report = analyzer.generate_report(args.output, args.visualize)
    
    # If no output file was specified, print the report to stdout
    if not args.output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Generate markdown summary if requested
    if args.summary and args.output:
        try:
            # Create markdown filename in project root reports directory
            report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
            md_output_path = os.path.join(report_dir, 
                os.path.splitext(os.path.basename(args.output))[0] + ".md")
            
            # Generate markdown content
            logger.info(f"Generating markdown summary to {md_output_path}")
            markdown_content = process_report(report)
            
            # Write markdown to file
            if markdown_content:
                with open(md_output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Markdown summary saved to {md_output_path}")
            else:
                logger.error("Failed to generate markdown summary")
        except Exception as e:
            logger.error(f"Error generating markdown summary: {str(e)}")
        
    # Exit with success code
    sys.exit(0)


if __name__ == '__main__':
    main()
