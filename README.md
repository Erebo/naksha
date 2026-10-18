# Naksha (নকশা)

**Inter-Agency Land Data Interoperability & Canonical Spatial Engine**  
*One parcel. One identity. Every land office looking at the same truth.*

Developed for the **LandTech 2026 Innovation Hackathon**.

---

## 📌 Problem Statement

In Bangladesh, a single land parcel is recorded across at least six distinct public and financial bodies, each operating in isolation under its own key:

| Agency | Record Identifier | Common Operational Blindspot |
| :--- | :--- | :--- |
| **Sub-Registry** | Deed Number | Registers deeds without real-time AC Land mutation check, opening double-sale risks. |
| **AC Land** | e-Mutation Case ID | Approves mutations without ground-truth DLRS geometry or deed chain verification. |
| **Union Land Office** | Holding No. / LD Tax | Accepts land taxes from non-owners, creating adverse possession claims. |
| **DLRS** | Sheet / Dag (CS, SA, RS, BS) | Surveyed polygons exist in isolation from registered deed claims. |
| **DC Office** | Acquisition Case No. | Pays compensation to outdated owners; acquisition locks are invisible to Sub-Registries. |
| **Banks** | Mortgage Reference | Mortgages are recorded in siloed bank ledgers, allowing duplicate liens on the same plot. |

Because these keys never meet at the moment of an official action, fraud and disputes thrive in the administrative gaps.

---

## 💡 The Solution: A Federated Overlay

**NAKSHA** is a Government-to-Government (G2G) interoperability engine. It does **not** replace existing ministry software or build another monolithic portal. Instead, it:
1. Resolves disparate agency keys into a single **Canonical Parcel UUID (UUIDv7)** across all four survey eras (**CS, SA, RS, BS**).
2. Runs **5 deterministic statutory integrity rules** and **PostGIS spatial checks** whenever a plot is touched.
3. Delivers actionable findings (**CLEAR**, **REVIEW**, or **BLOCK**) directly inside legacy portals via a zero-integration **Chrome Extension Side Panel**.
4. Seals every query and verdict in a tamper-evident, append-only **Trust Ledger** (Ed25519-signed SHA-256 hash-chain).

---

## 🚀 Stage 2: Canonical Land Data Model & Backend Baseline

Stage 2 establishes the normalized core data architecture and verification services:
* **Canonical Schema (`naksha.models.canonical`)**: Pydantic v2 schemas for `LandRecord`, `SourceReference`, `ExtractedField`, `RecordMatch`, `Discrepancy`, and `VerificationResult`.
* **Field Provenance**: `ExtractedField[T]` preserves the verbatim `raw_value`, normalized comparison value `normalized_value`, extraction `confidence` (0.0–1.0), and `source_citation`.
* **Normalization Engine (`naksha.normalization`)**:
  * Unicode NFC normalization, zero-width character stripping, and whitespace standardisation.
  * Bidirectional Bengali (০–৯) and ASCII (0–9) numeral conversion.
  * Dag, Khatian, and Holding identifier normalization with sub-plot preservation (`402/ka`).
  * Statutory land area conversions across Decimals (শতক), Acres (একর), Bighas (বিঘা), Kathas (কাঠা), Chhataks (ছটাক), Square Feet, and Square Meters.
  * Cross-lingual phonetic name similarity scoring across Bangla script and English transliterations with honorific stripping (`মোঃ`, `Md.`).
* **Repository Layer (`naksha.repository`)**: Abstract `BaseRecordRepository` and `InMemoryRecordRepository` enabling database decoupling.
* **Verification Engine (`naksha.services.verification`)**: Cross-references records to detect Dag conflicts, Khatian divergences, area deficits (>0.2 dec statutory tolerance), land-class inconsistencies, duplicate concurrent transfers, and unverified incomplete records.
* **REST API (`naksha.api`)**: FastAPI backend with OpenAPI documentation, query filtering, and demo reconciliation endpoints.

---

## 🧪 Synthetic Demonstration Federation

> [!IMPORTANT]
> **Data Privacy Guarantee:** In strict adherence to data privacy standards and hackathon requirements, NAKSHA uses **NO REAL CITIZEN NAMES, REAL NIDS, PHONE NUMBERS, OR ACTUAL PRIVATE LAND RECORDS**.
> Every record is generated deterministically by `naksha.data.synthetic` and marked with `is_synthetic: true` and a prominent audit disclaimer.

