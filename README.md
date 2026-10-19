<div align="center">

# নকশা (NAKSHA)

### AI-Powered Land Record Integrity Engine for Bangladesh

**Cross-agency cadastral verification · 2D GIS spatial analysis · Cryptographic audit ledger**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_PostGIS_3.4-336791?logo=postgresql&logoColor=white)](#)
[![Chrome MV3](https://img.shields.io/badge/Chrome_Extension-MV3-4285F4?logo=googlechrome&logoColor=white)](#)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS-199900?logo=leaflet&logoColor=white)](#)
[![Ed25519](https://img.shields.io/badge/Ed25519-SHA--256_Ledger-DC382D?logo=letsencrypt&logoColor=white)](#)
[![Tests](https://img.shields.io/badge/tests-136_passed-brightgreen?logo=pytest&logoColor=white)](#)
[![Concept Note](https://img.shields.io/badge/Concept_Note-PDF-red?logo=adobeacrobatreader&logoColor=white)](docs/Naksha_Concept_Note.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

</div>

---

## 🎯 Problem

Bangladesh's land records are scattered across **5+ agencies** (Sub-Registry, AC Land, DLRS, Union Land Office, DC Office), each using incompatible formats. Officers manually cross-reference paper documents, leading to **fraudulent transfers, Khas encroachment, and double-sale deeds** going undetected.

## 💡 Solution

**NAKSHA** is a zero-integration Chrome Side Panel that overlays existing government portals. It reads the officer's active portal session, verifies identity against a database registry, and instantly cross-references cadastral records across all agencies — delivering a **CLEAR / REVIEW / BLOCK** verdict with spatial proof, lineage tracing, and an immutable, tamper-evident audit trail.

> **Zero data entry. Zero portal redesign. One click to verify.**
>
> 📄 **[Download the Official Naksha Concept Note (PDF)](docs/Naksha_Concept_Note.pdf)** — *4-page executive brief prepared for the LandTech 2026 Innovation Hackathon.*

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph PORTAL["🏛️ Government Portals (Mock)"]
        P1["LD Tax Portal"]
        P2["e-Mutation Portal"]
    end

    subgraph EXT["🧩 Chrome Extension (MV3)"]
        CS["Content Script<br/>Reads DOM data-* attributes"]
        BG["Service Worker<br/>Side Panel lifecycle"]
        SP["Side Panel UI (Cockpit)<br/>Leaflet 2D GIS + Bento Cards"]
    end

    subgraph API["⚡ FastAPI Routers (Auth & Rate Limiting)"]
        AUTH["POST /auth/verify-officer<br/>Origin check · Rate limit · JWT"]
        REC["GET /api/v1/records/*<br/>Canonical land records"]
        SPATIAL["GET /api/v1/spatial/*<br/>PostGIS GeoJSON & layers"]
        VERIFY["GET /api/v1/.../verify<br/>Cross-agency verification"]
        LEDGER["GET /api/v1/ledger/*<br/>Audit log & integrity verification"]
    end

    subgraph ENGINE["🔬 Core Engine & Services"]
        NORM["Normalization<br/>BN↔EN digits, phonetics"]
        SPA["Spatial Engine<br/>Shapely + PyProj UTM 46N"]
        RULES["Rule Engine<br/>5 statutory rules (FAIL/PASS/UNKNOWN)"]
        VER["Verification Service<br/>Rules + Discrepancies synthesis"]
    end

    subgraph REPO["📦 Data Access Layer"]
        RBASE["SpatialRepository Interface<br/>PostgresRecordRepository"]
    end

    subgraph DB["🗄️ PostgreSQL 16 + PostGIS 3.4"]
        PG["PostGIS Spatial Tables<br/>Parcels · Surveys · Zones · Officers · Liens"]
        TRUST["Persistent Trust Ledger<br/>ledger_entries (Immutable Trigger)"]
        ALEMBIC["Alembic Migrations<br/>Versioned DDL & constraints"]
    end

    P1 & P2 --> CS
    CS -->|"officer identity +<br/>plot context"| BG
    BG --> SP
    SP -->|"Authenticated API calls (Bearer JWT)"| AUTH & REC & SPATIAL & VERIFY & LEDGER
    AUTH --> TRUST
    REC --> REPO
    SPATIAL --> SPA
    SPA --> REPO
    VERIFY --> VER
    VER --> RULES
    VER --> TRUST
    RULES --> REPO
    REPO --> PG
    ALEMBIC -.-> PG & TRUST

    style PORTAL fill:#FEF3C7,stroke:#F59E0B,color:#000
    style EXT fill:#DBEAFE,stroke:#3B82F6,color:#000
    style API fill:#D1FAE5,stroke:#10B981,color:#000
    style ENGINE fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style REPO fill:#E0E7FF,stroke:#6366F1,color:#000
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

Identity is read directly from portal DOM attributes, validated against the database registry, guarded by rate limits, and confirmed via separate origin checks.

```mermaid
sequenceDiagram
    participant P as Gov Portal
    participant CS as Content Script
    participant SP as Side Panel
    participant API as /auth/verify-officer
    participant DB as PostgreSQL DB
    participant LEDGER as Trust Ledger

    P->>CS: DOM data-officer-* attributes
    CS->>SP: Officer identity payload + portal origin
    SP->>SP: Render verification gate screen
    SP->>API: POST {portal_origin, officer_id, name, designation, office}
    Note over API: 1. Rate Limit Guard (5 req / 60s per IP)
    Note over API: 2. Exact Origin Allowlist Check<br/>✓ Origin/Referer header in allowlist<br/>✓ portal_origin body parameter in allowlist
    Note over API: 3. Officer Lookup in Database
    API->>DB: Query officers table by officer_id
    DB-->>API: Officer record (is_active, role, jurisdiction, name)
    alt Inactive or Suspended Officer
        API->>LEDGER: Append ACCESS_DENIED (inactive_officer)
        API-->>SP: 403 Forbidden ("Officer account is inactive")
        SP->>SP: ❌ Access Denied screen
    else Unknown Officer or Data Mismatch
        API->>LEDGER: Append ACCESS_DENIED (unlisted/mismatch)
        API-->>SP: 403 Forbidden ("Officer not authorized")
        SP->>SP: ❌ Access Denied screen
    else Active & Verified
        API->>LEDGER: Append ACCESS_GRANTED (UL-2024-KSH)
        API-->>SP: 200 OK + Signed JWT (15-min expiry, role, jurisdiction)
        SP->>SP: ✅ "যাচাই সম্পন্ন" → Open Verification Cockpit
    end
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

Each plot is evaluated against statutory rules. Missing data produces an `UNKNOWN` state (never `PASS`), and the final verdict represents the worst case across all evaluated rules and blocking discrepancies.

```mermaid
flowchart TD
    INPUT["Plot Context<br/>(Dag, Mouza, Khatian, Records, Spatial Layers)"] --> R1 & R2 & R3 & R4 & R5

    R1["Rule 1: Khas Encroachment<br/>Limit: 0.00 শতক on gov waterbody"]
    R2["Rule 2: Area Tolerance<br/>Deed vs DLRS ≤ ±0.20 শতক"]
    R3["Rule 3: Khatian Owner Match<br/>≥ 80% phonetic similarity"]
    R4["Rule 4: LD Tax Compliance<br/>≤ 1 year tax arrears"]
    R5["Rule 5: Mutation Status<br/>Deed mutated within 30 days"]

    R1 -->|FAIL / BLOCK| BLOCK_R["🔴 BLOCK<br/>নামজারি স্থগিত"]
    R2 -->|FAIL / BLOCK| BLOCK_R
    R3 -->|FAIL / REVIEW| REVIEW_R["🟡 REVIEW<br/>মানব পর্যালোচনা"]
    R4 -->|FAIL / REVIEW| REVIEW_R
    R5 -->|FAIL / REVIEW| REVIEW_R

    R1 & R2 & R3 & R4 & R5 -->|UNKNOWN / Missing Data| UNKNOWN_R["⚪ UNKNOWN<br/>Insufficient Data (never PASS)"]
    UNKNOWN_R -->|Escalates to| REVIEW_R

    R1 & R2 & R3 & R4 & R5 -->|ALL PASS| CLEAR_R["🟢 CLEAR<br/>অনুমোদনের সুপারিশ"]

    DISC["Blocking Discrepancies<br/>(Class conflict, chain breakage)"] -.->|Override| BLOCK_R

    subgraph DECISION["Verdict Synthesis: worst(rules ∪ blocking discrepancies)"]
        BLOCK_R --> VERDICT_BLOCK["Final Verdict: BLOCK"]
        REVIEW_R --> VERDICT_REVIEW["Final Verdict: REVIEW"]
        CLEAR_R --> VERDICT_CLEAR["Final Verdict: CLEAR"]
    end

    style BLOCK_R fill:#FEE2E2,stroke:#EF4444,color:#000
    style REVIEW_R fill:#FEF3C7,stroke:#F59E0B,color:#000
    style UNKNOWN_R fill:#F1F5F9,stroke:#64748B,color:#000
    style CLEAR_R fill:#D1FAE5,stroke:#10B981,color:#000
    style VERDICT_BLOCK fill:#FEE2E2,stroke:#EF4444,color:#000
    style VERDICT_REVIEW fill:#FEF3C7,stroke:#F59E0B,color:#000
    style VERDICT_CLEAR fill:#D1FAE5,stroke:#10B981,color:#000
```

### 4. 🔗 Cryptographic Trust Ledger

Every action is persisted in PostgreSQL in an append-only table. Mutating or deleting entries is strictly blocked by a database trigger. Signatures are verified against a pinned public key from environment settings.

```mermaid
flowchart LR
    subgraph SIGNING["Key Management"]
        ENV["NAKSHA_LEDGER_PRIVATE_KEY<br/>Loaded from environment (32-byte hex)"]
        PRIV["Ed25519 Private Key<br/>Never generated per-start"]
        PUB["Pinned Public Key<br/>settings.get_ledger_public_key()"]
        ENV --> PRIV --> PUB
    end

    subgraph PERSIST["PostgreSQL: ledger_entries Table"]
        G["Block #0<br/>GENESIS<br/>prev: 0×64"]
        B1["Block #1<br/>VERIFICATION_VERDICT<br/>Dag 402 · BLOCK"]
        B2["Block #2<br/>ACCESS_GRANTED<br/>UL-2024-KSH"]
        B3["Block #3<br/>ACCESS_DENIED<br/>INACTIVE_OFFICER"]
        BN["Block #N<br/>..."]

        G -->|"SHA-256<br/>prev_hash"| B1
        B1 -->|"SHA-256<br/>prev_hash"| B2
        B2 -->|"SHA-256<br/>prev_hash"| B3
        B3 -->|"SHA-256<br/>prev_hash"| BN
    end

    subgraph TAMPER["Immutability Protection"]
        LOCK["Concurrency Lock<br/>pg_advisory_xact_lock +<br/>SELECT ... FOR UPDATE"]
        TRG["PostgreSQL Trigger<br/>trg_ledger_entries_immutable<br/>BEFORE UPDATE OR DELETE<br/>RAISE EXCEPTION"]
    end

    subgraph VERIFY_INTEGRITY["Integrity Verification (/ledger/verify)"]
        V1["1. Genesis link & hash check"]
        V2["2. Sequential index check"]
        V3["3. Recompute payload_hash"]
        V4["4. Recompute entry_hash"]
        V5["5. Verify signature against PINNED public key"]
        V1 --> V2 --> V3 --> V4 --> V5
    end

    PRIV -.->|"Sign entry_hash"| B1 & B2 & B3 & BN
    LOCK -.-> B1 & B2 & B3 & BN
    TRG -.-> PERSIST
    PUB -.-> V5
    PERSIST -.-> VERIFY_INTEGRITY

    style G fill:#374151,stroke:#9CA3AF,color:#fff
    style SIGNING fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style PERSIST fill:#D1FAE5,stroke:#10B981,color:#000
    style TAMPER fill:#FEE2E2,stroke:#EF4444,color:#000
    style VERIFY_INTEGRITY fill:#FEF3C7,stroke:#F59E0B,color:#000
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

    T1["📊 Overview<br/>Area bars · Overlap ring<br/>Dynamic backend rules[] grid"]
    T2["🕰️ History<br/>CS→SA→RS→BS lineage<br/>Phonetic name match %"]
    T3["💰 Tax<br/>3-year holding metrics<br/>Arrears detection"]
    T4["🛡️ Liens<br/>CIB / AC Land / Bank<br/>Encumbrance status"]
    T5["🔗 Audit<br/>PostgreSQL hash chain<br/>Ed25519 signed blocks"]

    style COCKPIT fill:#DBEAFE,stroke:#3B82F6,color:#000
```

### 7. 🗄️ PostGIS Cadastral Relational Schema (ERD)

The PostgreSQL 16 schema stores multi-era spatial polygons in PostGIS (EPSG:4326 with UTM 46N transformations), encumbrance data, officer credentials, and the immutable audit chain:

```mermaid
erDiagram
    CANONICAL_PARCELS ||--o{ SURVEY_LAYERS : "has historical layers"
    CANONICAL_PARCELS ||--o{ TAX_PAYMENTS : "has tax records"
    CANONICAL_PARCELS ||--o{ LIENS : "has encumbrances"
    CANONICAL_PARCELS ||--o{ PARCEL_LINEAGE : "links ancestral chain"
    CANONICAL_PARCELS }o--o{ RESTRICTED_ZONES : "spatial ST_Intersects"
    OFFICERS ||--o{ LEDGER_ENTRIES : "authenticates actions"
    CANONICAL_PARCELS ||--o{ LEDGER_ENTRIES : "audits verdicts"

    CANONICAL_PARCELS {
        uuid id PK
        string upazila
        string mouza
        string dag_number
        string khatian_number
        geometry geometry_4326 "PostGIS Polygon EPSG:4326"
        float deed_area_decimals
        float dlrs_area_decimals
    }
    SURVEY_LAYERS {
        uuid id PK
        uuid parcel_id FK
        string survey_era "CS, SA, RS, BS"
        geometry geometry_4326 "PostGIS Polygon EPSG:4326"
        float area_decimals
    }
    RESTRICTED_ZONES {
        uuid id PK
        string zone_type "khas_waterbody, forest"
        string name_en
        geometry geometry_4326 "PostGIS MultiPolygon"
    }
    OFFICERS {
        string officer_id PK
        string name
        string role "ac_land, kanoongo, union_land_officer"
        string jurisdiction
        boolean is_active
    }
    TAX_PAYMENTS {
        uuid id PK
        uuid parcel_id FK
        string fiscal_year
        float amount_bdt
        boolean is_paid
    }
    LIENS {
        uuid id PK
        uuid parcel_id FK
        string lien_type "mortgage, freeze, dispute"
        string status "active, discharged"
    }
    PARCEL_LINEAGE {
        uuid ancestor_id FK
        uuid descendant_id FK
        string era_from
        string era_to
    }
    LEDGER_ENTRIES {
        int entry_index PK
        timestamp timestamp "UTC with timezone"
        string event_type
        uuid parcel_id
        string verdict
        string payload_hash
        string previous_hash
        string entry_hash
        string signature "Ed25519 hex"
    }
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop (for PostgreSQL 16 + PostGIS 3.4)
- Google Chrome (for MV3 extension)

### 1. Environment & Setup
```bash
git clone https://github.com/Erebo/naksha.git && cd naksha
python -m venv venv && .\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create a `.env` file in the project root:
```env
NAKSHA_ENVIRONMENT=development
NAKSHA_DATABASE_URL=postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha
NAKSHA_TEST_DATABASE_URL=postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test
NAKSHA_SECRET_KEY=change-to-a-secure-random-secret-in-production
NAKSHA_NID_HMAC_SECRET=change-to-a-secure-random-salt-in-production
NAKSHA_ALLOWED_ORIGINS=["http://localhost:8000","http://127.0.0.1:8000","chrome-extension://<YOUR_EXTENSION_ID>"]
NAKSHA_LEDGER_PRIVATE_KEY=<generate-with-cli-command-below>
```

> 🔑 **Generate a Production Ledger Key**:
> ```bash
> python -m naksha.cli generate-ledger-key
> ```
> In production, `NAKSHA_SECRET_KEY`, `NAKSHA_NID_HMAC_SECRET`, and `NAKSHA_LEDGER_PRIVATE_KEY` must be configured with strong, non-default values or startup will safely abort.

### 3. Start PostgreSQL + PostGIS Service
```powershell
docker compose up -d
```

### 4. Apply Database Migrations
```powershell
alembic upgrade head
```

### 5. Seed Benchmark Data
```powershell
python -m naksha.cli seed --target postgres --yes
```

### 6. Run Backend
```powershell
uvicorn naksha.api.app:app --reload --port 8000
```

### 7. Load Chrome Extension
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and select the `extension/` directory
4. Note your extension's generated ID and add `chrome-extension://<ID>` to `NAKSHA_ALLOWED_ORIGINS` in `.env` if needed
5. Visit [http://127.0.0.1:8000/portals/ld-tax](http://127.0.0.1:8000/portals/ld-tax)
6. Click the floating **"যাচাই করুন"** pill → Complete automated officer verification → Cockpit renders

### 8. Run Tests
```powershell
# Run all tests (PostgreSQL integration tests included)
$env:NAKSHA_TEST_DATABASE_URL="postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test"
pytest -q

# Or run tests offline without PostgreSQL (Postgres tests skipped automatically)
$env:NAKSHA_TEST_DATABASE_URL="none"
pytest -q
```

---

## 📂 Project Structure

```
naksha/
├── alembic/                    # Database migrations (0001–0004)
│   ├── versions/               # Schema, PostGIS, constraints, persistent ledger
│   └── env.py                  # Migration runner targeting database_url or test DB
├── docker/                     # Docker initialization scripts (init-test-db.sh)
├── extension/                  # Chrome MV3 Extension
│   ├── manifest.json           # Manifest V3 configuration & permissions
│   ├── background.js           # Service worker managing side panel lifecycle
│   ├── content.js              # Portal DOM reader + floating pill injector
│   ├── sidepanel.{html,css,js} # Verification cockpit UI & state orchestration
│   ├── tokens.css              # Linear/Stripe design tokens (dark/light themes)
│   └── components/             # RuleGrid (dynamic), VerdictHero, AreaChart,
│                               # AuditChain, LineageTimeline, TaxChart, i18n
├── naksha/
│   ├── api/
│   │   ├── app.py              # FastAPI factory, CORS, static portal mounts
│   │   └── routes.py           # Authenticated REST endpoints with role guards
│   ├── cli/
│   │   ├── __main__.py         # CLI entrypoint (seed, generate-ledger-key)
│   │   └── seed.py             # Idempotent PostgreSQL & PostGIS cadastral seeder
│   ├── core/
│   │   ├── auth.py             # JWT bearer verification, origin guards, rate limiting
│   │   └── config.py           # Pydantic Settings, statutory thresholds, env validation
│   ├── database/
│   │   ├── connection.py       # SQLAlchemy dynamic engine & session factory
│   │   ├── models.py           # Prototype models (SQLite fallback)
│   │   └── pg_models.py        # PostGIS models (parcels, surveys, ledger_entries)
│   ├── repository/
│   │   ├── base.py             # BaseRecordRepository & SpatialRepository interfaces
│   │   └── pg_repository.py    # PostgreSQL + PostGIS repository implementation
│   ├── services/
│   │   ├── verification.py     # Cross-agency verification & verdict synthesis
│   │   ├── ledger.py           # Persistent, tamper-evident Ed25519 TrustLedger
│   │   └── rules/              # 5 discrete statutory business rules
│   │       ├── khas_encroachment.py
│   │       ├── area_tolerance.py
│   │       ├── mutation_status.py
│   │       ├── owner_name_match.py
│   │       └── ld_tax_compliance.py
│   ├── spatial/
│   │   └── engine.py           # Shapely 2.0 + PyProj (UTM 46N) geospatial math
│   ├── normalization/          # Bengali text/digit normalization & area conversion
│   ├── models/                 # Domain Pydantic models (canonical, rules, enums)
│   ├── data/                   # Synthetic benchmark datasets (parcels, khas, officers)
│   └── static/                 # Mock government portals + standalone sidepanel view
├── tests/                      # 136 tests across 16 test modules
├── scripts/                    # Playwright automated screenshot scripts
├── docker-compose.yml          # PostgreSQL 16 + PostGIS 3.4 container service
├── alembic.ini                 # Alembic migration environment configuration
├── requirements.txt            # Pinned production dependencies (FastAPI, PostGIS, PyJWT)
└── docs/                       # Architecture, screenshots, database runbooks
    ├── Naksha_Concept_Note.pdf # 4-page executive concept note (LandTech 2026 Hackathon)
    ├── DATABASE.md             # PostgreSQL + PostGIS runbook & migration guide
    └── ROADMAP.md              # Multi-phase rollout and future milestones
```

---

## 🌐 API Reference

| Method | Endpoint | Auth | Description |
|:-------|:---------|:-----|:------------|
| `GET` | `/health` | Public | Service readiness and engine health check |
| `POST` | `/auth/verify-officer` | Public (Rate-limited, Origin allowlist) | Officer identity verification → signed 15-min JWT session |
| `GET` | `/api/v1/records` | Bearer JWT (`records`) | List canonical land records (paginated + filtered) |
| `GET` | `/api/v1/records/{id}` | Bearer JWT (`records`) | Fetch single canonical record by ID |
| `GET` | `/api/v1/records/{id}/verify` | Bearer JWT (`verification`) | Cross-agency verification → statutory verdict & rules |
| `GET` | `/api/v1/spatial/parcels` | Bearer JWT (`gis`) | All parcels as GeoJSON FeatureCollection |
| `GET` | `/api/v1/spatial/parcels/resolve` | Bearer JWT (`gis`) | Resolve parcel by normalized mouza + dag key |
| `GET` | `/api/v1/spatial/parcels/verify/{parcel_id}` | Bearer JWT (`verification`) | Verify parcel by UUID against repository |
| `GET` | `/api/v1/spatial/parcels/{id}/layers` | Bearer JWT (`gis`) | 5-layer cadastral stack (CS, Deed, DLRS, Khas, Conflict) |
| `GET` | `/api/v1/spatial/parcels/{id}/neighbors` | Bearer JWT (`gis`) | Neighbor parcels within spatial radius + tax status |
| `GET` | `/api/v1/spatial/parcels/{id}/conflicts` | Bearer JWT (`gis`) | Restricted zone (Khas canal) intersection area |
| `POST` | `/api/v1/spatial/calculate-area` | Bearer JWT (`gis`) | Polygon geometry → area in UTM 46N (m² + decimals) |
| `POST` | `/api/v1/spatial/calculate-overlap` | Bearer JWT (`gis`) | Two polygons → intersection area in UTM 46N |
| `GET` | `/api/v1/ledger` | Bearer JWT (`ledger`) | Retrieve recent append-only audit ledger blocks |
| `GET` | `/api/v1/ledger/verify` | Bearer JWT (`ledger`) | Full cryptographic chain integrity check (Ed25519) |

---

## 🧪 Test Coverage

| Suite | Tests | Scope |
|:------|:-----:|:------|
| `test_api.py` | 7 | REST API status codes, pagination, and filter parameters |
| `test_auth.py` | 18 | JWT creation/verification, role enforcement, origin checks, rate limiting |
| `test_extension.py` | 8 | Manifest V3, CSP compliance, Leaflet tiles, dynamic RuleGrid assertions |
| `test_frontend.py` | 4 | HTML endpoints, static assets, and mock portal responses |
| `test_ledger.py` | 5 | In-memory cryptographic trust ledger, genesis block, tamper detection |
| `test_mock_portals.py` | 4 | Mock government portals DOM attributes and multi-plot journey |
| `test_models.py` | 6 | Pydantic validation, serialization, and confidence score bounds |
| `test_normalization.py` | 10 | Bengali/English digit conversion, area conversion, phonetic similarity |
| `test_pg_ledger.py` | 6 | PostgreSQL ledger persistence, restart survival, trigger tamper defense, concurrency |
| `test_pg_repository.py` | 7 | Postgres repository parity, parcel resolver, Khas UTM overlap, neighbor radius, seeding |
| `test_pg_schema.py` | 7 | PostGIS DDL, spatial constraints, downgrade base → upgrade head migrations |
| `test_repository.py` | 1 | Base repository CRUD interface behavior |
| `test_route_protection.py` | 2 | Comprehensive API route security audits & unauthenticated rejection |
| `test_rules.py` | 20 | 5 discrete statutory rules, UNKNOWN states, boundary limits, verdict hierarchy |
| `test_spatial.py` | 17 | UTM 46N projection, Shapely geometry validation, overlap calculations |
| `test_synthetic_data.py` | 6 | Benchmark cohorts (401 CLEAR, 402 BLOCK, 403 REVIEW) data integrity |
| **Total** | **136** | **All passing ✅ (119 passed + 17 skipped when PostgreSQL is offline)** |

---

## 🎨 Tech Stack

```mermaid
flowchart LR
    subgraph Frontend
        A["Chrome MV3 Extension"]
        B["Leaflet.js 2D GIS"]
        C["Vanilla JS Components"]
        D["Design Tokens & i18n"]
    end

    subgraph Backend
        E["FastAPI 0.115"]
        F["Pydantic v2"]
        G["PyJWT (HS256 Auth)"]
        H["Uvicorn ASGI"]
    end

    subgraph Geospatial
        I["PostGIS 3.4 (EPSG:32646)"]
        J["GeoAlchemy2 0.17"]
        K["Shapely 2.1 & PyProj 3.7"]
    end

    subgraph Database
        L["PostgreSQL 16"]
        M["SQLAlchemy 2.0 ORM"]
        N["Alembic Migrations"]
        O["Docker Compose"]
    end

    subgraph Security
        P["Ed25519 Signatures"]
        Q["SHA-256 Hash Chain"]
        R["DB Immutability Triggers"]
    end

    Frontend --> Backend --> Geospatial --> Database --> Security

    style Frontend fill:#DBEAFE,stroke:#3B82F6,color:#000
    style Backend fill:#D1FAE5,stroke:#10B981,color:#000
    style Geospatial fill:#EDE9FE,stroke:#8B5CF6,color:#000
    style Database fill:#FEF3C7,stroke:#F59E0B,color:#000
    style Security fill:#FEE2E2,stroke:#EF4444,color:#000
```

---

## ⚠️ Known Limitations

- **Synthetic Benchmark Data**: All demonstration cohorts (401 CLEAR, 402 BLOCK, 403 REVIEW) use synthetic ground-truth data in `naksha/data/`. No live government land record database is connected.
- **Simulated Officer Registry**: Identity verification verifies against seeded records in the `officers` table. Real-world deployment requires integration with government Identity and Access Management (e.g., National ID verification or Land Ministry SSO).
- **Mock Portal Integration**: Data flow is demonstrated via local mock portals (`/portals/ld-tax`, `/portals/e-mutation`) that simulate DOM structures rather than production ministerial web applications.
- **Statutory References**: Legal references returned by rules currently default to `TODO: verify with legal source` notices pending formal review by legal counsel against the latest Bangladesh Land Management Manual and Gazette notifications.
- **Jurisdictional Boundaries**: Officer jurisdictional permissions are enforced at Upazila/Union level based on session claims, pending the implementation of official digital administrative boundary shapefiles.

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