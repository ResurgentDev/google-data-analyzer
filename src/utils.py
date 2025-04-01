# utils.py - Created 09.03.2025

def clean_text(text):
    """
    Cleans input text by replacing unusual line terminators and trimming whitespace.
    """
    if not text:
        return None
    unusual_line_terminators = ['\u2028', '\u2029']  # LS, PS
    for char in unusual_line_terminators:
        text = text.replace(char, '\n')
    return text.strip()

def is_spam(email_info):
    """
    Detects whether an email is likely to be spam based on keywords in the subject.
    """
    spam_keywords = ["winner", "lottery", "free", "cash"]
    subject = str(email_info.get("subject", ""))
    for keyword in spam_keywords:
        if keyword.lower() in subject.lower():
            return True
    return False
