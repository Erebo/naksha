<div align="center">

# নকশা (NAKSHA)

### AI-Powered Land Record Integrity Engine for Bangladesh

**Cross-agency cadastral verification · 2D GIS spatial analysis · Cryptographic audit ledger**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](#)
[![Chrome MV3](https://img.shields.io/badge/Chrome_Extension-MV3-4285F4?logo=googlechrome&logoColor=white)](#)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS-199900?logo=leaflet&logoColor=white)](#)
[![Ed25519](https://img.shields.io/badge/Ed25519-SHA--256_Ledger-DC382D?logo=letsencrypt&logoColor=white)](#)
[![Tests](https://img.shields.io/badge/tests-67_passed-brightgreen?logo=pytest&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

</div>

---

## 🎯 Problem

Bangladesh's land records are scattered across **5+ agencies** (Sub-Registry, AC Land, DLRS, Union Land Office, DC Office), each using incompatible formats. Officers manually cross-reference paper documents, leading to **fraudulent transfers, Khas encroachment, and double-sale deeds** going undetected.

## 💡 Solution

**NAKSHA** is a zero-integration Chrome Side Panel that overlays existing government portals. It reads the officer's active portal session, verifies identity against a registry, and instantly cross-references cadastral records across all agencies — delivering a **CLEAR / REVIEW / BLOCK** verdict with spatial proof, lineage tracing, and a tamper-proof audit trail.

> **Zero data entry. Zero portal redesign. One click to verify.**

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph PORTAL["🏛️ Government Portal (Mock)"]
        P1["LD Tax Portal"]
        P2["e-Mutation Portal"]
    end

    subgraph EXT["🧩 Chrome Extension (MV3)"]
        CS["Content Script<br/>Reads data-* attributes"]
        BG["Service Worker<br/>Side Panel lifecycle"]
        SP["Side Panel UI<br/>Leaflet + Bento Cards"]
    end

    subgraph API["⚡ FastAPI Backend"]
        AUTH["POST /auth/verify-officer<br/>JWT 15-min + allowlist"]
        REC["GET /api/v1/records<br/>Canonical records"]
        SPATIAL["GET /api/v1/spatial/*<br/>GeoJSON layers"]
        VERIFY["GET /api/v1/records/{id}/verify<br/>Cross-agency check"]
        LEDGER["GET /api/v1/ledger<br/>Hash-chain audit"]
    end

    subgraph ENGINE["🔬 Core Engine"]
        NORM["Normalization<br/>BN↔EN digits, phonetics"]
        SPA["Spatial Engine<br/>Shapely + PyProj UTM"]
        VER["Verification Service<br/>5 statutory rules"]
        TRUST["Trust Ledger<br/>SHA-256 + Ed25519"]
    end

    subgraph DB["🗄️ Storage"]
        SQL["SQLite<br/>Canonical records"]
        MEM["In-Memory<br/>Spatial GeoJSON"]
    end

    P1 & P2 --> CS
    CS -->|"officer identity +<br/>plot context"| BG
    BG --> SP
    SP -->|"API calls"| AUTH & REC & SPATIAL & VERIFY & LEDGER
    AUTH --> TRUST
    REC --> NORM
    SPATIAL --> SPA
    VERIFY --> VER
    VER --> TRUST
    NORM & SPA & VER --> DB
    TRUST --> DB

    style PORTAL fill:#FEF3C7,stroke:#F59E0B,color:#000
    style EXT fill:#DBEAFE,stroke:#3B82F6,color:#000
    style API fill:#D1FAE5,stroke:#10B981,color:#000
    style ENGINE fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style DB fill:#FEE2E2,stroke:#EF4444,color:#000
```

---

## 🖼️ Screenshots

### Portal Integration → Security Gate → Verification Cockpit

<table>
<tr>
<td width="50%">

**Mock Government Portal**
Officer session with floating "যাচাই করুন" pill

![Portal](docs/screenshots/final/01_portal_logged_in.png)

</td>
<td width="50%">

**Security Verification Gate**
Automatic 3-step identity check

![Verification](docs/screenshots/final/05_verify_identity_card_verified.png)

</td>
</tr>
<tr>
<td>

**Cockpit — BLOCK Verdict (EN)**
Khas canal overlap detected on Dag 402

![Cockpit EN](docs/screenshots/final/20_cockpit_english_mode.png)

</td>
<td>

**Access Denied — Unlisted Officer**
Unauthorized `EXT-999-HACK` blocked

![Denied](docs/screenshots/final/06_verify_denial_unlisted_officer.png)

</td>
</tr>
<tr>
<td>

**Multi-Era Layer Popover**
5 cadastral layers — CS·Deed·DLRS·Khas·Conflict

![Layers](docs/screenshots/final/08_map_layers_popover_all_active.png)

</td>
<td>

**Cryptographic Audit Ledger**
SHA-256 + Ed25519 signed blocks

![Audit](docs/screenshots/final/15_tab_audit_access_granted_intact.png)

</td>
</tr>
<tr>
<td>

**Lineage History Track**
CS→SA→RS→BS chain + phonetic name match

![History](docs/screenshots/final/12_tab_history_lineage_graph.png)

</td>
<td>

**Light Theme / Responsive**
Soft grey theme with complete token coverage

![Light](docs/screenshots/final/21_cockpit_light_theme.png)

</td>
</tr>
</table>

> 📸 **Full visual catalog** with 24 screenshots across all scenarios, viewports, and themes: [`docs/screenshots/final/INDEX.md`](docs/screenshots/final/INDEX.md)

---

## ✨ Features & Architecture Diagrams

### 1. 🔐 Zero-Login Officer Verification

No credentials entered. Identity is read from the portal's DOM `data-*` attributes.

```mermaid
sequenceDiagram
    participant P as Gov Portal
    participant CS as Content Script
    participant SP as Side Panel
    participant API as /auth/verify-officer

    P->>CS: data-officer-id, data-officer-name,<br/>data-officer-role, data-officer-office
    CS->>SP: Officer identity payload
    SP->>SP: Show identity card
    SP->>API: POST {portal_origin, officer_id,<br/>name, designation, office}
    API->>API: ✓ Origin allowlist<br/>✓ Officer registry<br/>✓ ID + name + title match
    alt Verified
        API-->>SP: 200 JWT (15-min, role + jurisdiction)
        SP->>SP: ✅ "যাচাই সম্পন্ন" → Cockpit
    else Denied
        API-->>SP: 403 denial_reason
        SP->>SP: ❌ "যাচাই ব্যর্থ" — locked
    end
    API->>API: Log ACCESS_GRANTED / ACCESS_DENIED<br/>to audit ledger
```

### 2. 🗺️ Multi-Era 2D GIS Spatial Engine

Five toggleable cadastral layers rendered on Leaflet with UTM 46N (`EPSG:32646`) precision.

```mermaid
flowchart LR
    subgraph LAYERS["Cadastral Layer Stack"]
        L1["🟣 CS 1888<br/>Ancestral Footprint<br/>18.00 শতক"]
        L2["🟠 Deed Claim<br/>Sub-Registry<br/>6.00 শতক"]
        L3["🔵 DLRS Survey<br/>Ground Truth (BS)<br/>5.10 শতক"]
        L4["🔴 Khas Canal<br/>Gov. Drainage<br/>8.48 শতক"]
        L5["❌ Conflict Zone<br/>Computed Overlap<br/>0.90 শতক"]
    end

    L1 & L2 & L3 & L4 --> L5

    subgraph CALC["Spatial Calculations"]
        C1["Shapely<br/>Polygon Intersection"]
        C2["PyProj UTM 46N<br/>Area (m² → শতক)"]
        C3["Tolerance Check<br/>±0.20 শতক limit"]
    end

    L5 --> C1 --> C2 --> C3

    style L5 fill:#FEE2E2,stroke:#EF4444,color:#000
    style CALC fill:#EDE9FE,stroke:#8B5CF6,color:#000
```

### 3. ⚖️ 5-Rule Statutory Verification Engine

Each plot is evaluated against Bangladesh land law. The worst-case rule determines the verdict.

```mermaid
flowchart TD
    INPUT["Plot Context<br/>(Dag, Khatian, Mouza)"] --> R1 & R2 & R3 & R4 & R5

    R1["Rule 1: Khas Encroachment<br/>0.00 শতক allowed on gov land"]
    R2["Rule 2: Area Tolerance<br/>Deed vs DLRS ≤ ±0.20 শতক"]
    R3["Rule 3: Khatian Name Match<br/>≥ 80% phonetic similarity"]
    R4["Rule 4: LD Tax Compliance<br/>≤ 1 year arrears"]
    R5["Rule 5: Mutation Status<br/>Deed must be mutated"]

    R1 -->|FAIL| BLOCK["🔴 BLOCK<br/>নামজারি স্থগিত"]
    R2 -->|FAIL| BLOCK
    R3 -->|FAIL| REVIEW["🟡 REVIEW<br/>মানব পর্যালোচনা"]
    R4 -->|FAIL| REVIEW
    R5 -->|FAIL| REVIEW
    R1 & R2 & R3 & R4 & R5 -->|ALL PASS| CLEAR["🟢 CLEAR<br/>নিয়মিত প্রক্রিয়া"]

    style BLOCK fill:#FEE2E2,stroke:#EF4444,color:#000
    style REVIEW fill:#FEF3C7,stroke:#F59E0B,color:#000
    style CLEAR fill:#D1FAE5,stroke:#10B981,color:#000
```

### 4. 🔗 Cryptographic Trust Ledger

Every verification action is recorded in an immutable, hash-chained, digitally signed audit trail.

```mermaid
flowchart LR
    G["Block #0<br/>GENESIS<br/>hash: 0×64"]
    B1["Block #1<br/>VERIFICATION_VERDICT<br/>Dag 402 · BLOCK"]
    B2["Block #2<br/>ACCESS_GRANTED<br/>UL-2024-KSH"]
    B3["Block #3<br/>ACCESS_DENIED<br/>EXT-999-HACK"]
    BN["Block #N<br/>..."]

    G -->|"SHA-256<br/>prev_hash"| B1
    B1 -->|"SHA-256<br/>prev_hash"| B2
    B2 -->|"SHA-256<br/>prev_hash"| B3
    B3 -->|"SHA-256<br/>prev_hash"| BN

    B1 -.- S1["✓ Ed25519"]
    B2 -.- S2["✓ Ed25519"]
    B3 -.- S3["✓ Ed25519"]

    style G fill:#374151,stroke:#9CA3AF,color:#fff
    style S1 fill:#D1FAE5,stroke:#10B981,color:#000
    style S2 fill:#D1FAE5,stroke:#10B981,color:#000
    style S3 fill:#D1FAE5,stroke:#10B981,color:#000
```

### 5. 🏛️ Cross-Agency Data Flow

```mermaid
flowchart TD
    subgraph AGENCIES["Siloed Government Agencies"]
        A1["📋 Sub-Registry<br/>Sale Deeds"]
        A2["📋 AC Land<br/>e-Mutation"]
        A3["📋 DLRS<br/>Ground Survey"]
        A4["📋 Union Land Office<br/>LD Tax"]
        A5["📋 DC Office<br/>Khas Register"]
    end

    subgraph NAKSHA["🔬 NAKSHA Reconciliation"]
        N1["Normalize<br/>BN ↔ EN digits<br/>Phonetic matching"]
        N2["Cross-Reference<br/>Dag · Khatian · Area<br/>Owner · Class"]
        N3["Spatial Analysis<br/>Polygon overlap<br/>UTM area calc"]
        N4["Verdict Engine<br/>5 statutory rules"]
    end

    A1 & A2 & A3 & A4 & A5 --> N1 --> N2 --> N3 --> N4

    N4 -->|"✅"| V1["CLEAR"]
    N4 -->|"⚠️"| V2["REVIEW"]
    N4 -->|"🚫"| V3["BLOCK"]

    style AGENCIES fill:#FEF3C7,stroke:#F59E0B,color:#000
    style NAKSHA fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style V1 fill:#D1FAE5,stroke:#10B981,color:#000
    style V2 fill:#FEF3C7,stroke:#F59E0B,color:#000
    style V3 fill:#FEE2E2,stroke:#EF4444,color:#000
```

### 6. 📊 Cockpit Tab Architecture

```mermaid
flowchart LR
    COCKPIT["Verification<br/>Cockpit"] --> T1 & T2 & T3 & T4 & T5

    T1["📊 Overview<br/>Area bars · Overlap ring<br/>Rule pass/fail grid"]
    T2["🕰️ History<br/>CS→SA→RS→BS lineage<br/>Phonetic name match %"]
    T3["💰 Tax<br/>3-year holding metrics<br/>Arrears detection"]
    T4["🛡️ Liens<br/>CIB / AC Land<br/>Encumbrance status"]
    T5["🔗 Audit<br/>SHA-256 hash chain<br/>Ed25519 signatures"]

    style COCKPIT fill:#DBEAFE,stroke:#3B82F6,color:#000
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Google Chrome (for extension)

### 1. Setup
```bash
git clone https://github.com/Erebo/naksha.git && cd naksha
python -m venv venv && .\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### 2. Run Backend
```bash
uvicorn naksha.api.app:app --reload --port 8000
```

### 3. Load Chrome Extension
1. Go to `chrome://extensions/` → Enable **Developer mode**
2. Click **Load unpacked** → Select `extension/` folder
3. Navigate to [http://127.0.0.1:8000/portals/ld-tax](http://127.0.0.1:8000/portals/ld-tax)
4. Click **"যাচাই করুন"** pill → Side Panel opens with verification gate

### 4. Run Tests
```bash
pytest -v    # 67 tests covering all layers
```

### 5. Capture Screenshots
```bash
python scripts/capture_screenshots.py    # 24 automated Playwright captures
```

---

## 📂 Project Structure

```
naksha/
├── extension/                  # Chrome MV3 Extension
│   ├── manifest.json           # Extension manifest
│   ├── background.js           # Service worker (side panel lifecycle)
│   ├── content.js              # Portal DOM reader + floating pill
│   ├── sidepanel.{html,css,js} # Verification cockpit UI
│   ├── tokens.css              # Design tokens (dark/light)
│   └── components/             # VerdictHero, AreaChart, AuditChain,
│                               # LineageTimeline, TaxChart, RuleGrid, i18n
├── naksha/
│   ├── api/
│   │   ├── app.py              # FastAPI factory + CORS + static mounts
│   │   └── routes.py           # 15+ REST endpoints
│   ├── models/
│   │   ├── canonical.py        # Pydantic schemas (LandRecord, GeoJSON, etc.)
│   │   └── enums.py            # AgencyType, Verdict, SurveyEra, LandClass
│   ├── normalization/
│   │   ├── text.py             # BN↔EN digits, phonetic matching
│   │   └── area.py             # Unit conversion (শতক, বিঘা, কাঠা, একর)
│   ├── spatial/
│   │   └── engine.py           # Shapely + PyProj (UTM 46N) calculations
│   ├── services/
│   │   ├── verification.py     # 5-rule statutory engine
│   │   └── ledger.py           # SHA-256 + Ed25519 trust ledger
│   ├── database/               # SQLite + SQLAlchemy persistence
│   ├── data/                   # Synthetic benchmark datasets
│   └── static/                 # Mock portals + standalone side panel
├── tests/                      # 67 tests (pytest)
├── scripts/                    # Playwright screenshot automation
└── docs/screenshots/final/     # 24 captured visual artifacts
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Service readiness check |
| `POST` | `/auth/verify-officer` | Officer identity verification → JWT |
| `GET` | `/api/v1/records` | List canonical records (paginated + filtered) |
| `GET` | `/api/v1/records/{id}` | Fetch single record |
| `GET` | `/api/v1/records/{id}/verify` | Cross-agency verification → verdict |
| `GET` | `/api/v1/spatial/parcels` | All parcels as GeoJSON FeatureCollection |
| `GET` | `/api/v1/spatial/parcels/{id}/layers` | 5-layer cadastral stack |
| `GET` | `/api/v1/spatial/parcels/{id}/neighbors` | Neighbor plots + tax status |
| `GET` | `/api/v1/spatial/parcels/{id}/conflicts` | Computed conflict zones |
| `POST` | `/api/v1/spatial/calculate-area` | Polygon → area (m² + শতক) |
| `POST` | `/api/v1/spatial/calculate-overlap` | Two polygons → intersection area |
| `GET` | `/api/v1/ledger` | Full audit chain |
| `GET` | `/api/v1/ledger/verify` | Cryptographic chain integrity check |

---

## 🧪 Test Coverage

| Suite | Tests | Scope |
|:------|:-----:|:------|
| `test_api.py` | 7 | API endpoints, status codes, filters |
| `test_extension.py` | 7 | Manifest, content script, side panel contract |
| `test_frontend.py` | 4 | Portal HTML structure, pill injection |
| `test_ledger.py` | 5 | Hash chain, Ed25519 signatures, integrity |
| `test_mock_portals.py` | 4 | Portal routes, officer data attributes |
| `test_models.py` | 6 | Pydantic validation, JSON serialization |
| `test_normalization.py` | 10 | BN/EN digits, area conversion, phonetics |
| `test_repository.py` | 1 | Repository CRUD + filtering |
| `test_spatial.py` | 17 | UTM projection, overlap, GeoJSON, tolerance |
| `test_synthetic_data.py` | 6 | Benchmark integrity, conflict scenarios |
| **Total** | **67** | **All green ✅** |

---

## 🎨 Tech Stack

```mermaid
flowchart LR
    subgraph Frontend
        A["Chrome MV3 Extension"]
        B["Leaflet.js GIS"]
        C["Vanilla JS Components"]
        D["CSS Design Tokens"]
    end

    subgraph Backend
        E["FastAPI"]
        F["Pydantic v2"]
        G["SQLAlchemy + SQLite"]
    end

    subgraph Geospatial
        H["Shapely 2.0"]
        I["PyProj EPSG:32646"]
    end

    subgraph Security
        J["Ed25519 Signatures"]
        K["SHA-256 Hash Chain"]
        L["JWT (15-min)"]
    end

    Frontend --> Backend --> Geospatial --> Security

    style Frontend fill:#DBEAFE,stroke:#3B82F6,color:#000
    style Backend fill:#D1FAE5,stroke:#10B981,color:#000
    style Geospatial fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style Security fill:#FEE2E2,stroke:#EF4444,color:#000
```

---

## 👥 Team

| Role | Name | ID |
|:-----|:-----|:---|
| **Team Leader** | Mahadi Rahman Jihad | 251-15-008, CSE |
| **Team Member** | Tartib Kaiser Munna | 251-15-848, CSE |
| **Faculty Mentor** | Abdullah Al-Amin | Lecturer, CSE |
| **Industry Mentor** | Farvez Rakib | CSE-TECH |

---

## 📜 License

[MIT License](LICENSE)