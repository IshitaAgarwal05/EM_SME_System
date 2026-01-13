"""
Security service for PII masking, input sanitization, and security auditing.
"""

import re
import html
import structlog
from typing import Any

logger = structlog.get_logger()

class SecurityService:
    """
    Centralized security service for handling data protection and sanitization.
    """

    # Regex patterns for PII detection
    EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE_REGEX = r'(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}'
    CREDIT_CARD_REGEX = r'(?:\d{4}[- ]){3}\d{4}|\d{16}'
    # Simple Indian PAN card regex (ABCDE1234F)
    PAN_REGEX = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """
        Detects and masks PII (Email, Phone, Credit Card, PAN) in the given text.
        Replaces sensitive data with [REDACTED_TYPE].
        """
        if not text:
            return ""

        masked_text = text

        # Mask Emails
        masked_text = re.sub(cls.EMAIL_REGEX, "[REDACTED_EMAIL]", masked_text)

        # Mask Phone Numbers
        masked_text = re.sub(cls.PHONE_REGEX, "[REDACTED_PHONE]", masked_text)

        # Mask Credit Cards
        masked_text = re.sub(cls.CREDIT_CARD_REGEX, "[REDACTED_CC]", masked_text)
        
        # Mask PAN Cards
        masked_text = re.sub(cls.PAN_REGEX, "[REDACTED_PAN]", masked_text)

        if masked_text != text:
             logger.info("pii_detected_and_masked", original_length=len(text), masked_length=len(masked_text))

        return masked_text

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Sanitizes user input to prevent XSS and injection attacks.
        Escapes HTML characters.
        """
        if not text:
            return ""
        
        # Basic HTML escaping
        sanitized = html.escape(text)
        
        return sanitized

    @classmethod
    def validate_output(cls, text: str) -> bool:
        """
        Validates LLM output or other system outputs for prohibited content.
        Returns True if safe, False otherwise.
        """
        # Example: Check for simple injection success markers or prohibited words
        prohibited_terms = ["<script>", "javascript:", "DROP TABLE", "DELETE FROM"]
        
        for term in prohibited_terms:
            if term.lower() in text.lower():
                logger.warning("prohibited_content_detected", term=term)
                return False
        
        return True

    @classmethod
    def audit_event(cls, event_type: str, user_id: Any, details: dict):
        """
        Logs a security-related event.
        """
        logger.info(
            "security_audit_event",
            event_type=event_type,
            user_id=str(user_id),
            details=details
        )

security_service = SecurityService()