The Stage 2 benchmark cohort includes:
1. **Matching Pair (`SYN-MATCH-01` & `SYN-MATCH-02`)**: Sub-Registry sale deed and AC Land e-mutation agreeing on Mouza Kashimpur, Dag 402, Khatian 120, 6.00 decimals, and owner Md. Abdul Karim (`CLEAR`).
2. **Conflicting Identifiers (`SYN-CONFLICT-ID-01`)**: LD Tax dakhila receipt asserting Dag 403 and Khatian 125 with land-class conflict (`BLOCK`).
3. **Conflicting Area (`SYN-CONFLICT-AREA-01`)**: DLRS ground-truth cadastral survey of 5.10 decimals vs. 6.00 decimals deed claim (0.90 dec deficit exceeding ±0.20 dec statutory limit) (`BLOCK`).
4. **Duplicate Transfer Hazard (`SYN-DUPLICATE-01`)**: Second registered deed entered for the same plot within 14 days to another buyer (`BLOCK`).
5. **Incomplete Historical Fragment (`SYN-INCOMPLETE-01`)**: Damaged historical CS record missing plot and khatian identifiers with low extraction confidence (`REVIEW`).

---

## 🛠️ Setup & Installation

### Prerequisites
* Python 3.11+
* Git

### 1. Clone & Setup Environment
```bash
# Clone the repository (if not already local)
git clone https://github.com/Erebo/naksha.git
cd naksha

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Test Suite
Execute the comprehensive test suite (50 unit & integration tests covering data models, normalization, spatial engine, frontend contract, and APIs):
```bash
pytest -v
```

### 4. Start Backend & Access Interfaces
Launch the FastAPI development server:
```bash
uvicorn naksha.api.app:app --reload --host 127.0.0.1 --port 8000
```
Interactive visual interface and documentation links:
* **Bangla-First 2D GIS Interactive Map**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) or [http://127.0.0.1:8000/map](http://127.0.0.1:8000/map)
* **Mock ভূমি উন্নয়ন কর পোর্টাল (LD Tax Portal)**: [http://127.0.0.1:8000/portals/ld-tax](http://127.0.0.1:8000/portals/ld-tax)
* **Mock ই-নামজারি ও মিউটেশন পোর্টাল (e-Mutation Portal)**: [http://127.0.0.1:8000/portals/e-mutation](http://127.0.0.1:8000/portals/e-mutation)
* **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧩 Stage 5: Chrome Extension Side Panel & Mock Portals

Stage 5 delivers the zero-integration side panel experience for land officers:
* **Bangla-First Mock Land Portals (`naksha/static/portals/`)**:
  * Realistic, purely synthetic mock interfaces representing the Union Land Office LD Tax portal (`/portals/ld-tax`) and AC Land e-Mutation portal (`/portals/e-mutation`).
  * Structured context containers exposing synthetic Mouza, Dag, Khatian, holding, and owner attributes.
  * Interactive plot switcher allowing officers to test Dag 402 (target plot), Dag 401 (west neighbor), and Dag 403 (south neighbor with tax arrears).
  * 100% synthetic demonstration data; zero connection to live government servers.
* **Chrome Extension Manifest V3 (`extension/`)**:
  * **Service Worker (`background.js`)**: Manages `chrome.sidePanel` lifecycle, state storage (`chrome.storage.local`), and cross-context routing.
  * **Content Script (`content.js` & `content.css`)**: Injected into the local mock portal domains (`http://127.0.0.1:8000/portals/*`). Detects plot identifiers from the active page, listens to dynamic plot switching, and renders a floating Bangla NAKSHA launcher badge.
  * **Interactive GIS Side Panel (`sidepanel.html`, `sidepanel.css`, `sidepanel.js`)**: Custom-tailored for the Chrome Side Panel drawer width (~380px). Renders the full Leaflet 2D GIS map with toggleable multi-era layers (CS 88 ancestral footprint, Deed claim, DLRS survey, Khas canal conflict zone), neighbor tax statuses, and discrepancy explainers.

### 🔌 Hackathon Step-by-Step Demonstration Walkthrough

Follow this exact script for a 100% reproducible live presentation:

