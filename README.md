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

## 🏛️ System Architecture

NAKSHA operates across five modular layers:

- **Layer 1: Agency Adapter Mesh**: Async, read-only connectors for Sub-Registry, AC Land, LD Tax, and DLRS (REST, CDC, batch).
- **Layer 2: Identity & Lineage Engine**: Canonical UUIDv7 mapping, CS→SA→RS→BS genealogical DAG, salted HMAC for NID privacy, and Bangla phonetic name matching.
- **Layer 3: Spatial Integrity Engine (PostGIS 3.4)**: Metric calculations in UTM 46N (`EPSG:32646`), polygon validation, conflict zone calculation (Khas canal/wetland overlaps, ±0.2 dec area tolerances).
- **Layer 4: Deterministic Rule Engine**: Statutory validation logic returning explainable verdicts with cited legal/record evidence:
  - `RULE_UNMUTATED_DEED`: Detects unmutated deeds registered >30 days ago (double-selling hazard).
  - `RULE_TAX_OWNER_MISMATCH`: Flags tax payments tendered by non-owners.
  - `RULE_CLASS_CONFLICT`: Detects discrepancy between khatian class (e.g. *Nal*) and tax assessment (e.g. *Viti*).
  - `RULE_ACQUISITION_OR_MORTGAGE_LOCK`: Blocks transfers with active bank liens or DC acquisition notices.
  - `RULE_GEOMETRIC_OVERLAP`: Flags Khas/boundary encroachments or paper area inflation.
- **Layer 5: Trust Ledger**: Cryptographically sealed audit log with hash chains and daily Merkle root generation.

---

## 🧪 Synthetic Demonstration Federation

In adherence to data privacy standards and hackathon requirements, NAKSHA uses **no real citizen PII, live government databases, or actual land records**.

All demonstrations operate against a deterministic synthetic data generator (`seed_synthetic.py`) covering four benchmark scenarios:
1. **CLEAR** — Clean parcel with continuous CS→BS lineage, synchronized mutation and tax, matching 6.0 dec polygon.
2. **BLOCK** — Unmutated double-sale hazard (prior deed registered 124 days ago with no mutation).
3. **REVIEW** — Adverse possession attempt (LD Tax paid by unrelated individual; Nal vs. Viti class discrepancy).
4. **BLOCK** — Spatial encroachment (6.0 dec deed claim vs. 5.1 dec polygon crossing a public Khas canal strip).

---

## 📂 Repository Structure

```text
naksha/
├── .gitignore              # Ignores Python, Node, caches, secrets, and local databases
├── .env.example            # Environment configuration template
├── LICENSE                 # MIT License
├── README.md               # Project overview and specifications
└── docs/
    ├── Naksha_Concept_Note.pdf   # Hackathon concept note
    └── ROADMAP.md                # Multi-phase implementation roadmap
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