#!/usr/bin/env python3
"""
Email Data Visualization Module

This module provides functions for creating visualizations based on email data analysis:
- Bar charts (top senders, recipients, content size, etc.)
- Line plots (email distribution over time)
- Pie charts (attachment types)
- Comparative visualizations

It's designed to work with the data format produced by the email analyzer.
"""

import os
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)


def create_top_senders_chart(from_data, output_path):
    """
    Creates a bar chart of the top email senders.
    
    Args:
        from_data (Counter): Counter object with email addresses and counts
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        top_senders = from_data.most_common(10)
        if not top_senders:
            logger.warning("No sender data available for visualization")
            return None
            
        plt.figure(figsize=(12, 6))
        senders, counts = zip(*top_senders)
        plt.bar(senders, counts, color='skyblue')
        plt.xticks(rotation=45, ha='right')
        plt.title('Top 10 Email Senders')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created top senders visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating top senders chart: {str(e)}")
        return None


def create_top_recipients_chart(to_data, output_path):
    """
    Creates a bar chart of the top email recipients.
    
    Args:
        to_data (Counter): Counter object with email addresses and counts
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        top_recipients = to_data.most_common(10)
        if not top_recipients:
            logger.warning("No recipient data available for visualization")
            return None
            
        plt.figure(figsize=(12, 6))
        recipients, counts = zip(*top_recipients)
        plt.bar(recipients, counts, color='lightgreen')
        plt.xticks(rotation=45, ha='right')
        plt.title('Top 10 Email Recipients')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created top recipients visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating top recipients chart: {str(e)}")
        return None


