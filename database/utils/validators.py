"""
Database Document Validators.
Validation helpers for waste categories, disposal statuses, credit transactions, and PyMongo ObjectIDs.
"""

from typing import Any, Optional
import bson

STATUTORY_WASTE_CATEGORIES = ["Wet", "Dry", "Sanitary", "Special Care"]
DISPOSAL_STATUSES = ["verified", "incorrect", "uncertain", "pending", "rejected", "verification_unclear"]
CREDIT_TRANSACTION_TYPES = ["earn", "redeem", "adjustment"]
NUDGE_SEVERITIES = ["information", "guidance", "warning"]


def validate_statutory_category(category: Optional[str]) -> bool:
    """
    Validates if input string matches one of the 4 statutory waste categories.
    """
    if not category or not isinstance(category, str):
        return False
    return category.strip() in STATUTORY_WASTE_CATEGORIES


def validate_disposal_status(status_str: Optional[str]) -> bool:
    """
    Validates if input string matches recognized disposal verification statuses.
    """
    if not status_str or not isinstance(status_str, str):
        return False
    return status_str.strip().lower() in DISPOSAL_STATUSES


def validate_transaction_type(tx_type: Optional[str]) -> bool:
    """
    Validates credit transaction type ('earn', 'redeem', 'adjustment').
    """
    if not tx_type or not isinstance(tx_type, str):
        return False
    return tx_type.strip().lower() in CREDIT_TRANSACTION_TYPES


def validate_nudge_severity(severity: Optional[str]) -> bool:
    """
    Validates nudge severity ('information', 'guidance', 'warning').
    """
    if not severity or not isinstance(severity, str):
        return False
    return severity.strip().lower() in NUDGE_SEVERITIES


def convert_objectid_to_str(value: Any) -> str:
    """
    Converts PyMongo ObjectId or string representation to a clean string ID.

    Args:
        value: ObjectId, string UUID, or object.

    Returns:
        str: String representation of ID.
    """
    if value is None:
        return ""
    if isinstance(value, bson.ObjectId):
        return str(value)
    return str(value)
