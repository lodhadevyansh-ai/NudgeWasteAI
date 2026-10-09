"""
Waste Taxonomy and Material Classification Service.
Maps physical waste items, materials, and model predictions into standardized
statutory segregation streams (Wet, Dry, Sanitary, Special Care, Unknown).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re

from app.core.constants import WasteCategory, WasteMaterial, CATEGORY_BIN_MAPPING


@dataclass
class WasteTaxonomyEntry:
    """Metadata for a waste taxonomy category."""
    material: str
    statutory_category: str
    bin_name: str
    bin_color: str
    disposal_guide: str
    keywords: List[str]
    examples: List[str]


# Authoritative Taxonomy Catalog mapping materials to statutory disposal streams
TAXONOMY_CATALOG: Dict[str, WasteTaxonomyEntry] = {
    WasteMaterial.WET_ORGANIC.value: WasteTaxonomyEntry(
        material=WasteMaterial.WET_ORGANIC.value,
        statutory_category=WasteCategory.WET.value,
        bin_name="Green Bin",
        bin_color="green",
        disposal_guide="Place in Green Bin for municipal composting and biomethanation.",
        keywords=[
            "banana", "peel", "apple", "fruit", "vegetable", "food", "scrap", "leftover",
            "organic", "compost", "kitchen", "tea", "coffee ground", "leaves", "bread",
            "egg shell", "biological", "citrus", "salad", "curry", "rice", "bone",
        ],
        examples=["Banana peels", "Fruit scraps", "Vegetable leftovers", "Tea leaves", "Kitchen waste"],
    ),
    WasteMaterial.PLASTIC.value: WasteTaxonomyEntry(
        material=WasteMaterial.PLASTIC.value,
        statutory_category=WasteCategory.DRY.value,
        bin_name="Blue Bin",
        bin_color="blue",
        disposal_guide="Place in Blue Bin for material recycling (ensure items are clean and empty).",
        keywords=[
            "plastic bottle", "pet bottle", "plastic container", "plastic bag", "polythene",
            "plastic cup", "plastic jug", "shampoo bottle", "detergent bottle", "plastic wrapper",
            "plastic cap", "plastic jar", "tupperware", "plastic", "polyester",
        ],
        examples=["Plastic beverage bottles", "Rigid plastic containers", "Detergent jugs", "Clean packaging film"],
    ),
    WasteMaterial.DRY_RECYCLABLE.value: WasteTaxonomyEntry(
        material=WasteMaterial.DRY_RECYCLABLE.value,
        statutory_category=WasteCategory.DRY.value,
        bin_name="Blue Bin",
        bin_color="blue",
        disposal_guide="Place in Blue Bin for paper and fiber recycling (flatten and keep dry).",
        keywords=[
            "paper", "cardboard", "box", "carton", "newspaper", "magazine", "office paper",
            "envelope", "tissue roll core", "flyer", "pamphlet", "notebook", "tetra pak",
            "egg carton", "packaging box", "shipping box",
        ],
        examples=["Clean cardboard boxes", "Newspapers", "Office paper", "Flattened carton packaging"],
    ),
    WasteMaterial.METAL.value: WasteTaxonomyEntry(
        material=WasteMaterial.METAL.value,
        statutory_category=WasteCategory.DRY.value,
        bin_name="Blue Bin",
        bin_color="blue",
        disposal_guide="Place in Blue Bin for metal and aluminium recycling (rinse clean).",
        keywords=[
            "can", "aluminium can", "soda can", "tin can", "metal", "foil", "aluminium foil",
            "tin lid", "bottle cap", "metal cap", "scrap metal", "steel can", "brass",
        ],
        examples=["Aluminium beverage cans", "Tin food cans", "Clean metal lids", "Clean aluminium foil"],
    ),
    WasteMaterial.GLASS.value: WasteTaxonomyEntry(
        material=WasteMaterial.GLASS.value,
        statutory_category=WasteCategory.DRY.value,
        bin_name="Blue Bin",
        bin_color="blue",
        disposal_guide="Place in Blue Bin for glass recycling (rinse clean and keep intact).",
        keywords=[
            "glass", "glass bottle", "glass jar", "wine bottle", "beer bottle", "jam jar",
            "sauce bottle", "cullet", "mason jar",
        ],
        examples=["Glass beverage bottles", "Glass pickle/jam jars", "Intact glass containers"],
    ),
    WasteMaterial.SANITARY_HYGIENE.value: WasteTaxonomyEntry(
        material=WasteMaterial.SANITARY_HYGIENE.value,
        statutory_category=WasteCategory.SANITARY.value,
        bin_name="Red / Sanitary Bin",
        bin_color="red",
        disposal_guide="Wrap securely in newspaper marked with a red cross; place in Red / Sanitary Bin for high-temperature incineration.",
        keywords=[
            "sanitary pad", "menstrual pad", "sanitary napkin", "tampon", "diaper", "nappy",
            "used tissue", "gauze", "bandage", "cotton swab", "q-tip", "wound dressing",
            "face mask", "surgical mask", "medical cap", "shoe cover", "sanitary", "hygiene",
        ],
        examples=["Sanitary pads & napkins", "Diapers", "Wound dressings & gauze", "Used facial tissues"],
    ),
    WasteMaterial.E_WASTE_BATTERIES.value: WasteTaxonomyEntry(
        material=WasteMaterial.E_WASTE_BATTERIES.value,
        statutory_category=WasteCategory.SPECIAL_CARE.value,
        bin_name="Black Bin",
        bin_color="black",
        disposal_guide="Never throw in normal trash! Store safely and hand over to authorized E-Waste collectors or place in Black Bin.",
        keywords=[
            "battery", "lithium", "lithium battery", "li-ion", "dry cell", "aa battery",
            "aaa battery", "phone battery", "laptop battery", "e-waste", "circuit board",
            "charger", "cable", "usb cable", "electronic", "cell phone", "calculator",
            "remote control", "earphone", "power bank",
        ],
        examples=["Lithium-ion batteries", "Household dry cells", "Discarded electronics & chargers"],
    ),
    WasteMaterial.HAZARDOUS_SPECIAL.value: WasteTaxonomyEntry(
        material=WasteMaterial.HAZARDOUS_SPECIAL.value,
        statutory_category=WasteCategory.SPECIAL_CARE.value,
        bin_name="Black Bin",
        bin_color="black",
        disposal_guide="Hazardous / Biohazard material. Keep separate and dispose of via authorized hazardous waste facility or Black Bin.",
        keywords=[
            "chemical", "paint", "pesticide", "aerosol", "spray can", "medicine", "pill",
            "blister pack", "tube", "test tube", "urine bag", "syringe", "needle", "sharp",
            "broken glass", "fluorescent bulb", "cfl", "led bulb", "tube light", "thermometer",
            "hazardous", "toxic", "poison",
        ],
        examples=["Fluorescent bulbs", "Expired medicines & blister packs", "Paint cans & chemicals", "Pressurized aerosols"],
    ),
    WasteMaterial.RESIDUAL_OTHER.value: WasteTaxonomyEntry(
        material=WasteMaterial.RESIDUAL_OTHER.value,
        statutory_category=WasteCategory.DRY.value,
        bin_name="Blue Bin",
        bin_color="blue",
        disposal_guide="Non-recyclable domestic residual waste. Dispose of per municipal non-biodegradable collection.",
        keywords=["ceramic", "dust", "sweepings", "ash", "composite", "inert", "residual"],
        examples=["Inert dust & sweepings", "Broken ceramics", "Multi-layer laminate packaging"],
    ),
    WasteMaterial.UNKNOWN.value: WasteTaxonomyEntry(
        material=WasteMaterial.UNKNOWN.value,
        statutory_category=WasteCategory.UNKNOWN.value,
        bin_name="Manual Review Bin",
        bin_color="amber",
        disposal_guide="Recapture item clearly under good lighting, or visually inspect the material to select the appropriate bin.",
        keywords=["unknown", "blurry", "unidentified", "uncertain", "ambiguous", "dark", "low_conf"],
        examples=["Unclear photographs", "Obscured items", "Mixed unsegregated items"],
    ),
}


# Default fallback for canonical vision classes (when no text hint or material sub-type is detected)
STATUTORY_DEFAULTS = {
    WasteCategory.WET.value: {
        "material": WasteMaterial.WET_ORGANIC.value,
        "label": "Organic / Wet Waste",
        "bin_name": "Green Bin",
        "guide": "Place in Green Bin for municipal composting and organic recycling.",
    },
    WasteCategory.DRY.value: {
        "material": WasteMaterial.DRY_RECYCLABLE.value,
        "label": "Dry Recyclable Waste",
        "bin_name": "Blue Bin",
        "guide": "Ensure item is clean and dry; place in Blue Bin for material recycling.",
    },
    WasteCategory.SANITARY.value: {
        "material": WasteMaterial.SANITARY_HYGIENE.value,
        "label": "Sanitary / Hygiene Waste",
        "bin_name": "Red / Sanitary Bin",
        "guide": "Wrap securely in newspaper/marked pouch and place in Red / Sanitary Bin.",
    },
    WasteCategory.SPECIAL_CARE.value: {
        "material": WasteMaterial.E_WASTE_BATTERIES.value,
        "label": "Special Care / Domestic Hazardous Waste",
        "bin_name": "Black Bin",
        "guide": "Hand over to E-Waste / Hazardous Waste collector or place in Black Bin.",
    },
    WasteCategory.UNKNOWN.value: {
        "material": WasteMaterial.UNKNOWN.value,
        "label": "Unidentified Object",
        "bin_name": "Manual Review Bin",
        "guide": "Recapture image clearly under good lighting or manually inspect material to select the appropriate bin.",
    },
}


def clean_text_hint(text: Optional[str]) -> Optional[str]:
    """
    Cleans user hint text and rejects generic image filenames (e.g. image.jpg, IMG_001.png).
    """
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned:
        return None

    # Check if text is just a raw camera/file upload filename
    # e.g. "image.jpg", "IMG_1234.JPEG", "photo.png", "frame_01.webp"
    file_pattern = re.compile(r'^(?:img_?\d+|image\d*|photo\d*|picture\d*|frame\d*|upload\d*|captured?|untitled\d*)\.(?:jpe?g|png|webp|gif|bmp|tiff?)$', re.IGNORECASE)
    if file_pattern.match(cleaned):
        return None

    # Strip file extension if user typed "plastic_bottle.jpg"
    cleaned = re.sub(r'\.(jpe?g|png|webp|gif|bmp)$', '', cleaned, flags=re.IGNORECASE)
    # Replace underscores/dashes with spaces
    cleaned = cleaned.replace('_', ' ').replace('-', ' ').strip()
    return cleaned if len(cleaned) >= 2 else None


def match_hint_to_taxonomy(hint: str) -> Optional[WasteTaxonomyEntry]:
    """
    Matches text hint keywords against the comprehensive taxonomy catalog.
    Matches longer/more specific phrases first.
    """
    clean_h = hint.lower().strip()
    if not clean_h:
        return None

    # 1. Exact phrase matching
    best_entry = None
    longest_match_len = 0

    for entry in TAXONOMY_CATALOG.values():
        for kw in entry.keywords:
            # Word boundary search for keyword
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, clean_h):
                if len(kw) > longest_match_len:
                    longest_match_len = len(kw)
                    best_entry = entry

    return best_entry


def resolve_taxonomy(
    predicted_stream: Optional[str],
    confidence: float,
    item_hint: Optional[str] = None,
    min_confidence: float = 0.60,
) -> Dict[str, Any]:
    """
    Integrates vision model prediction with optional item hint and taxonomy catalog.

    Returns:
        Dict containing:
            - statutory_category: str or None (Wet, Dry, Sanitary, Special Care, Unknown)
            - material_category: str (e.g. Plastic, E-waste / Batteries, Sanitary / Hygiene)
            - item_label: str
            - bin_name: str
            - bin_color: str
            - disposal_guide: str
            - is_uncertain: bool
    """
    cleaned_hint = clean_text_hint(item_hint)
    hint_entry = match_hint_to_taxonomy(cleaned_hint) if cleaned_hint else None

    # If the user explicitly provided an unknown/uncertain keyword (e.g. "blurry", "unknown")
    if hint_entry and hint_entry.material == WasteMaterial.UNKNOWN.value:
        return {
            "statutory_category": None,
            "material_category": WasteMaterial.UNKNOWN.value,
            "item_label": cleaned_hint.title() if cleaned_hint else "Unidentified Object",
            "bin_name": "Manual Review Bin",
            "bin_color": "amber",
            "disposal_guide": TAXONOMY_CATALOG[WasteMaterial.UNKNOWN.value].disposal_guide,
            "is_uncertain": True,
        }

    # Case 1: Vision model produced a high confidence prediction (>= min_confidence)
    if predicted_stream in [c.value for c in WasteCategory if c != WasteCategory.UNKNOWN] and confidence >= min_confidence:
        # If user also gave an informative hint that aligns with or refines the stream
        if hint_entry:
            # Hint provides granular material (e.g. Plastic bottle -> Plastic material, Dry stream)
            mat = hint_entry.material
            cat = hint_entry.statutory_category
            label = cleaned_hint.title()
            bin_name = hint_entry.bin_name
            bin_color = hint_entry.bin_color
            guide = hint_entry.disposal_guide
        else:
            default_meta = STATUTORY_DEFAULTS.get(predicted_stream, STATUTORY_DEFAULTS[WasteCategory.DRY.value])
            mat = default_meta["material"]
            cat = predicted_stream
            label = cleaned_hint.title() if cleaned_hint else default_meta["label"]
            bin_name = default_meta["bin_name"]
            bin_color = CATEGORY_BIN_MAPPING.get(cat, {}).get("color", "blue")
            guide = default_meta["guide"]

        return {
            "statutory_category": cat,
            "material_category": mat,
            "item_label": label,
            "bin_name": bin_name,
            "bin_color": bin_color,
            "disposal_guide": guide,
            "is_uncertain": False,
        }

    # Case 2: Vision model is low-confidence or failed, but user gave a valid, recognized item hint
    if hint_entry and hint_entry.material != WasteMaterial.UNKNOWN.value:
        return {
            "statutory_category": hint_entry.statutory_category,
            "material_category": hint_entry.material,
            "item_label": cleaned_hint.title() if cleaned_hint else hint_entry.material,
            "bin_name": hint_entry.bin_name,
            "bin_color": hint_entry.bin_color,
            "disposal_guide": hint_entry.disposal_guide,
            "is_uncertain": False,
        }

    # Case 3: Vision model is low-confidence AND no recognizable text hint was supplied
    # Must NOT guess or default to Dry! Return clean Unknown / Needs review state.
    label = cleaned_hint.title() if cleaned_hint else "Unidentified Object"
    return {
        "statutory_category": None,
        "material_category": WasteMaterial.UNKNOWN.value,
        "item_label": label,
        "bin_name": "Manual Review Bin",
        "bin_color": "amber",
        "disposal_guide": (
            f"Low confidence ({confidence * 100:.1f}% < {min_confidence * 100:.0f}%). "
            "Please recapture under good lighting, or visually verify the waste item before disposing."
        ),
        "is_uncertain": True,
    }
