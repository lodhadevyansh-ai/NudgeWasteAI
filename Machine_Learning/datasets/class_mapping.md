# NudgeWasteAI — Phase 2: Dataset Label Mapping to Four Canonical Classes

**Document Path:** `Machine_Learning/datasets/class_mapping.md`  
**Execution Date:** 2026-10-01  
**Status:** Canonical Four-Class Mapping Defined  
**Centralized Module:** `Machine_Learning/preprocessing/class_mapper.py`

---

## 1. Canonical Four-Class Taxonomy

Under standard municipal solid waste management protocols (including India's Solid Waste Management Rules, 2016 and smart segregation standards), waste generated at households, commercial establishments, and institutions is segregated into distinct, non-overlapping streams.

The four canonical classes for NudgeWasteAI are strictly:

1. **Wet**
   - **Definition:** Biodegradable organic matter, raw and cooked food leftovers, fruit and vegetable peels, tea leaves, coffee grounds, garden/plant waste, fallen leaves, and decomposing food items.
   - **Post-Collection Destination:** Composting, biomethanation, organic fertilizer plants.
   - **Key Visual Identifiers:** Organic textures, produce shapes, biological decay patterns, kitchen scrap forms.

2. **Dry**
   - **Definition:** Non-biodegradable, non-sanitary, non-hazardous recyclable and combustible materials. Includes paper, clean cardboard, plastic containers/bottles/wrappers, aluminium/tin cans, metal caps/foils, glass bottles/jars, and clean dry packaging.
   - **Post-Collection Destination:** Material Recovery Facilities (MRFs), mechanical recycling, refuse-derived fuel (RDF).
   - **Key Visual Identifiers:** Engineered geometry, artificial packaging, barcodes, branded labels, plastic/metal/glass luster, paper/carton fiber.

3. **Sanitary**
   - **Definition:** Single-use personal hygiene and domestic sanitary waste that has been in contact with human body fluids or used as disposable hygiene barriers. Includes used facial tissues/paper napkins, cotton swabs/pads, wound dressings/gauze, used bandages, disposable single-use protective gloves, disposable shoe covers, and sanitary head caps.
   - **Post-Collection Destination:** High-temperature incineration or deep sanitary burial (never commingled with recyclables or compost).
   - **Key Visual Identifiers:** Gauze weave, absorbent cotton, tissue paper folds, non-woven protective polypropylene fabric, single-use sanitary apparel.

4. **Special Care**
   - **Definition:** Domestic hazardous, biomedical, chemical, sharp, or electronic waste that poses immediate toxicological, biological, infection, chemical, or physical hazards to sanitation personnel, public health, or the ecosystem. Includes spent batteries, pressurized aerosols, broken cullet/glass shards, clinical diagnostic test tubes, drainage fluid bags, contaminated surgical procedure gloves, and pharmaceutical blister packaging.
   - **Post-Collection Destination:** Authorized hazardous waste treatment, storage, and disposal facilities (TSDF) or authorized biomedical autoclaving/incineration.
   - **Key Visual Identifiers:** Battery terminals, aerosol nozzles/canisters, jagged sharp glass edges, clinical fluid tubing/ports, medical vial/tube graduations, surgical latex contours.

---

## 2. Complete Traceable Label Mapping Tables

Every category from every inspected dataset has been evaluated. No label has been assigned arbitrarily; categories that do not meet strict criteria are classified as **EXCLUDED / AMBIGUOUS**.

### 2.1 Dataset: Garbage_Classification

| Dataset | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Garbage_Classification` | `cardboard` | **Dry** | **INCLUDE** | HIGH | Clean corrugated cardboard and paperboard packaging; standard recyclable dry stream. |
| `Garbage_Classification` | `glass` | **Dry** | **INCLUDE** | HIGH | Intact glass bottles and jars; standard recyclable dry stream. |
| `Garbage_Classification` | `metal` | **Dry** | **INCLUDE** | HIGH | Aluminium and tin food/drink cans, clean metal; standard recyclable dry stream. |
| `Garbage_Classification` | `paper` | **Dry** | **INCLUDE** | HIGH | Clean office paper, newspapers, printed sheets; standard recyclable dry stream. |
| `Garbage_Classification` | `plastic` | **Dry** | **INCLUDE** | HIGH | Rigid and container plastics, consumer bottles; standard recyclable dry stream. |
| `Garbage_Classification` | `trash` | *None* | **EXCLUDE** | LOW | Heterogeneous unsegregated mixed garbage (packaging fragments, Styrofoam, mixed debris); violates single-stream classification and introduces high label noise. |

---

### 2.2 Dataset: Garbage_Dataset_(GD)

| Dataset | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Garbage_Dataset_(GD)` | `battery` | **Special Care** | **INCLUDE** | HIGH | Domestic hazardous e-waste containing toxic heavy metals (lithium, lead, cadmium, acid); poses severe fire, chemical, and soil contamination hazards. |
| `Garbage_Dataset_(GD)` | `biological` | **Wet** | **INCLUDE** | HIGH | Biodegradable organic matter, food remains, kitchen vegetable/fruit waste; canonical wet waste stream. |
| `Garbage_Dataset_(GD)` | `cardboard` | **Dry** | **INCLUDE** | HIGH | Cardboard boxes and corrugated shipping cartons; standard recyclable dry stream. |
| `Garbage_Dataset_(GD)` | `clothes` | *None* | **EXCLUDE** | LOW | Textiles and wearable apparel are handled through donation or specialized textile recovery, not standard municipal daily bins. Training on clothes introduces severe false-positive risks on user clothing during real-time camera scanning. |
| `Garbage_Dataset_(GD)` | `glass` | **Dry** | **INCLUDE** | HIGH | Recyclable glass bottles, jars, and containers; standard recyclable dry stream. |
| `Garbage_Dataset_(GD)` | `metal` | **Dry** | **INCLUDE** | HIGH | Food/beverage cans, aluminium tins, scrap metal pieces; standard recyclable dry stream. |
| `Garbage_Dataset_(GD)` | `paper` | **Dry** | **INCLUDE** | HIGH | Clean paper, documents, newsprint; standard recyclable dry stream. |
| `Garbage_Dataset_(GD)` | `plastic` | **Dry** | **INCLUDE** | HIGH | Plastic beverage bottles, detergent jugs, consumer plastic packaging; standard recyclable dry stream. |
| `Garbage_Dataset_(GD)` | `shoes` | *None* | **EXCLUDE** | LOW | Footwear is out of scope for standard household 4-stream daily waste sorting; induces false positives when user footwear is visible in camera frames. |
| `Garbage_Dataset_(GD)` | `trash` | *None* | **EXCLUDE** | LOW | Heterogeneous catch-all garbage category without consistent physical or material attributes; excluded to prevent label noise. |

---

### 2.3 Dataset: Medical_Waste_Dataset

| Dataset | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Medical_Waste_Dataset` | `gauze` | **Sanitary** | **INCLUDE** | HIGH | Wound dressings, absorbent cotton gauze pads; under solid waste management rules (e.g. SWM Rules 2016), soiled cotton, dressings, and bandages are explicitly classified as Sanitary Waste. |
| `Medical_Waste_Dataset` | `glove_pair_latex` | **Special Care** | **INCLUDE** | HIGH | Clinical latex examination gloves; contaminated biomedical personal protective equipment with potential biohazard contact. |
| `Medical_Waste_Dataset` | `glove_pair_nitrile` | **Special Care** | **INCLUDE** | HIGH | Clinical nitrile examination gloves; contaminated protective equipment subject to biohazard precautions. |
| `Medical_Waste_Dataset` | `glove_pair_surgery` | **Special Care** | **INCLUDE** | HIGH | Surgical procedure gloves; direct clinical exposure to blood and biological fluids; strictly biomedical Special Care waste. |
| `Medical_Waste_Dataset` | `glove_single_latex` | **Special Care** | **INCLUDE** | HIGH | Single clinical latex examination glove; contaminated biomedical barrier. |
| `Medical_Waste_Dataset` | `glove_single_nitrile` | **Special Care** | **INCLUDE** | HIGH | Single clinical nitrile examination glove; contaminated biomedical barrier. |
| `Medical_Waste_Dataset` | `glove_single_surgery` | **Special Care** | **INCLUDE** | HIGH | Single surgical procedure glove; clinical biohazard item. |
| `Medical_Waste_Dataset` | `medical_cap` | **Sanitary** | **INCLUDE** | MEDIUM | Disposable non-woven head cover/hairnet used as a personal hygiene sanitary barrier. |
| `Medical_Waste_Dataset` | `medical_glasses` | *None* | **EXCLUDE** | LOW | Durable, washable plastic protective eye goggles; primarily reusable safety apparatus rather than single-use disposable waste. |
| `Medical_Waste_Dataset` | `shoe_cover_pair` | **Sanitary** | **INCLUDE** | MEDIUM | Disposable non-woven polypropylene shoe covers; single-use personal sanitary barrier apparel. |
| `Medical_Waste_Dataset` | `shoe_cover_single` | **Sanitary** | **INCLUDE** | MEDIUM | Single disposable non-woven shoe cover; single-use personal sanitary barrier apparel. |
| `Medical_Waste_Dataset` | `test_tube` | **Special Care** | **INCLUDE** | HIGH | Clinical and laboratory specimen tubes containing or exposed to biological samples, blood, or reagents; high-risk biohazard Special Care. |
| `Medical_Waste_Dataset` | `urine_bag` | **Special Care** | **INCLUDE** | HIGH | Clinical drainage collection bag holding human physiological fluids; biohazard medical Special Care waste. |

---

### 2.4 Dataset: TACO (Trash Annotations in Context — 60 Categories)

| ID | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | `Aluminium foil` | **Dry** | **INCLUDE** | HIGH | Clean aluminium food foil; recyclable dry metal. |
| 1 | `Battery` | **Special Care** | **INCLUDE** | HIGH | Household batteries contain acid, lithium, and toxic heavy metals; domestic hazardous Special Care waste. |
| 2 | `Aluminium blister pack` | **Special Care** | **INCLUDE** | MEDIUM | Pharmaceutical medicine packaging; associated with pharmaceutical residues and domestic medical waste. |
| 3 | `Carded blister pack` | **Special Care** | **INCLUDE** | MEDIUM | Pharmaceutical packaging for pills/capsules; pharmaceutical Special Care stream. |
| 4 | `Other plastic bottle` | **Dry** | **INCLUDE** | HIGH | Recyclable plastic container bottles. |
| 5 | `Clear plastic bottle` | **Dry** | **INCLUDE** | HIGH | Clear PET beverage bottle; canonical recyclable dry waste. |
| 6 | `Glass bottle` | **Dry** | **INCLUDE** | HIGH | Recyclable glass beverage bottle. |
| 7 | `Plastic bottle cap` | **Dry** | **INCLUDE** | HIGH | Polypropylene/HDPE plastic bottle closures; recyclable dry plastic. |
| 8 | `Metal bottle cap` | **Dry** | **INCLUDE** | HIGH | Crown cork or aluminium bottle cap; recyclable dry metal. |
| 9 | `Broken glass` | **Special Care** | **INCLUDE** | HIGH | Sharp cullet and glass shards present severe physical puncture/injury risks to sanitation handlers; requires special handling. |
| 10 | `Food Can` | **Dry** | **INCLUDE** | HIGH | Steel/tin canned food container; recyclable dry metal. |
| 11 | `Aerosol` | **Special Care** | **INCLUDE** | HIGH | Pressurized aerosol canister with flammable propellants and chemical residue; explosion and toxicity hazard requiring Special Care. |
| 12 | `Drink can` | **Dry** | **INCLUDE** | HIGH | Aluminium beverage can; high-value recyclable dry stream. |
| 13 | `Toilet tube` | **Dry** | **INCLUDE** | HIGH | Clean cardboard roll core; recyclable paperboard dry stream. |
| 14 | `Other carton` | **Dry** | **INCLUDE** | HIGH | Paperboard packaging; recyclable dry stream. |
| 15 | `Egg carton` | **Dry** | **INCLUDE** | HIGH | Molded pulp or clear plastic egg carton; dry recyclable. |
| 16 | `Drink carton` | **Dry** | **INCLUDE** | HIGH | Aseptic beverage carton (Tetra Pak); recyclable dry stream. |
| 17 | `Corrugated carton` | **Dry** | **INCLUDE** | HIGH | Corrugated shipping cardboard box; canonical recyclable dry waste. |
| 18 | `Meal carton` | **Dry** | **INCLUDE** | HIGH | Paperboard takeout meal box; dry packaging stream. |
| 19 | `Pizza box` | **Dry** | **INCLUDE** | MEDIUM | Corrugated pizza box packaging; standard packaging dry stream. |
| 20 | `Paper cup` | **Dry** | **INCLUDE** | HIGH | Single-use paper beverage cup; dry stream. |
| 21 | `Disposable plastic cup` | **Dry** | **INCLUDE** | HIGH | Single-use plastic drink cup; recyclable dry stream. |
| 22 | `Foam cup` | **Dry** | **INCLUDE** | MEDIUM | Expanded polystyrene foam beverage cup; non-biodegradable dry waste. |
| 23 | `Glass cup` | **Dry** | **INCLUDE** | HIGH | Glass drinking tumbler; recyclable glass dry stream. |
| 24 | `Other plastic cup` | **Dry** | **INCLUDE** | HIGH | Rigid plastic cup; recyclable dry stream. |
| 25 | `Food waste` | **Wet** | **INCLUDE** | HIGH | Biodegradable food scraps, fruit remnants, kitchen organic waste; canonical Wet waste. |
| 26 | `Glass jar` | **Dry** | **INCLUDE** | HIGH | Food/jam glass container jar; recyclable dry glass. |
| 27 | `Plastic lid` | **Dry** | **INCLUDE** | HIGH | Plastic cup or container lid; dry plastic. |
| 28 | `Metal lid` | **Dry** | **INCLUDE** | HIGH | Metal jar/can lid; recyclable dry metal. |
| 29 | `Other plastic` | **Dry** | **INCLUDE** | HIGH | Miscellaneous plastic consumer items; dry plastic stream. |
| 30 | `Magazine paper` | **Dry** | **INCLUDE** | HIGH | Glossy periodical and magazine paper; recyclable dry paper. |
| 31 | `Tissues` | **Sanitary** | **INCLUDE** | HIGH | Facial tissues, handkerchiefs, napkins containing bodily secretions or personal hygiene residues; canonical Sanitary waste. |
| 32 | `Wrapping paper` | **Dry** | **INCLUDE** | HIGH | Decorative paper wrap; recyclable dry paper. |
| 33 | `Normal paper` | **Dry** | **INCLUDE** | HIGH | Standard printer and notebook paper sheets; recyclable dry paper. |
| 34 | `Paper bag` | **Dry** | **INCLUDE** | HIGH | Kraft paper grocery shopping bag; recyclable dry paper. |
| 35 | `Plastified paper bag` | **Dry** | **INCLUDE** | HIGH | Polymer-laminated paper carrier bag; dry packaging stream. |
| 36 | `Plastic film` | **Dry** | **INCLUDE** | HIGH | Thin plastic cling film and shrink wrap; dry plastic stream. |
| 37 | `Six pack rings` | **Dry** | **INCLUDE** | HIGH | LDPE beverage can collar rings; recyclable dry plastic. |
| 38 | `Garbage bag` | **Dry** | **INCLUDE** | MEDIUM | Polyethylene bin liner film; dry plastic waste. |
| 39 | `Other plastic wrapper` | **Dry** | **INCLUDE** | HIGH | Plastic outer packaging film and confectionery wrappers; dry plastic. |
| 40 | `Single-use carrier bag` | **Dry** | **INCLUDE** | HIGH | HDPE/LDPE grocery carry bag; dry plastic. |
| 41 | `Polypropylene bag` | **Dry** | **INCLUDE** | HIGH | Woven/non-woven polypropylene shopping bag; dry plastic/textile stream. |
| 42 | `Crisp packet` | **Dry** | **INCLUDE** | HIGH | Metallized plastic film snack bag; dry non-biodegradable packaging. |
| 43 | `Spread tub` | **Dry** | **INCLUDE** | HIGH | Polypropylene margarine/butter tub; recyclable dry plastic. |
| 44 | `Tupperware` | **Dry** | **INCLUDE** | HIGH | Rigid plastic storage container; dry plastic. |
| 45 | `Disposable food container` | **Dry** | **INCLUDE** | HIGH | Single-use clear or white plastic takeaway container; dry packaging. |
| 46 | `Foam food container` | **Dry** | **INCLUDE** | MEDIUM | Expanded polystyrene clamshell food container; dry non-biodegradable packaging. |
| 47 | `Other plastic container` | **Dry** | **INCLUDE** | HIGH | Rigid plastic tub or canister; dry plastic stream. |
| 48 | `Plastic glooves` | **Sanitary** | **INCLUDE** | MEDIUM | Disposable plastic protective gloves used for personal hygiene / sanitary cleaning. |
| 49 | `Plastic utensils` | **Dry** | **INCLUDE** | HIGH | Disposable plastic forks, spoons, knives; dry plastic stream. |
| 50 | `Pop tab` | **Dry** | **INCLUDE** | HIGH | Aluminium beverage can pull ring; recyclable dry metal. |
| 51 | `Rope & strings` | *None* | **EXCLUDE** | LOW | Ambiguous cords, twines, fibers; materials vary from natural jute to synthetic nylon, creates high ambiguity with wire/cables or textiles. |
| 52 | `Scrap metal` | **Dry** | **INCLUDE** | HIGH | Miscellaneous metal pieces; recyclable dry metal. |
| 53 | `Shoe` | *None* | **EXCLUDE** | LOW | Footwear is out of scope for standard household 4-stream daily waste sorting; induces false positives when user footwear is visible in camera frames. |
| 54 | `Squeezable tube` | **Dry** | **INCLUDE** | HIGH | Plastic/laminate toothpaste or cosmetic squeeze tube; dry plastic stream. |
| 55 | `Plastic straw` | **Dry** | **INCLUDE** | HIGH | Single-use polypropylene drinking straw; dry plastic. |
| 56 | `Paper straw` | **Dry** | **INCLUDE** | HIGH | Single-use paper drinking straw; dry paper stream. |
| 57 | `Styrofoam piece` | **Dry** | **INCLUDE** | MEDIUM | Expanded polystyrene packaging fragment; dry non-biodegradable waste. |
| 58 | `Unlabeled litter` | *None* | **EXCLUDE** | ZERO | Explicitly unannotated litter fragments lacking ground-truth category definition. |
| 59 | `Cigarette` | *None* | **EXCLUDE** | LOW | Cigarette butts contain toxic nicotine, heavy metals, and non-biodegradable cellulose acetate filters. Classified variably across jurisdictions as domestic hazardous, street litter, or non-recyclable; excluded to prevent conflicting label signals. |

---

### 2.5 Dataset: Waste_Classification_Dataset

| Dataset | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Waste_Classification_Dataset` | `O` | **Wet** | **INCLUDE** | HIGH | Organic kitchen waste, food remains, fruit peels, vegetables, leaves; canonical Wet waste. |
| `Waste_Classification_Dataset` | `R` | **Dry** | **INCLUDE** | HIGH | Recyclable dry materials (plastic containers, metal cans, paper, glass, cardboard); canonical Dry waste. |

---

### 2.6 Dataset: india_waste_metrics

| Dataset | Original Label | Canonical Class | Include / Exclude | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `india_waste_metrics` | `__all__` | *None* | **EXCLUDE** | ZERO | Tabular dataset with municipal records and statistics; contains **zero images**. Excluded from computer vision image classification pipeline. |

---

## 3. Detailed Handling Rationale for Sensitive Categories

### 3.1 Medical Waste Categories: Sanitary vs. Special Care vs. Excluded
- **Special Care Assignment (`test_tube`, `urine_bag`, `glove_*_surgery`, `glove_*_latex`, `glove_*_nitrile`):**
  - Clinical diagnostic items and bodily fluid collectors (`test_tube`, `urine_bag`) represent direct biohazards. They can carry pathogens, chemical reagents, or blood-borne contaminants. They cannot be disposed of in standard domestic bins or handled without strict PPE.
  - Surgical and clinical examination gloves from medical settings carry infection risk and are treated under biohazard/biomedical waste protocols.
- **Sanitary Assignment (`gauze`, `medical_cap`, `shoe_cover_*`):**
  - In municipal solid waste guidelines, absorbent wound dressings, gauze pads, and personal hygiene apparel are managed under **Sanitary Waste** (instructed to be wrapped securely before collection).
  - Disposable shoe covers and hairnets represent non-invasive personal hygiene barrier materials.
- **Excluded (`medical_glasses`):**
  - Protective eye goggles are durable, rigid polycarbonate safety wear designed for multiple reuses and washings, not single-use disposable waste.

### 3.2 TACO Categories: Segmentation to Classification Nuances
- **Bounding-box Cropping Requirement:** TACO images are multi-object natural scenes. A single image typically contains multiple litter items. When utilized in subsequent phases, individual bounding boxes must be cropped to train a single-label image classifier.
- **Hazardous Litter to Special Care:** `Battery`, `Aerosol`, `Broken glass`, and `Aluminium/Carded blister pack` are mapped to **Special Care** due to toxicity, flammability, puncture risk, and residual medication hazards.
- **Excluded Litter Items:**
  - `Unlabeled litter`: Has no ground-truth label (0 confidence).
  - `Cigarette`: Small, ambiguous, and classified inconsistently across regions (hazardous vs non-recyclable dry vs litter).
  - `Rope & strings`: High risk of confusing textiles, cables, or wiring.
  - `Shoe`: Out-of-scope wearable footwear.

### 3.3 Non-Waste and Ambiguous Items: Clothes, Shoes, and "Trash"
- **`clothes` & `shoes`:**
  - In consumer mobile apps, classifying wearable items (t-shirts, jeans, sneakers) as "Dry Waste" causes frequent false-positive triggers when cameras view people or floors. Furthermore, wearable textiles belong in reuse/donation channels or dedicated textile drop-offs.
  - Decision: Strictly **EXCLUDED** from the 4-class waste classifier.
- **`trash` in Garbage_Classification and Garbage_Dataset_(GD):**
  - The label "trash" is intrinsically heterogeneous: it combines broken plastic, soiled paper, Styrofoam pieces, foil wrappers, and household sweepings into one unsegregated pool.
  - Training on "trash" teaches a convolutional neural network conflicting feature representations, polluting clean dry/wet class boundaries.
  - Decision: Strictly **EXCLUDED**.

---

## 4. Class Distribution & Training Source Summary

| Canonical Class | Contributing Datasets | Total Contributing Source Labels | Estimated Raw Image Volume Available |
| :--- | :--- | :--- | :--- |
| **Wet** | `Waste_Classification_Dataset` (`O`), `Garbage_Dataset_(GD)` (`biological`), `TACO` (`Food waste`) | 3 unique labels | **~14,665+ images** |
| **Dry** | `Waste_Classification_Dataset` (`R`), `Garbage_Classification` (5 classes), `Garbage_Dataset_(GD)` (5 classes), `TACO` (48 classes) | 59 unique labels | **~20,500+ images** |
| **Sanitary** | `Medical_Waste_Dataset` (`gauze`, `medical_cap`, `shoe_cover_*`), `TACO` (`Tissues`, `Plastic glooves`) | 6 unique labels | **~550+ images/crops** |
| **Special Care** | `Garbage_Dataset_(GD)` (`battery`), `Medical_Waste_Dataset` (`test_tube`, `urine_bag`, 6 glove variants), `TACO` (`Battery`, `Aerosol`, `Broken glass`, blister packs) | 14 unique labels | **~1,750+ images/crops** |
| **EXCLUDED** | `Garbage_Classification` (`trash`), `Garbage_Dataset_(GD)` (`clothes`, `shoes`, `trash`), `Medical_Waste_Dataset` (`medical_glasses`), `TACO` (4 classes), `india_waste_metrics` (tabular) | 10 source labels | *Excluded from training set* |

---

## 5. Traceability Pipeline Verification

The canonical mapping is fully centralized in [`Machine_Learning/preprocessing/class_mapper.py`](file:///c:/Users/lodha/Downloads/NudgeWasteAI/Machine_Learning/preprocessing/class_mapper.py):
- `map_label(dataset_name, original_label) -> Optional[str]`
- `map_label_or_raise(dataset_name, original_label) -> str`
- `get_mapping_entry(dataset_name, original_label) -> MappingEntry`
- `is_included(dataset_name, original_label) -> bool`
- `CANONICAL_CLASSES = ["Wet", "Dry", "Sanitary", "Special Care"]`

All downstream data loaders in Phase 3 will ingest mappings strictly through this centralized module, guaranteeing complete reproducibility and zero scattered hardcoded string transformations.

---

**FINAL STATUS:**  
**CLASS MAPPING COMPLETE**
