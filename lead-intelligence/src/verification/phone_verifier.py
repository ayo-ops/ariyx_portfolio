"""
Phone Verification and Normalization Module
Formats public business phone numbers into standard E.164 notation using Google Libphonenumber.
"""

import logging
from typing import Dict, Any, Optional
import phonenumbers
from phonenumbers import PhoneNumberType

logger = logging.getLogger(__name__)


class PhoneVerifier:
    """
    Validates and standardizes public business phone numbers.
    """

    @staticmethod
    def verify(raw_phone: Optional[str], default_country: str = "US", source_url: str = "") -> Dict[str, Any]:
        """
        Parses raw phone input, validates structure, and returns E.164 formatted string.
        """
        if not raw_phone or not raw_phone.strip():
            return {
                "raw_phone": "",
                "formatted_phone": "",
                "status": "Unavailable",
                "phone_type": "None",
                "is_valid": False,
                "source_url": source_url,
                "notes": "No public phone number found."
            }

        cleaned = raw_phone.strip()
        # Normalize country code for phonenumbers library
        country = default_country.strip().upper()
        if country in ("UK", "ENGLAND", "SCOTLAND", "WALES"):
            country = "GB"

        try:
            parsed = phonenumbers.parse(cleaned, country)
            is_valid = phonenumbers.is_valid_number(parsed)

            if not is_valid:
                return {
                    "raw_phone": cleaned,
                    "formatted_phone": "",
                    "status": "Invalid",
                    "phone_type": "Invalid",
                    "is_valid": False,
                    "source_url": source_url,
                    "notes": "Number syntax is invalid for region."
                }

            formatted_e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            num_type_enum = phonenumbers.number_type(parsed)

            type_mapping = {
                PhoneNumberType.FIXED_LINE: "Landline (Business)",
                PhoneNumberType.MOBILE: "Mobile",
                PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed or Mobile",
                PhoneNumberType.TOLL_FREE: "Toll-Free",
                PhoneNumberType.VOIP: "VoIP (Cloud PBX)",
            }
            phone_type = type_mapping.get(num_type_enum, "Other")

            return {
                "raw_phone": cleaned,
                "formatted_phone": formatted_e164,
                "status": "Public Business Phone",
                "phone_type": phone_type,
                "is_valid": True,
                "source_url": source_url,
                "notes": f"Validated public business number ({phone_type})."
            }

        except phonenumbers.NumberParseException as e:
            return {
                "raw_phone": cleaned,
                "formatted_phone": "",
                "status": "Invalid",
                "phone_type": "Unparseable",
                "is_valid": False,
                "source_url": source_url,
                "notes": f"Parse error: {e}"
            }
        except Exception as e:
            logger.debug(f"Phone verification error: {e}")
            return {
                "raw_phone": cleaned,
                "formatted_phone": "",
                "status": "Invalid",
                "phone_type": "Error",
                "is_valid": False,
                "source_url": source_url,
                "notes": f"Verification error: {e}"
            }