#### Step 1: Start the Backend Server
```bash
# In project root with active venv:
uvicorn naksha.api.app:app --reload --host 127.0.0.1 --port 8000
```
Verify readiness at `http://127.0.0.1:8000/health` (`"status": "ok"`).

#### Step 2: Install Unpacked Chrome Extension
1. Open Google Chrome and visit `chrome://extensions/`.
2. Toggle **Developer mode** to ON in the upper-right corner.
3. Click **Load unpacked** (top-left) and select `c:\Users\user\Desktop\P\naksha\extension`.
4. The **নকশা (NAKSHA)** icon will appear in your Chrome toolbar.

#### Step 3: Open the Synthetic LD Tax Portal & Launch NAKSHA
1. Navigate to: [http://127.0.0.1:8000/portals/ld-tax](http://127.0.0.1:8000/portals/ld-tax).
2. The page loads with Bangladeshi Bangla typography (`Hind Siliguri`) displaying holding `H-402`.
3. Notice the floating **নকশা** launcher pill at the bottom-right showing `প্লট শনাক্ত: দাগ ৪০২`.
4. Click the NAKSHA icon in the toolbar or click **Side Panel** in Chrome to open the side panel.

#### Step 4: Inspect Plot Scenarios

| Action on Mock Portal | Expected Detection | Side Panel GIS & Findings | Statutory Decision |
| :--- | :--- | :--- | :--- |
| **Select দাগ ৪০২** *(Default)* | মৌজা কাশিমপুর, দাগ ৪০২, খতিয়ান ১২০ | Renders 4 layers (purple CS 88, blue deed claim, green DLRS survey, red conflict zone). Highlights **০.৯০ শতক** canal encroachment into public Khas land. | **ব্লক (BLOCK)** — নামজারি স্থগিত |
| **Click দাগ ৪০১ Chip** *(West Neighbor)* | মৌজা কাশিমপুর, দাগ ৪০১, খতিয়ান ৮৮ | Re-centers map on Dag 401 polygon (৪.৩৭ শতক). Clears conflict alert; confirms LD Tax paid and boundary in order. | **ক্লিয়ার (CLEAR)** — নিয়মিত খাজনা পরিশোধিত |
| **Click দাগ ৪০৩ Chip** *(South Neighbor)* | মৌজা কাশিমপুর, দাগ ৪০৩, খতিয়ান ১২৫ | Re-centers map on Dag 403 polygon (৫.৫৩ শতক). Shows amber warning for 3 years tax arrears and khatian divergence. | **রিভিউ (REVIEW)** — বকেয়া কর নোটিশ প্রযোজ্য |

#### Step 5: Verify the Cryptographic Trust Ledger
1. In the side panel, click the **অডিট লেজার (Ed25519)** tab.
2. Observe the immutable append-only chain blocks (`ব্লক #1`, `ব্লক #2`, etc.).
3. Each block displays the queried Dag, timestamp, decision verdict, SHA-256 hash digest, and verified `Ed25519` signature.
4. Verify via API: [http://127.0.0.1:8000/api/v1/ledger/verify](http://127.0.0.1:8000/api/v1/ledger/verify) (`"is_valid": true`).

#### Step 6: Test the e-Mutation Portal
1. Navigate to: [http://127.0.0.1:8000/portals/e-mutation](http://127.0.0.1:8000/portals/e-mutation).
2. The detection bar updates immediately to `ই-নামজারি পোর্টাল` with mutation case `MUT-2024-GZ-884` and Sub-Registry deed `DEED-2024-DH-402`.

#### ⚠️ Troubleshooting & FAQ
* **Side panel does not open automatically on button click**: In Chrome 116+, click the NAKSHA icon in your extension toolbar directly or click the Chrome Side Panel dropdown and choose **নকশা**.
* **Port 8000 already in use**: Pass `--port 8080` to uvicorn and reload the extension (manifest permits `localhost` and `127.0.0.1`).
* **Tile layer loading**: The Leaflet map uses OpenStreetMap (`tile.openstreetmap.org`) without API keys or watermarks; an active internet connection renders base tiles, while all cadastral GeoJSON polygons and conflict zones are calculated and served 100% locally from FastAPI.

---

## 🌐 API Endpoints

### Canonical Records & Verification
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health and readiness check returning service status, spatial engine state, and version. |
| `GET` | `/api/v1/records` | List normalized land records with pagination (`limit`, `offset`) and filters (`agency`, `mouza`, `dag`). |
| `GET` | `/api/v1/records/{record_id}` | Fetch a specific canonical land record by its unique ID (e.g. `SYN-MATCH-01`). Returns `404` if not found. |
| `GET` | `/api/v1/records/demo` | Runs cross-agency reconciliation across all benchmark scenarios and returns explainable verdicts and findings. |

### 2D GIS & Spatial Engine
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/spatial/parcels` | GeoJSON `FeatureCollection` of all cadastral parcels with attributes (Dag, Khatian, area, tax status). |
| `GET` | `/api/v1/spatial/parcels/{parcel_id}/layers` | 4-layer multi-era visual stack (CS Dag 88 ancestral footprint, Deed claim, DLRS survey, Khas conflict zone). |
| `GET` | `/api/v1/spatial/parcels/{parcel_id}/neighbors` | Target parcel and neighboring plots with LD Tax status (`paid`, `arrears`) for the Tax Map. |
| `GET` | `/api/v1/spatial/parcels/{parcel_id}/conflicts` | Computed geometric conflict zone details (e.g. 0.90 dec Khas canal encroachment). |
| `POST` | `/api/v1/spatial/calculate-area` | Computes deterministic area in UTM 46N (`EPSG:32646`) and returns decimals (শতক) and metric square meters. |
| `POST` | `/api/v1/spatial/calculate-overlap` | Computes geometric intersection and overlap area between two GeoJSON polygons. |

### Cryptographic Trust Ledger (Audit Trail)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/records/{record_id}/verify` | Verifies a single record against cohort and appends an Ed25519-signed block to the ledger. |
| `GET` | `/api/v1/ledger` | Retrieves the append-only SHA-256 hash-chain audit log with Ed25519 signatures. |
| `GET` | `/api/v1/ledger/verify` | Cryptographically verifies the unbroken linkage and digital signatures of all blocks. |

---

## 📂 Repository Structure

```text
naksha/
├── .env.example              # Environment configuration template
├── .gitignore                # Python, Node, database, cache, and secret exclusions
├── LICENSE                   # MIT License
├── README.md                 # Complete project documentation
├── requirements.txt          # Minimal dependency specifications
├── docs/
│   ├── Naksha_Concept_Note.pdf   # Hackathon concept note
│   └── ROADMAP.md                # Multi-phase implementation roadmap
├── naksha/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py            # FastAPI application factory and CORS configuration
│   │   └── routes.py         # Route handlers for health, records, and demo reconciliation
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py         # Application settings
│   ├── data/
│   │   ├── __init__.py
│   │   └── synthetic.py      # Clearly marked synthetic benchmark records
│   ├── models/
│   │   ├── __init__.py
│   │   ├── canonical.py      # Pydantic models: LandRecord, ExtractedField, Discrepancy, etc.
│   │   └── enums.py          # Enums: AgencyType, LandAreaUnit, SurveyEra, LandClass, Verdicts
│   ├── normalization/
│   │   ├── __init__.py
│   │   ├── area.py           # Explicit unit conversion rules (Decimal, Acre, Bigha, Katha, Sqm)
│   │   └── text.py           # Text cleaning, Bangla numerals, identifier & phonetic matching
│   ├── repository/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract BaseRecordRepository interface
│   │   └── memory.py         # In-memory repository with filtering and pagination
│   └── services/
│       ├── __init__.py
│       └── verification.py   # Record comparison, completeness check, and discrepancy detection
└── tests/
    ├── __init__.py
    ├── test_api.py           # API endpoint integration tests (status codes, filters, 404s)
    ├── test_models.py        # Pydantic schema validation, optional fields, JSON serialization
    ├── test_normalization.py # Bangla/English digits, area conversion, phonetic similarity
    ├── test_repository.py    # Repository interface, CRUD, and filter tests
    └── test_synthetic_data.py# Benchmark dataset safety, matching pairs, and conflict tests
```

---

## 👥 Hackathon Team & Mentors

- **Team Leader**: Mahadi Rahman Jihad (ID: 251-15-008, Department of Computer Science & Engineering)
- **Team Member**: Tartib Kaiser Munna (ID: 251-15-848, Department of Computer Science & Engineering)
- **Faculty Mentor**: Abdullah Al-Amin (Lecturer, Department of Computer Science & Engineering)
- **Industry Support Mentor**: Farvez Rakib (CSE-TECH)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).