# NAKSHA (নকশা) — Implementation Roadmap
### LandTech 2026 Innovation Hackathon

> **One parcel. One identity. Every land office looking at the same truth.**

---

## 1. Executive Summary

NAKSHA is a Government-to-Government (G2G) interoperability engine and zero-integration spatial overlay designed to solve land record fragmentation in Bangladesh without replacing legacy ministry systems.

By reconciling six disconnected agency keys into a single **Canonical Parcel UUID (UUIDv7)** and enforcing five deterministic statutory integrity rules in real time, NAKSHA enables officers across the Sub-Registry, AC Land (e-Mutation), Union Land Office (LD Tax), DLRS, DC Office, and commercial banks to detect hazards at the exact moment an action is initiated.

---

## 2. System Architecture Blueprint

```
+-------------------------------------------------------------------------------+
|                        OFFICER INTERACTION LAYER                              |
|   Sub-Registry Portal  |  e-Mutation Portal  |  LD Tax Portal  |  Acquisition |
|       [Chrome Extension Overlay: Side Panel (Manifest v3, Vanilla / React)]   |
+-------------------------------------------------------------------------------+
                                      | REST / WebSockets / MVT
                                      v
+-------------------------------------------------------------------------------+
|                       API GATEWAY & SECURITY LAYER                            |
|       FastAPI Gateway · RBAC / ABAC · OIDC/SSO Simulation · Session JWT       |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
|                          CORE BACKEND SERVICES                                |
|  L1: Agency Adapter Mesh  (FastAPI async connectors, CDC / batch pull / REST) |
|  L2: Identity & Lineage   (PostgreSQL 16: CS -> SA -> RS -> BS DAG, HMAC NID)|
|  L3: Spatial Integrity    (PostGIS 3.4: UTM 46N EPSG:32646, conflict polygons)|
|  L4: Rule Engine          (5 pure deterministic rules: CLEAR / REVIEW / BLOCK)|
|  L5: Trust Ledger         (Append-only SHA-256 hash-chain, Ed25519 signing)   |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
|                    SYNTHETIC FEDERATION DATA LAYER                            |
|       Isolated Agency Schemas: Sub-Registry · AC Land · LD Tax · DLRS        |
|            Deterministic Seeder: seed_synthetic.py (4 scenarios)             |
+-------------------------------------------------------------------------------+
```

---

## 3. The 5 Deterministic Statutory Rules

| Rule Identifier | Trigger Condition | Primary Hazard Prevented | Expected Verdict |
| :--- | :--- | :--- | :--- |
| `RULE_UNMUTATED_DEED` | Deed registered > 30 days prior with no active/approved mutation opened at AC Land. | Double-selling before title is recorded. | **BLOCK** |
| `RULE_TAX_OWNER_MISMATCH` | LD Tax tendered by person not in current mutated khatian or verified inheritance DAG. | Manufacturing adverse possession claims. | **REVIEW** |
| `RULE_CLASS_CONFLICT` | Khatian land class (e.g. agricultural *Nal*) contradicts LD Tax assessment class (e.g. commercial/homestead *Viti*). | Unauthorized land-use change & revenue evasion. | **REVIEW** |
| `RULE_ACQUISITION_OR_MORTGAGE_LOCK` | Active DC acquisition corridor notice or active commercial bank mortgage on parcel UUID. | Transfer of encumbered land / duplicate pledging. | **BLOCK** |
| `RULE_GEOMETRIC_OVERLAP` | Polygon boundary intersects Khas / waterbody / forest, adjacent plots, or paper claim exceeds survey area by > ±0.2 dec. | Encroachment on public land & paper area inflation. | **BLOCK** |

---

## 4. Implementation Phases & Milestones

### Phase 1: Environment, Data Schemas & Synthetic Federation
- [ ] Setup repository structure (`backend/`, `extension/`, `docs/`, `tests/`).
- [ ] Configure Python backend dependencies (`fastapi`, `pydantic`, `uvicorn`, `geopandas`, `shapely`, `psycopg`, `cryptography`).
- [ ] Build isolated SQLite / PostgreSQL schemas simulating the 4 agency silos:
  - `sub_registry` (deeds, parties, claimed areas)
  - `ac_land` (mutations, khatian status, approval logs)
  - `ld_tax` (holdings, payers, land classes, arrears)
  - `dlrs` (spatial polygons, survey eras CS/SA/RS/BS, Khas layers)
