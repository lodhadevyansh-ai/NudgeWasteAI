"""
Validation Utilities.
Input validators for waste categories, prediction payloads, disposal statuses, and data formats.
"""

from typing import Optional
from app.core.constants import WASTE_CATEGORIES, DISPOSAL_STATUSES


def validate_waste_category(category: Optional[str]) -> bool:
    """
    Validates if a category string is strictly one of the 4 statutory waste categories:
    - Wet
    - Dry
    - Sanitary
    - Special Care

    Args:
        category: Waste category string to check.

    Returns:
        bool: True if category is valid, False otherwise.
    """
    if not category or not isinstance(category, str):
        return False
    return category.strip() in WASTE_CATEGORIES


def validate_disposal_status(status_str: Optional[str]) -> bool:
    """
    Validates if a disposal status string is one of the recognized constants:
    - verified
    - incorrect
    - uncertain
    - pending

    Args:
        status_str: Status string to validate.

    Returns:
        bool: True if valid status, False otherwise.
    """
    if not status_str or not isinstance(status_str, str):
        return False
    return status_str.strip().lower() in DISPOSAL_STATUSES


def validate_prediction_input(
    image_base64: Optional[str] = None,
    image_url: Optional[str] = None,
    item_label: Optional[str] = None,
) -> bool:
    """
    Validates that a prediction request payload contains at least one non-empty input source.

    Args:
        image_base64: Base64-encoded image string.
        image_url: Remote URL of image.
        item_label: Descriptive item text hint.

    Returns:
        bool: True if input payload is valid and non-empty, False otherwise.
    """
    if image_base64 and len(image_base64.strip()) > 0:
        return True
    if image_url and len(image_url.strip()) > 0:
        return True
    if item_label and len(item_label.strip()) > 0:
        return True
    return False
