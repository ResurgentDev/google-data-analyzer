# mbox_email_clean.py - created: 07.03.2025
# mbox_email_clean.py - updated: 09.03.2025 - explain here - see dev diary

import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from utils import clean_text
import json

def clean_parsed_emails(input_file, output_file):
    """
    Loads parsed emails, applies cleaning, and saves cleaned data.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        emails = json.load(f)

    cleaned_emails = []
    for email in emails:
        # Clean headers and body
        email["headers"] = {k: clean_text(v) for k, v in email.get("headers", {}).items()}
        email["body"] = clean_text(email.get("body", ""))
        cleaned_emails.append(email)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_emails, f, ensure_ascii=False, indent=4)
    print(f"Cleaned emails saved to {output_file}")

if __name__ == "__main__":
    clean_parsed_emails(config.PARSED_EMAILS_JSON, config.PROCESSED_DATA_DIR + "/cleaned/cleaned_emails.json")
