"""
Application-wide Constants.
Centralized location for static constants, enumerations, and metadata.
"""

from enum import Enum


class WasteCategory(str, Enum):
    """Enumeration of civic waste segregation categories."""

    WET = "Wet"
    DRY = "Dry"
    SANITARY = "Sanitary"
    SPECIAL_CARE = "Special Care"
    UNKNOWN = "Unknown"


class WasteMaterial(str, Enum):
    """Enumeration of physical material categories."""

    WET_ORGANIC = "Wet / Organic"
    DRY_RECYCLABLE = "Dry Recyclable"
    PLASTIC = "Plastic"
    METAL = "Metal"
    GLASS = "Glass"
    SANITARY_HYGIENE = "Sanitary / Hygiene"
    E_WASTE_BATTERIES = "E-waste / Batteries"
    HAZARDOUS_SPECIAL = "Hazardous / Special"
    RESIDUAL_OTHER = "Residual / Other"
    UNKNOWN = "Unknown / Needs Review"


# List of valid waste categories for quick validation & lookup
WASTE_CATEGORIES = [category.value for category in WasteCategory]
WASTE_MATERIALS = [material.value for material in WasteMaterial]

# API Constants
DEFAULT_API_PREFIX = "/api/v1"
HEALTH_CHECK_ENDPOINT = "/health"

# Application Metadata
APP_NAME = "NudgeWasteAI Backend"
APP_DESCRIPTION = "Civic Waste-Segregation Platform API - Wongsknow India Hackathon"
APP_VERSION = "1.0.0"

# Health Response Statuses
STATUS_HEALTHY = "healthy"
STATUS_UNHEALTHY = "unhealthy"

# Disposal Statuses
DISPOSAL_STATUS_VERIFIED = "verified"
DISPOSAL_STATUS_INCORRECT = "incorrect"
DISPOSAL_STATUS_UNCERTAIN = "uncertain"
DISPOSAL_STATUS_PENDING = "pending"
DISPOSAL_STATUS_REJECTED = "rejected"
DISPOSAL_STATUS_UNCLEAR = "verification_unclear"

DISPOSAL_STATUSES = [
    DISPOSAL_STATUS_VERIFIED,
    DISPOSAL_STATUS_INCORRECT,
    DISPOSAL_STATUS_UNCERTAIN,
    DISPOSAL_STATUS_PENDING,
    DISPOSAL_STATUS_REJECTED,
    DISPOSAL_STATUS_UNCLEAR,
]

# Canonical Waste Category to Bin Mapping
CATEGORY_BIN_MAPPING = {
    WasteCategory.WET.value: {"color": "green", "name": "Green Bin", "category": WasteCategory.WET.value, "guide": "Place in Green Bin for municipal composting and organic recycling."},
    WasteCategory.DRY.value: {"color": "blue", "name": "Blue Bin", "category": WasteCategory.DRY.value, "guide": "Place in Blue Bin for material recycling (ensure items are clean and dry)."},
    WasteCategory.SANITARY.value: {"color": "red", "name": "Red / Sanitary Bin", "category": WasteCategory.SANITARY.value, "guide": "Wrap securely in newspaper/marked pouch and place in Red / Sanitary Bin."},
    WasteCategory.SPECIAL_CARE.value: {"color": "black", "name": "Black Bin", "category": WasteCategory.SPECIAL_CARE.value, "guide": "Hand over to E-Waste / Hazardous Waste collector or place in Black Bin."},
    WasteCategory.UNKNOWN.value: {"color": "amber", "name": "Manual Review Bin", "category": WasteCategory.UNKNOWN.value, "guide": "Recapture image clearly under good lighting or manually inspect material to select the appropriate bin."},
}

# Nudge Severity Levels
NUDGE_SEVERITY_INFO = "information"
NUDGE_SEVERITY_GUIDANCE = "guidance"
NUDGE_SEVERITY_WARNING = "warning"

NUDGE_SEVERITIES = [
    NUDGE_SEVERITY_INFO,
    NUDGE_SEVERITY_GUIDANCE,
    NUDGE_SEVERITY_WARNING,
]

# Swachh Credit Rules & Transaction Types
CREDIT_TRANSACTION_TYPE_EARN = "earn"
CREDIT_TRANSACTION_TYPE_REDEEM = "redeem"
CREDIT_TRANSACTION_TYPE_ADJUSTMENT = "adjustment"

CREDIT_RULES_BY_CATEGORY = {
    WasteCategory.WET.value: 10.0,
    WasteCategory.DRY.value: 10.0,
    WasteCategory.SANITARY.value: 15.0,
    WasteCategory.SPECIAL_CARE.value: 20.0,
}

DEFAULT_CREDIT_AWARD = 10.0
