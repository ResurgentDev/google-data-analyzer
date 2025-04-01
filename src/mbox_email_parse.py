# mbox_email_parse.py - created: 07.03.2025 
# mbox_email_parse.py - updated: 09.03.2025 - explain here! - see dev diary
 
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
import mailbox
import json

def get_clean_body(message):
    """
    Gets the body of a message, handling multipart messages properly.
    """
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8", errors="ignore")
    else:
        return message.get_payload(decode=True).decode("utf-8", errors="ignore")
    return None

def parse_mbox():
    """
    Parses all data from the mbox file and saves raw email metadata.
    """
    mbox = mailbox.mbox(config.MBOX_FILE)
    email_data = []
    for i, message in enumerate(mbox):
        try:
            # Convert header values to strings to make them JSON serializable
            headers = {}
            for header_name, header_value in message.items():
                headers[header_name] = str(header_value)
                
            email_info = {
                "headers": headers,  # Save all headers as strings
                "body": get_clean_body(message)
            }
            email_data.append(email_info)
        except Exception as e:
            print(f"Error parsing email #{i}: {e}")
    return email_data

def save_to_json(data, output_file):
    """
    Saves raw email data to a JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parsed_emails = parse_mbox()
    save_to_json(parsed_emails, config.PARSED_EMAILS_JSON)
    print(f"Saved {len(parsed_emails)} emails to {config.PARSED_EMAILS_JSON}")
