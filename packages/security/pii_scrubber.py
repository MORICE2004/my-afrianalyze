"""
Privacy controls for the AfriAnalyze platform.
"""
import re

class PIIScrubber:
    """Scrub Personally Identifiable Information from text."""

    @staticmethod
    def scrub_text(text: str) -> str:
        """
        Scrub emails, phone numbers, and IDs from the given text.
        """
        if not text:
            return text

        # Scrub Emails
        email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        text = re.sub(email_regex, '[REDACTED_EMAIL]', text)

        # Scrub Phone Numbers (simple international/local formats)
        # Matches formats like +123 456 7890, (123) 456-7890, 123-456-7890
        phone_regex = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        text = re.sub(phone_regex, '[REDACTED_PHONE]', text)

        # Scrub potentially sensitive IDs (e.g. National IDs, SSN).
        id_regex = r'\b\d{3}-\d{2}-\d{4}\b'
        text = re.sub(id_regex, '[REDACTED_ID]', text)

        return text