def create_email_distribution_chart(date_distribution, output_path):
    """
    Creates a line plot showing email distribution over time.
    
    Args:
        date_distribution (dict): Dictionary with dates as keys and counts as values
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        if not date_distribution:
            logger.warning("No date distribution data available for visualization")
            return None
            
        sorted_dates = sorted(date_distribution.items())
        dates, counts = zip(*sorted_dates)
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, counts, marker='o', linestyle='-', color='green')
        plt.xticks(rotation=45, ha='right')
        plt.title('Email Count by Month')
        plt.xlabel('Month')
        plt.ylabel('Email Count')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created email distribution visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating email distribution chart: {str(e)}")
        return None


def create_attachment_types_chart(attachment_counts, output_path):
    """
    Creates a pie chart showing distribution of attachment types.
    
    Args:
        attachment_counts (Counter): Counter object with attachment types and counts
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        if not attachment_counts:
            logger.warning("No attachment data available for visualization")
            return None
            
        top_types = attachment_counts.most_common(8)  # Top 8 types + others
        labels = [t[0] if t[0] else 'No extension' for t in top_types]
        sizes = [t[1] for t in top_types]
        
        # Add "Others" category if there are more types
        if len(attachment_counts) > 8:
            others_count = sum(c for t, c in attachment_counts.items() if t not in [l[0] for l in top_types])
            labels.append('Others')
            sizes.append(others_count)
            
        plt.figure(figsize=(10, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Attachment Types Distribution')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created attachment types visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating attachment types chart: {str(e)}")
        return None


def create_body_size_comparison_chart(plain_sizes, html_sizes, output_path):
    """
    Creates a bar chart comparing plain text and HTML body sizes.
    
    Args:
        plain_sizes (list): List of plain text body sizes in bytes
        html_sizes (list): List of HTML body sizes in bytes
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        if not plain_sizes and not html_sizes:
            logger.warning("No body size data available for visualization")
            return None
        
        # Calculate total and average sizes
        plain_total = sum(plain_sizes) if plain_sizes else 0
        html_total = sum(html_sizes) if html_sizes else 0
        plain_avg = plain_total / len(plain_sizes) if plain_sizes else 0
        html_avg = html_total / len(html_sizes) if html_sizes else 0
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create positions for the bars
        x_pos = [0, 1, 3, 4]
        
        # Plot bar chart
        ax.bar(x_pos[:2], [plain_total, html_total], width=0.8, 
               color=['lightblue', 'lightgreen'], label='Total Size')
        ax.bar(x_pos[2:], [plain_avg, html_avg], width=0.8, 
               color=['darkblue', 'darkgreen'], label='Average Size')
        
        # Add labels and titles
        ax.set_xticks(x_pos)
        ax.set_xticklabels(['Plain Text Total', 'HTML Total', 'Plain Text Avg', 'HTML Avg'])
        ax.set_title('Body Size Comparison: Plain Text vs HTML')
        ax.set_ylabel('Size in bytes')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created body size comparison visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating body size comparison chart: {str(e)}")
        return None


def create_email_domain_distribution_chart(from_data, output_path):
    """
    Creates a pie chart showing distribution of email domains from senders.
    
    Args:
        from_data (Counter): Counter object with email addresses and counts
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        if not from_data:
            logger.warning("No sender data available for domain visualization")
            return None
            
        # Extract domains from email addresses
        domains = Counter()
        for email, count in from_data.items():
            try:
                domain = email.split('@')[1].lower()
                domains[domain] += count
            except (IndexError, AttributeError):
                domains['unknown'] += count
        
        top_domains = domains.most_common(8)  # Top 8 domains + others
        labels = [d[0] for d in top_domains]
        sizes = [d[1] for d in top_domains]
        
        # Add "Others" category if there are more domains
        if len(domains) > 8:
            others_count = sum(c for d, c in domains.items() if d not in labels)
            labels.append('Others')
            sizes.append(others_count)
            
        plt.figure(figsize=(10, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Email Domain Distribution')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created email domain distribution visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating email domain distribution chart: {str(e)}")
        return None


def create_weekday_distribution_chart(date_data, output_path):
    """
    Creates a bar chart showing email distribution by day of the week.
    
    Args:
        date_data (list): List of datetime objects representing email dates
        output_path (str): Full path to save the visualization
        
    Returns:
        str: Path to the saved visualization file or None if failed
    """
    try:
        if not date_data:
            logger.warning("No date data available for weekday visualization")
            return None
            
        # Count emails by weekday
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts = Counter([d.weekday() for d in date_data])
        
        # Prepare data for plotting
        counts = [weekday_counts.get(i, 0) for i in range(7)]
        
        plt.figure(figsize=(10, 6))
        plt.bar(weekdays, counts, color='purple')
        plt.title('Email Distribution by Day of Week')
        plt.ylabel('Number of Emails')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created weekday distribution visualization: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating weekday distribution chart: {str(e)}")
        return None


def create_all_visualizations(report_data, output_dir):
    """
    Creates all available visualizations from the report data.
    
    Args:
        report_data (dict): The email analysis report data
        output_dir (str): Directory where visualization files will be saved
        
    Returns:
        list: Paths to the generated visualization files
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        visualization_files = []
        
        # 1. Top senders visualization
        if report_data.get("headers", {}).get("from"):
            from_data = Counter(report_data["headers"]["from"])
            viz_path = os.path.join(output_dir, 'top_senders.png')
            result = create_top_senders_chart(from_data, viz_path)
            if result:
                visualization_files.append(result)
        
        # 2. Top recipients visualization
        if report_data.get("headers", {}).get("to"):
            to_data = Counter(report_data["headers"]["to"])
            viz_path = os.path.join(output_dir, 'top_recipients.png')
            result = create_top_recipients_chart(to_data, viz_path)
            if result:
                visualization_files.append(result)
        
        # 3. Email distribution by month
        if report_data.get("headers", {}).get("date_distribution"):
            viz_path = os.path.join(output_dir, 'email_by_month.png')
            result = create_email_distribution_chart(
                report_data["headers"]["date_distribution"], viz_path)
            if result:
                visualization_files.append(result)
        
        # 4. Attachment types pie chart
        if report_data.get("content", {}).get("attachments", {}).get("counts_by_type"):
            attachment_counts = Counter(report_data["content"]["attachments"]["counts_by_type"])
            viz_path = os.path.join(output_dir, 'attachment_types.png')
            result = create_attachment_types_chart(attachment_counts, viz_path)
            if result:
                visualization_files.append(result)
        
        # 5. Body size comparison
        plain_sizes = report_data.get("content", {}).get("body_sizes", {}).get("plain_text", [])
        html_sizes = report_data.get("content", {}).get("body_sizes", {}).get("html", [])
        if plain_sizes or html_sizes:
            viz_path = os.path.join(output_dir, 'body_size_comparison.png')
            result = create_body_size_comparison_chart(plain_sizes, html_sizes, viz_path)
            if result:
                visualization_files.append(result)
        
        # 6. Email domain distribution
        if report_data.get("headers", {}).get("from"):
            from_data = Counter(report_data["headers"]["from"])
            viz_path = os.path.join(output_dir, 'email_domains.png')
            result = create_email_domain_distribution_chart(from_data, viz_path)
            if result:
                visualization_files.append(result)
        
        logger.info(f"Created {len(visualization_files)} visualizations in {output_dir}")
        return visualization_files
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {str(e)}")
        return []


if __name__ == "__main__":
    import sys
    import json
    
    # Simple command-line interface for testing
    if len(sys.argv) != 3:
        print("Usage: python visualizer.py <report_json_file> <output_directory>")
        sys.exit(1)
    
    report_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        viz_files = create_all_visualizations(report_data, output_dir)
        print(f"Created visualizations: {viz_files}")
    except FileNotFoundError:
        print(f"Error: Report file '{report_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{report_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating visualizations: {str(e)}")
        sys.exit(1)
