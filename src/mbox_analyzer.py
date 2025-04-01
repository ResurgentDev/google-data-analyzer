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
import email
import os
import sys
import json
import argparse
import datetime
import mimetypes
import re
from collections import Counter, defaultdict
from email.header import decode_header
import logging

# Import markdown report generation functionality
try:
    from mbox_report_to_md import process_report
except ImportError:
    def process_report(report_data):
        logger.error("mbox_report_to_md.py module not found. Cannot generate markdown summary.")
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
    def _decode_header_value(header_value):
        """
        Decodes email header values properly.
        
        Args:
            header_value: The email header value to decode
            
        Returns:
            str: Decoded header value
        """
        if not header_value:
            return ""
        
        try:
            decoded_parts = []
            for part, encoding in decode_header(header_value):
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            decoded_parts.append(part.decode(encoding))
                        except (LookupError, UnicodeDecodeError):
                            decoded_parts.append(part.decode('utf-8', errors='replace'))
                    else:
                        decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(part)
            return ' '.join(decoded_parts)
        except Exception as e:
            logger.warning(f"Error decoding header: {str(e)}")
            return str(header_value)

    @staticmethod
    def _extract_email_addresses(header_value):
        """
        Extracts email addresses from a header value.
        
        Args:
            header_value (str): The header value containing email addresses
            
        Returns:
            list: List of extracted email addresses
        """
        if not header_value:
            return []
        
        # Simple regex for email extraction
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        return re.findall(email_pattern, header_value)
    
    @staticmethod
    def _extract_subject_keywords(subject):
        """
        Extracts keywords from email subjects.
        
        Args:
            subject (str): The email subject
            
        Returns:
            list: List of keywords
        """
        if not subject:
            return []
        
        # Remove common prefixes like Re:, Fwd:, etc.
        cleaned_subject = re.sub(r'^(Re|Fwd|Fw|RE|FWD|FW):\s*', '', subject, flags=re.IGNORECASE)
        
        # Split into words and filter out common words and short words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_subject)
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'your', 'have'}
        keywords = [word.lower() for word in words if word.lower() not in common_words]
        
        return keywords
    
    @staticmethod
    def _format_size(size_bytes):
        """
        Formats a byte size into a human-readable string.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
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
            from_value = self._decode_header_value(message['from'])
            from_addresses = self._extract_email_addresses(from_value)
            for addr in from_addresses:
                self.report["headers"]["from"][addr] += 1
        
        # Process To header
        if 'to' in message:
            to_value = self._decode_header_value(message['to'])
            to_addresses = self._extract_email_addresses(to_value)
            for addr in to_addresses:
                self.report["headers"]["to"][addr] += 1
        
        # Process CC header
        if 'cc' in message:
            cc_value = self._decode_header_value(message['cc'])
            cc_addresses = self._extract_email_addresses(cc_value)
            for addr in cc_addresses:
                self.report["headers"]["cc"][addr] += 1
        
        # Process BCC header
        if 'bcc' in message:
            bcc_value = self._decode_header_value(message['bcc'])
            bcc_addresses = self._extract_email_addresses(bcc_value)
            for addr in bcc_addresses:
                self.report["headers"]["bcc"][addr] += 1
        
        # Process Subject header
        if 'subject' in message:
            subject = self._decode_header_value(message['subject'])
            keywords = self._extract_subject_keywords(subject)
            for keyword in keywords:
                self.report["headers"]["subject_keywords"][keyword] += 1
        
        # Process Date header
        if 'date' in message:
            try:
                date_str = self._decode_header_value(message['date'])
                # Try to parse the date
                date_tuple = email.utils.parsedate_tz(date_str)
                if date_tuple:
                    timestamp = email.utils.mktime_tz(date_tuple)
                    date = datetime.datetime.fromtimestamp(timestamp)
                    year_month = date.strftime('%Y-%m')
                    self.report["headers"]["date_distribution"][year_month] += 1
            except Exception as e:
                logger.warning(f"Error parsing date '{date_str}' in message {msg_idx}: {str(e)}")
    
    def analyze_content(self, message, msg_idx):
        """
        Analyzes body content and attachments of an email message.
        
        Args:
            message (mailbox.Message): The email message to analyze
            msg_idx (int): Index of the message in the mailbox
        """
        # Initialize counters for this message
        plain_text_size = 0
        html_size = 0
        attachment_sizes = []
        
        try:
            # Handle single part messages
            if not message.is_multipart():
                content_type = message.get_content_type()
                content = message.get_payload(decode=True)
                content_size = len(content) if content else 0
                
                if content_type == 'text/plain':
                    plain_text_size += content_size
                elif content_type == 'text/html':
                    html_size += content_size
                else:
                    # Treat as attachment
                    filename = self._get_filename_from_part(message)
                    if filename:
                        extension = os.path.splitext(filename)[1].lower()
                        self.report["content"]["attachments"]["counts_by_type"][extension or 'unknown'] += 1
                        self.report["content"]["attachments"]["sizes_by_type"][extension or 'unknown'].append(content_size)
                        attachment_sizes.append(content_size)
            
            # Handle multipart messages
            else:
                for part in message.walk():
                    if part.is_multipart():
                        continue
                    
                    content_type = part.get_content_type()
                    content = part.get_payload(decode=True)
                    content_size = len(content) if content else 0
                    
                    # Check for main body parts
                    if content_type == 'text/plain':
                        plain_text_size += content_size
                    elif content_type == 'text/html':
                        html_size += content_size
                    
                    # Check for attachments
                    filename = self._get_filename_from_part(part)
                    disposition = part.get('Content-Disposition', '')
                    
                    if filename or 'attachment' in disposition:
                        extension = os.path.splitext(filename)[1].lower() if filename else ''
                        self.report["content"]["attachments"]["counts_by_type"][extension or 'unknown'] += 1
                        self.report["content"]["attachments"]["sizes_by_type"][extension or 'unknown'].append(content_size)
                        attachment_sizes.append(content_size)
            
            # Record body sizes for this message
            if plain_text_size > 0:
                self.report["content"]["body_sizes"]["plain_text"].append(plain_text_size)
            
            if html_size > 0:
                self.report["content"]["body_sizes"]["html"].append(html_size)
                
        except Exception as e:
            logger.warning(f"Error analyzing content in message {msg_idx}: {str(e)}")
            self.report["errors"].append({
                "type": "content_analysis_error",
                "message": str(e),
                "message_index": msg_idx
            })
    
    @staticmethod
    def _get_filename_from_part(part):
        """
        Extracts filename from a message part.
        
        Args:
            part: Email message part
            
        Returns:
            str: Filename or empty string
        """
        filename = part.get_filename()
        if filename:
            filename = MboxAnalyzer._decode_header_value(filename)
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
    
    def create_visualizations(self, output_dir):
        """
        Creates visualizations of the email data.
        
        Args:
            output_dir (str): Directory where visualization files will be saved
            
        Returns:
            list: Paths to the generated visualization files
        """
        # Check for matplotlib availability
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
        except ImportError:
            logger.warning("Matplotlib is not available. Skipping visualizations.")
            return []
            
        visualization_files = []
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 1. Top senders visualization
            if len(self.report["headers"]["from"]) > 0:
                top_senders = self.report["headers"]["from"].most_common(10)
                if top_senders:
                    plt.figure(figsize=(12, 6))
                    senders, counts = zip(*top_senders)
                    plt.bar(senders, counts, color='skyblue')
                    plt.xticks(rotation=45, ha='right')
                    plt.title('Top 10 Email Senders')
                    plt.tight_layout()
                    sender_viz_path = os.path.join(output_dir, 'top_senders.png')
                    plt.savefig(sender_viz_path)
                    plt.close()
                    visualization_files.append(sender_viz_path)
                    
            # 2. Email distribution by month
            date_dist = self.report["headers"]["date_distribution"]
            if date_dist:
                sorted_dates = sorted(date_dist.items())
                if sorted_dates:
                    plt.figure(figsize=(12, 6))
                    dates, counts = zip(*sorted_dates)
                    plt.plot(dates, counts, marker='o', linestyle='-', color='green')
                    plt.xticks(rotation=45, ha='right')
                    plt.title('Email Count by Month')
                    plt.tight_layout()
                    date_viz_path = os.path.join(output_dir, 'email_by_month.png')
                    plt.savefig(date_viz_path)
                    plt.close()
                    visualization_files.append(date_viz_path)
                    
            # 3. Attachment types pie chart
            attachment_counts = self.report["content"]["attachments"]["counts_by_type"]
            if attachment_counts:
                top_types = attachment_counts.most_common(8)  # Top 8 types + others
                if top_types:
                    labels = [t[0] for t in top_types]
                    sizes = [t[1] for t in top_types]
                    
                    # Add "Others" category if there are more types
                    if len(attachment_counts) > 8:
                        others_count = sum(c for t, c in attachment_counts.items() if t not in labels)
                        labels.append('Others')
                        sizes.append(others_count)
                        
                    plt.figure(figsize=(10, 8))
                    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
                    plt.axis('equal')
                    plt.title('Attachment Types Distribution')
                    plt.tight_layout()
                    attachment_viz_path = os.path.join(output_dir, 'attachment_types.png')
                    plt.savefig(attachment_viz_path)
                    plt.close()
                    visualization_files.append(attachment_viz_path)
                    
            # 4. Body size comparison (HTML vs Plain Text)
            plain_sizes = self.report["content"]["body_sizes"]["plain_text"]
            html_sizes = self.report["content"]["body_sizes"]["html"]
            
            if plain_sizes or html_sizes:
                plt.figure(figsize=(10, 6))
                
                # Calculate total and average sizes
                plain_total = sum(plain_sizes) if plain_sizes else 0
                html_total = sum(html_sizes) if html_sizes else 0
                plain_avg = plain_total / len(plain_sizes) if plain_sizes else 0
                html_avg = html_total / len(html_sizes) if html_sizes else 0
                
                # Plot bar chart
                plt.bar(['Plain Text', 'HTML'], [plain_total, html_total], alpha=0.7, label='Total Size')
                plt.bar(['Plain Text Avg', 'HTML Avg'], [plain_avg, html_avg], alpha=0.7, label='Average Size')
                
                plt.title('Body Size Comparison: Plain Text vs HTML')
                plt.ylabel('Size in bytes')
                plt.legend()
                plt.tight_layout()
                body_viz_path = os.path.join(output_dir, 'body_size_comparison.png')
                plt.savefig(body_viz_path)
                plt.close()
                visualization_files.append(body_viz_path)
                
            logger.info(f"Created {len(visualization_files)} visualizations in {output_dir}")
            return visualization_files
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            return []
        
    def analyze(self):
        """
        Performs the complete analysis of the .mbox file.
        
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        if not self.open_mbox():
            return False
            
        try:
            logger.info("Starting email analysis...")
            
            # Process each message
            for i, message in enumerate(self.mbox):
                if i % 100 == 0 and i > 0:
                    logger.info(f"Processed {i} emails...")
                
                # Analyze headers
                self.analyze_headers(message, i)
                
                # Analyze content
                self.analyze_content(message, i)
                
            logger.info(f"Finished processing {self.email_count} emails")
            
            # Calculate statistics
            self.calculate_statistics()
            
            return True
        
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            self.report["errors"].append({
                "type": "analysis_error",
                "message": str(e)
            })
            return False
            
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
        serializable_report = self._make_json_serializable(self.report)
        
        # Generate visualizations if requested
        if visualize:
            viz_dir = os.path.splitext(output_path)[0] + "_visualizations" if output_path else "mbox_visualizations"
            visualization_files = self.create_visualizations(viz_dir)
            serializable_report["visualizations"] = visualization_files
            
        # Output to file if path provided
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_report, f, indent=2, ensure_ascii=False)
                logger.info(f"Report saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving report to {output_path}: {str(e)}")
                
        return serializable_report
        
    def _make_json_serializable(self, obj):
        """
        Converts the report to a JSON-serializable format.
        
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
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
            
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
            
        elif isinstance(obj, Counter):
            return dict(obj)
            
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
            
        else:
            return obj


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
            # Create markdown filename based on JSON output path
            md_output_path = os.path.splitext(args.output)[0] + ".md"
            
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