- [ ] Implement `seed_synthetic.py` providing the 4 canonical test parcels:
  1. **CLEAR**: Clean parcel with unbroken CS->BS lineage, matched tax & mutation, 6.0 dec survey.
  2. **BLOCK**: Unmutated double-sale hazard (deed registered 124 days ago without AC Land mutation).
  3. **REVIEW**: Adverse possession attempt (tax paid by stranger, Nal vs. Viti class discrepancy).
  4. **BLOCK**: Spatial encroachment (6.0 dec deed claim vs. 5.1 dec polygon overlapping Khas canal).

### Phase 2: Core Backend Engine & Verification Services
- [ ] **L1 Adapter Mesh**: Abstracted async adapters normalising agency data into canonical events.
- [ ] **L2 Identity & Lineage Engine**:
  - UUIDv7 parcel generator and identifier crosswalk table.
  - Survey lineage DAG (CS -> SA -> RS -> BS) with fractional share conservation checks.
  - Salted HMAC NID indexing (zero plaintext PII).
  - Bangla phonetic string matcher (honorific stripping, edit distance, confidence score).
- [ ] **L3 Spatial Integrity Engine**:
  - EPSG:4326 storage and metric calculations in UTM 46N (`EPSG:32646`).
  - Polygon validation (`ST_MakeValid`), area calculation (1 decimal = 40.4686 m²).
  - Overlap and conflict zone calculation (Khas canal, road buffer, neighboring plots).
  - GeoJSON / Vector Tile generation for client rendering.
- [ ] **L4 Rule Engine**:
  - Pure deterministic rule evaluator executing the 5 statutory rules.
  - Explanation generator returning structured findings with cited records.
- [ ] **L5 Trust Ledger**:
  - Cryptographic append-only chain (SHA-256 previous-hash linkage).
  - Ed25519 digital signature per ledger entry.
  - Ledger verification utility detecting any tampering or broken chains.

### Phase 3: Zero-Integration Chrome Extension Overlay
- [ ] Manifest v3 Chrome extension with content script and side panel UI.
- [ ] Portal Context Detector:
  - Regex & DOM scrapers detecting deed entry, e-Mutation, and LD Tax inputs.
  - Manual fallback search bar (by Mouza + Dag, Deed No., or Parcel UUID).
- [ ] Side Panel Presentation:
  - Header: Officer auth badge, parcel identity badge, clearance verdict pill (**CLEAR / REVIEW / BLOCK**).
  - Detailed Tabs:
    - **Overview**: Finding summaries and recommended actions.
    - **Land History**: Visual CS->SA->RS->BS genealogical DAG with fractional shares.
    - **GIS Map**: 4-layer interactive map (Ancestral CS footprint, Deed claim, DLRS surveyed boundary, PostGIS conflict polygon).
    - **Tax Map**: Holding status of target parcel and neighbouring plots.
    - **Liens & Locks**: Bank mortgage and DC acquisition status.
    - **Audit Trail**: Real-time hash-chained query log.

### Phase 4: Testing, Performance & Hackathon Deliverables
- [ ] End-to-end integration tests covering all 4 synthetic scenarios.
- [ ] Performance benchmarking targeting sub-second p95 verdict latency.
- [ ] Interactive mock agency portals for realistic hackathon presentation.
- [ ] Complete documentation, pitch deck alignment, and demonstration runbook.

---

## 5. Team & Governance

- **Team Leader**: Mahadi Rahman Jihad (ID: 251-15-008, CSE)
- **Team Member**: Tartib Kaiser Munna (ID: 251-15-848, CSE)
- **Faculty Mentor**: Abdullah Al-Amin (Lecturer, CSE)
- **Industry Support Mentor**: Farvez Rakib (CSE-TECH)
