"""
Centralized Class Mapper for NudgeWasteAI Machine Learning Pipeline
===================================================================

This module provides a centralized, traceable mapping from all source dataset
labels to the four canonical NudgeWasteAI waste segregation classes:
    1. Wet
    2. Dry
    3. Sanitary
    4. Special Care

Safety & Design Principles:
---------------------------
1. Traceability: original dataset -> original label -> canonical class.
2. Conservative mapping: Ambiguous, heterogeneous, out-of-scope, or non-waste
   categories are marked as EXCLUDED with documented rationales.
3. Centralized authority: Prevents scattered or ad-hoc hardcoded label conversions.
4. Multi-modal label support: Handles both directory class names and annotation
   IDs/variants (e.g. COCO category IDs, filenames, underscores vs spaces).
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union


class CanonicalClass(str, Enum):
    WET = "Wet"
    DRY = "Dry"
    SANITARY = "Sanitary"
    SPECIAL_CARE = "Special Care"


class MappingStatus(str, Enum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ZERO = "ZERO"


CANONICAL_CLASSES: List[str] = [c.value for c in CanonicalClass]

CLASS_TO_IDX: Dict[str, int] = {
    CanonicalClass.WET.value: 0,
    CanonicalClass.DRY.value: 1,
    CanonicalClass.SANITARY.value: 2,
    CanonicalClass.SPECIAL_CARE.value: 3,
}

IDX_TO_CLASS: Dict[int, str] = {v: k for k, v in CLASS_TO_IDX.items()}


@dataclass(frozen=True)
class MappingEntry:
    dataset: str
    original_label: str
    canonical_class: Optional[str]
    status: str
    confidence: str
    reason: str

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# DATASET-SPECIFIC CANONICAL MAPPINGS
# =============================================================================

# 1. Garbage_Classification (Gary Thung & Mindy Yang)
GARBAGE_CLASSIFICATION_MAP: Dict[str, MappingEntry] = {
    "cardboard": MappingEntry(
        dataset="Garbage_Classification",
        original_label="cardboard",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clean corrugated cardboard and paperboard packaging; standard recyclable dry stream.",
    ),
    "glass": MappingEntry(
        dataset="Garbage_Classification",
        original_label="glass",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Intact glass bottles and jars; standard recyclable dry stream.",
    ),
    "metal": MappingEntry(
        dataset="Garbage_Classification",
        original_label="metal",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Aluminium and tin cans, metal containers; standard recyclable dry stream.",
    ),
    "paper": MappingEntry(
        dataset="Garbage_Classification",
        original_label="paper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Office paper, newspaper, clean paper sheets; standard recyclable dry stream.",
    ),
    "plastic": MappingEntry(
        dataset="Garbage_Classification",
        original_label="plastic",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Rigid and container plastics, bottles; standard recyclable dry stream.",
    ),
    "trash": MappingEntry(
        dataset="Garbage_Classification",
        original_label="trash",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Heterogeneous unsegregated mixed garbage (packaging fragments, Styrofoam, mixed debris); violates single-stream classification and lacks semantic consistency.",
    ),
}

# 2. Garbage_Dataset_(GD)
GARBAGE_DATASET_GD_MAP: Dict[str, MappingEntry] = {
    "battery": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="battery",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Domestic hazardous e-waste containing toxic heavy metals (lead, lithium, cadmium, acid); poses severe fire and contamination hazards.",
    ),
    "biological": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="biological",
        canonical_class=CanonicalClass.WET.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Biodegradable organic matter, food remains, kitchen vegetable/fruit waste; canonical wet waste stream.",
    ),
    "cardboard": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="cardboard",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Cardboard and corrugated shipping boxes; standard recyclable dry stream.",
    ),
    "clothes": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="clothes",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Textiles and wearable apparel are handled through donation or dedicated textile recycling, not standard municipal daily waste bins. Inclusion creates high risk of false positives on user clothing in camera feeds.",
    ),
    "glass": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="glass",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Recyclable glass containers and bottles; standard recyclable dry stream.",
    ),
    "metal": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="metal",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Cans, beverage tins, recyclable metal scrap; standard recyclable dry stream.",
    ),
    "paper": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="paper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clean paper, newsprint, cardboard-free paper waste; standard recyclable dry stream.",
    ),
    "plastic": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="plastic",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Plastic beverage bottles, consumer plastic packaging; standard recyclable dry stream.",
    ),
    "shoes": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="shoes",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Footwear is out of scope for standard household 4-stream daily waste sorting; induces false positives when user footwear is visible in camera frames.",
    ),
    "trash": MappingEntry(
        dataset="Garbage_Dataset_(GD)",
        original_label="trash",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Heterogeneous catch-all garbage category without consistent physical or material attributes; excluded to prevent label noise.",
    ),
}

# 3. Medical_Waste_Dataset (Medical Waste 4.0)
MEDICAL_WASTE_DATASET_MAP: Dict[str, MappingEntry] = {
    "gauze": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="gauze",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Wound dressings, absorbent cotton gauze pads; under solid waste management rules (e.g. SWM Rules 2016), soiled cotton, dressings, and bandages are explicitly classified as Sanitary Waste.",
    ),
    "glove_pair_latex": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_pair_latex",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clinical latex examination gloves; contaminated biomedical personal protective equipment with potential biohazard contact.",
    ),
    "glove_pair_nitrile": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_pair_nitrile",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clinical nitrile examination gloves; contaminated protective equipment subject to biohazard precautions.",
    ),
    "glove_pair_surgery": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_pair_surgery",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Surgical procedure gloves; direct clinical exposure to blood and biological fluids; strictly biomedical Special Care waste.",
    ),
    "glove_single_latex": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_single_latex",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single clinical latex examination glove; contaminated biomedical barrier.",
    ),
    "glove_single_nitrile": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_single_nitrile",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single clinical nitrile examination glove; contaminated biomedical barrier.",
    ),
    "glove_single_surgery": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="glove_single_surgery",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single surgical procedure glove; clinical biohazard item.",
    ),
    "medical_cap": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="medical_cap",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Disposable non-woven head cover/hairnet used as a sanitary personal hygiene barrier.",
    ),
    "medical_glasses": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="medical_glasses",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Durable, washable plastic protective eye goggles; primarily reusable safety apparatus rather than single-use disposable waste.",
    ),
    "shoe_cover_pair": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="shoe_cover_pair",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Disposable non-woven polypropylene shoe covers; single-use personal sanitary barrier apparel.",
    ),
    "shoe_cover_single": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="shoe_cover_single",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Single disposable non-woven shoe cover; single-use personal sanitary barrier apparel.",
    ),
    "test_tube": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="test_tube",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clinical and laboratory specimen tubes containing or exposed to biological samples, blood, or reagents; high-risk biohazard Special Care.",
    ),
    "urine_bag": MappingEntry(
        dataset="Medical_Waste_Dataset",
        original_label="urine_bag",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clinical drainage collection bag holding human physiological fluids; biohazard medical Special Care waste.",
    ),
}

# 4. TACO (Trash Annotations in Context - 60 categories)
TACO_MAP: Dict[str, MappingEntry] = {
    "Aluminium foil": MappingEntry(
        dataset="TACO",
        original_label="Aluminium foil",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clean aluminium food foil; recyclable dry metal.",
    ),
    "Battery": MappingEntry(
        dataset="TACO",
        original_label="Battery",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Household batteries contain acid, lithium, and toxic heavy metals; domestic hazardous Special Care waste.",
    ),
    "Aluminium blister pack": MappingEntry(
        dataset="TACO",
        original_label="Aluminium blister pack",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Pharmaceutical medicine packaging; associated with pharmaceutical residues and domestic medical waste.",
    ),
    "Carded blister pack": MappingEntry(
        dataset="TACO",
        original_label="Carded blister pack",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Pharmaceutical packaging for pills/capsules; pharmaceutical Special Care stream.",
    ),
    "Other plastic bottle": MappingEntry(
        dataset="TACO",
        original_label="Other plastic bottle",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Recyclable plastic container bottles.",
    ),
    "Clear plastic bottle": MappingEntry(
        dataset="TACO",
        original_label="Clear plastic bottle",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clear PET beverage bottle; canonical recyclable dry waste.",
    ),
    "Glass bottle": MappingEntry(
        dataset="TACO",
        original_label="Glass bottle",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Recyclable glass beverage bottle.",
    ),
    "Plastic bottle cap": MappingEntry(
        dataset="TACO",
        original_label="Plastic bottle cap",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Polypropylene/HDPE plastic bottle closures; recyclable dry plastic.",
    ),
    "Metal bottle cap": MappingEntry(
        dataset="TACO",
        original_label="Metal bottle cap",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Crown cork or aluminium bottle cap; recyclable dry metal.",
    ),
    "Broken glass": MappingEntry(
        dataset="TACO",
        original_label="Broken glass",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Sharp cullet and glass shards present severe physical puncture/injury risks to sanitation handlers; requires special handling.",
    ),
    "Food Can": MappingEntry(
        dataset="TACO",
        original_label="Food Can",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Steel/tin canned food container; recyclable dry metal.",
    ),
    "Aerosol": MappingEntry(
        dataset="TACO",
        original_label="Aerosol",
        canonical_class=CanonicalClass.SPECIAL_CARE.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Pressurized aerosol canister with flammable propellants and chemical residue; explosion and toxicity hazard requiring Special Care.",
    ),
    "Drink can": MappingEntry(
        dataset="TACO",
        original_label="Drink can",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Aluminium beverage can; high-value recyclable dry stream.",
    ),
    "Toilet tube": MappingEntry(
        dataset="TACO",
        original_label="Toilet tube",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Clean cardboard roll core; recyclable paperboard dry stream.",
    ),
    "Other carton": MappingEntry(
        dataset="TACO",
        original_label="Other carton",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Paperboard packaging; recyclable dry stream.",
    ),
    "Egg carton": MappingEntry(
        dataset="TACO",
        original_label="Egg carton",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Molded pulp or clear plastic egg carton; dry recyclable.",
    ),
    "Drink carton": MappingEntry(
        dataset="TACO",
        original_label="Drink carton",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Aseptic beverage carton (Tetra Pak); recyclable dry stream.",
    ),
    "Corrugated carton": MappingEntry(
        dataset="TACO",
        original_label="Corrugated carton",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Corrugated shipping cardboard box; canonical recyclable dry waste.",
    ),
    "Meal carton": MappingEntry(
        dataset="TACO",
        original_label="Meal carton",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Paperboard takeout meal box; dry packaging stream.",
    ),
    "Pizza box": MappingEntry(
        dataset="TACO",
        original_label="Pizza box",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Corrugated pizza box packaging; standard packaging dry stream.",
    ),
    "Paper cup": MappingEntry(
        dataset="TACO",
        original_label="Paper cup",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single-use paper beverage cup; dry stream.",
    ),
    "Disposable plastic cup": MappingEntry(
        dataset="TACO",
        original_label="Disposable plastic cup",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single-use plastic drink cup; recyclable dry stream.",
    ),
    "Foam cup": MappingEntry(
        dataset="TACO",
        original_label="Foam cup",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Expanded polystyrene foam beverage cup; non-biodegradable dry waste.",
    ),
    "Glass cup": MappingEntry(
        dataset="TACO",
        original_label="Glass cup",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Glass drinking tumbler; recyclable glass dry stream.",
    ),
    "Other plastic cup": MappingEntry(
        dataset="TACO",
        original_label="Other plastic cup",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Rigid plastic cup; recyclable dry stream.",
    ),
    "Food waste": MappingEntry(
        dataset="TACO",
        original_label="Food waste",
        canonical_class=CanonicalClass.WET.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Biodegradable food scraps, fruit remnants, kitchen organic waste; canonical Wet waste.",
    ),
    "Glass jar": MappingEntry(
        dataset="TACO",
        original_label="Glass jar",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Food/jam glass container jar; recyclable dry glass.",
    ),
    "Plastic lid": MappingEntry(
        dataset="TACO",
        original_label="Plastic lid",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Plastic cup or container lid; dry plastic.",
    ),
    "Metal lid": MappingEntry(
        dataset="TACO",
        original_label="Metal lid",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Metal jar/can lid; recyclable dry metal.",
    ),
    "Other plastic": MappingEntry(
        dataset="TACO",
        original_label="Other plastic",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Miscellaneous plastic consumer items; dry plastic stream.",
    ),
    "Magazine paper": MappingEntry(
        dataset="TACO",
        original_label="Magazine paper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Glossy periodical and magazine paper; recyclable dry paper.",
    ),
    "Tissues": MappingEntry(
        dataset="TACO",
        original_label="Tissues",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Facial tissues, handkerchiefs, napkins containing bodily secretions or personal hygiene residues; canonical Sanitary waste.",
    ),
    "Wrapping paper": MappingEntry(
        dataset="TACO",
        original_label="Wrapping paper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Decorative paper wrap; recyclable dry paper.",
    ),
    "Normal paper": MappingEntry(
        dataset="TACO",
        original_label="Normal paper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Standard printer and notebook paper sheets; recyclable dry paper.",
    ),
    "Paper bag": MappingEntry(
        dataset="TACO",
        original_label="Paper bag",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Kraft paper grocery shopping bag; recyclable dry paper.",
    ),
    "Plastified paper bag": MappingEntry(
        dataset="TACO",
        original_label="Plastified paper bag",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Polymer-laminated paper carrier bag; dry packaging stream.",
    ),
    "Plastic film": MappingEntry(
        dataset="TACO",
        original_label="Plastic film",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Thin plastic cling film and shrink wrap; dry plastic stream.",
    ),
    "Six pack rings": MappingEntry(
        dataset="TACO",
        original_label="Six pack rings",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="LDPE beverage can collar rings; recyclable dry plastic.",
    ),
    "Garbage bag": MappingEntry(
        dataset="TACO",
        original_label="Garbage bag",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Polyethylene bin liner film; dry plastic waste.",
    ),
    "Other plastic wrapper": MappingEntry(
        dataset="TACO",
        original_label="Other plastic wrapper",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Plastic outer packaging film and confectionery wrappers; dry plastic.",
    ),
    "Single-use carrier bag": MappingEntry(
        dataset="TACO",
        original_label="Single-use carrier bag",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="HDPE/LDPE grocery carry bag; dry plastic.",
    ),
    "Polypropylene bag": MappingEntry(
        dataset="TACO",
        original_label="Polypropylene bag",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Woven/non-woven polypropylene shopping bag; dry plastic/textile stream.",
    ),
    "Crisp packet": MappingEntry(
        dataset="TACO",
        original_label="Crisp packet",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Metallized plastic film snack bag; dry non-biodegradable packaging.",
    ),
    "Spread tub": MappingEntry(
        dataset="TACO",
        original_label="Spread tub",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Polypropylene margarine/butter tub; recyclable dry plastic.",
    ),
    "Tupperware": MappingEntry(
        dataset="TACO",
        original_label="Tupperware",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Rigid plastic storage container; dry plastic.",
    ),
    "Disposable food container": MappingEntry(
        dataset="TACO",
        original_label="Disposable food container",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single-use clear or white plastic takeaway container; dry packaging.",
    ),
    "Foam food container": MappingEntry(
        dataset="TACO",
        original_label="Foam food container",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Expanded polystyrene clamshell food container; dry non-biodegradable packaging.",
    ),
    "Other plastic container": MappingEntry(
        dataset="TACO",
        original_label="Other plastic container",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Rigid plastic tub or canister; dry plastic stream.",
    ),
    "Plastic glooves": MappingEntry(
        dataset="TACO",
        original_label="Plastic glooves",
        canonical_class=CanonicalClass.SANITARY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Disposable plastic protective gloves used for personal hygiene / sanitary cleaning.",
    ),
    "Plastic utensils": MappingEntry(
        dataset="TACO",
        original_label="Plastic utensils",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Disposable plastic forks, spoons, knives; dry plastic stream.",
    ),
    "Pop tab": MappingEntry(
        dataset="TACO",
        original_label="Pop tab",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Aluminium beverage can pull ring; recyclable dry metal.",
    ),
    "Rope & strings": MappingEntry(
        dataset="TACO",
        original_label="Rope & strings",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Ambiguous cords, twines, fibers; materials vary from natural jute to synthetic nylon, creates high ambiguity with wire/cables or textiles.",
    ),
    "Scrap metal": MappingEntry(
        dataset="TACO",
        original_label="Scrap metal",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Miscellaneous metal pieces; recyclable dry metal.",
    ),
    "Shoe": MappingEntry(
        dataset="TACO",
        original_label="Shoe",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Footwear is out of scope for standard household 4-stream daily waste sorting; induces false positives when user footwear is visible in camera frames.",
    ),
    "Squeezable tube": MappingEntry(
        dataset="TACO",
        original_label="Squeezable tube",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Plastic/laminate toothpaste or cosmetic squeeze tube; dry plastic stream.",
    ),
    "Plastic straw": MappingEntry(
        dataset="TACO",
        original_label="Plastic straw",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single-use polypropylene drinking straw; dry plastic.",
    ),
    "Paper straw": MappingEntry(
        dataset="TACO",
        original_label="Paper straw",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Single-use paper drinking straw; dry paper stream.",
    ),
    "Styrofoam piece": MappingEntry(
        dataset="TACO",
        original_label="Styrofoam piece",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
        reason="Expanded polystyrene packaging fragment; dry non-biodegradable waste.",
    ),
    "Unlabeled litter": MappingEntry(
        dataset="TACO",
        original_label="Unlabeled litter",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.ZERO.value,
        reason="Explicitly unannotated litter fragments lacking ground-truth category definition.",
    ),
    "Cigarette": MappingEntry(
        dataset="TACO",
        original_label="Cigarette",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.LOW.value,
        reason="Cigarette butts contain toxic nicotine, heavy metals, and non-biodegradable cellulose acetate filters. Classified variably across jurisdictions as domestic hazardous, street litter, or non-recyclable; excluded to prevent conflicting label signals.",
    ),
}

# 5. Waste_Classification_Dataset
WASTE_CLASSIFICATION_DATASET_MAP: Dict[str, MappingEntry] = {
    "O": MappingEntry(
        dataset="Waste_Classification_Dataset",
        original_label="O",
        canonical_class=CanonicalClass.WET.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Organic kitchen waste, food remains, fruit peels, vegetables, leaves; canonical Wet waste.",
    ),
    "R": MappingEntry(
        dataset="Waste_Classification_Dataset",
        original_label="R",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Recyclable dry materials (plastic containers, metal cans, paper, glass, cardboard); canonical Dry waste.",
    ),
    "Organic": MappingEntry(
        dataset="Waste_Classification_Dataset",
        original_label="Organic",
        canonical_class=CanonicalClass.WET.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Organic kitchen waste (alias for 'O').",
    ),
    "Recyclable": MappingEntry(
        dataset="Waste_Classification_Dataset",
        original_label="Recyclable",
        canonical_class=CanonicalClass.DRY.value,
        status=MappingStatus.INCLUDED.value,
        confidence=ConfidenceLevel.HIGH.value,
        reason="Recyclable packaging (alias for 'R').",
    ),
}

# 6. india_waste_metrics (Tabular - Non-Vision)
INDIA_WASTE_METRICS_MAP: Dict[str, MappingEntry] = {
    "__all__": MappingEntry(
        dataset="india_waste_metrics",
        original_label="__all__",
        canonical_class=None,
        status=MappingStatus.EXCLUDED.value,
        confidence=ConfidenceLevel.ZERO.value,
        reason="india_waste_metrics is a tabular municipal statistics dataset with zero images; cannot be mapped into a computer vision classification pipeline.",
    )
}

# Master registry mapping dataset names to their mapping dictionaries
ALL_DATASET_REGISTRY: Dict[str, Dict[str, MappingEntry]] = {
    "Garbage_Classification": GARBAGE_CLASSIFICATION_MAP,
    "Garbage_Dataset_(GD)": GARBAGE_DATASET_GD_MAP,
    "Medical_Waste_Dataset": MEDICAL_WASTE_DATASET_MAP,
    "TACO": TACO_MAP,
    "Waste_Classification_Dataset": WASTE_CLASSIFICATION_DATASET_MAP,
    "india_waste_metrics": INDIA_WASTE_METRICS_MAP,
}


# =============================================================================
# NORMALIZATION & LOOKUP HELPERS
# =============================================================================

def _normalize_dataset_name(dataset_name: str) -> str:
    """Normalize user or loader dataset names to registry keys."""
    raw = dataset_name.strip().lower()
    for reg_key in ALL_DATASET_REGISTRY:
        if reg_key.lower() == raw:
            return reg_key
    # fuzzy matching for common aliases
    if "garbage_classification" in raw:
        return "Garbage_Classification"
    if "garbage_dataset" in raw or raw == "gd":
        return "Garbage_Dataset_(GD)"
    if "medical" in raw:
        return "Medical_Waste_Dataset"
    if "taco" in raw:
        return "TACO"
    if "waste_classification" in raw or raw == "wcd":
        return "Waste_Classification_Dataset"
    if "india" in raw:
        return "india_waste_metrics"
    return dataset_name


def _normalize_label_name(label: Union[str, int]) -> str:
    """Normalize label query to match registry string keys."""
    return str(label).strip()


def get_mapping_entry(dataset_name: str, original_label: Union[str, int]) -> Optional[MappingEntry]:
    """
    Retrieve the full MappingEntry metadata for a given dataset and label.

    Handles variations such as underscores vs spaces (e.g. 'glove_pair_latex'
    vs 'glove pair latex').
    """
    norm_ds = _normalize_dataset_name(dataset_name)
    if norm_ds not in ALL_DATASET_REGISTRY:
        return None

    dataset_map = ALL_DATASET_REGISTRY[norm_ds]
    norm_lbl = _normalize_label_name(original_label)

    # Direct match
    if norm_lbl in dataset_map:
        return dataset_map[norm_lbl]

    # Try space <-> underscore variants
    alt_space = norm_lbl.replace("_", " ")
    if alt_space in dataset_map:
        return dataset_map[alt_space]

    alt_underscore = norm_lbl.replace(" ", "_")
    if alt_underscore in dataset_map:
        return dataset_map[alt_underscore]

    # Try case-insensitive matching
    for key, entry in dataset_map.items():
        if key.lower() == norm_lbl.lower() or key.lower() == alt_space.lower() or key.lower() == alt_underscore.lower():
            return entry

    return None


def map_label(dataset_name: str, original_label: Union[str, int]) -> Optional[str]:
    """
    Map an original dataset label to its canonical 4-class target:
    'Wet', 'Dry', 'Sanitary', 'Special Care'.

    Returns:
        Canonical class string ('Wet', 'Dry', 'Sanitary', 'Special Care')
        or None if the label is EXCLUDED or unmapped.
    """
    entry = get_mapping_entry(dataset_name, original_label)
    if entry is None or entry.status == MappingStatus.EXCLUDED.value:
        return None
    return entry.canonical_class


def map_label_or_raise(dataset_name: str, original_label: Union[str, int]) -> str:
    """
    Map label or raise ValueError if excluded, ambiguous, or not found.
    """
    entry = get_mapping_entry(dataset_name, original_label)
    if entry is None:
        raise ValueError(f"Label '{original_label}' not recognized in dataset '{dataset_name}'.")
    if entry.status == MappingStatus.EXCLUDED.value:
        raise ValueError(
            f"Label '{original_label}' in dataset '{dataset_name}' is EXCLUDED from training. Reason: {entry.reason}"
        )
    if entry.canonical_class not in CANONICAL_CLASSES:
        raise ValueError(
            f"Mapped class '{entry.canonical_class}' is not one of canonical classes {CANONICAL_CLASSES}."
        )
    return entry.canonical_class


def is_included(dataset_name: str, original_label: Union[str, int]) -> bool:
    """Check whether a label is officially included for training."""
    entry = get_mapping_entry(dataset_name, original_label)
    return entry is not None and entry.status == MappingStatus.INCLUDED.value


def get_included_labels(dataset_name: str) -> List[str]:
    """Get list of all included original labels for a dataset."""
    norm_ds = _normalize_dataset_name(dataset_name)
    if norm_ds not in ALL_DATASET_REGISTRY:
        return []
    return [
        label
        for label, entry in ALL_DATASET_REGISTRY[norm_ds].items()
        if entry.status == MappingStatus.INCLUDED.value
    ]


def get_excluded_labels(dataset_name: str) -> List[str]:
    """Get list of all excluded original labels for a dataset."""
    norm_ds = _normalize_dataset_name(dataset_name)
    if norm_ds not in ALL_DATASET_REGISTRY:
        return []
    return [
        label
        for label, entry in ALL_DATASET_REGISTRY[norm_ds].items()
        if entry.status == MappingStatus.EXCLUDED.value
    ]


def get_class_breakdown() -> Dict[str, Dict[str, List[str]]]:
    """
    Summarize which labels from each dataset contribute to each canonical class.
    """
    summary: Dict[str, Dict[str, List[str]]] = {cls_name: {} for cls_name in CANONICAL_CLASSES}
    summary["EXCLUDED"] = {}

    for ds_name, ds_map in ALL_DATASET_REGISTRY.items():
        for lbl, entry in ds_map.items():
            if entry.status == MappingStatus.INCLUDED.value and entry.canonical_class:
                summary[entry.canonical_class].setdefault(ds_name, []).append(lbl)
            else:
                summary["EXCLUDED"].setdefault(ds_name, []).append(lbl)

    return summary


if __name__ == "__main__":
    print("=" * 60)
    print("NudgeWasteAI — Centralized Class Mapper Validation")
    print("=" * 60)
    for c in CANONICAL_CLASSES:
        print(f"Canonical Class: {c} (Index: {CLASS_TO_IDX[c]})")

    breakdown = get_class_breakdown()
    print("\nMapping Summary:")
    for cls_name, datasets in breakdown.items():
        total_cats = sum(len(lbls) for lbls in datasets.values())
        print(f"\n--- {cls_name.upper()} ({total_cats} source categories) ---")
        for ds, lbls in datasets.items():
            print(f"  {ds} ({len(lbls)}): {', '.join(lbls[:8])}{'...' if len(lbls) > 8 else ''}")
