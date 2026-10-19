"""Database Seeding Module for NAKSHA Spatial Intelligence Engine."""
import uuid
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2.elements import WKTElement

from naksha.core.config import get_settings
from naksha.database.pg_models import (
    CanonicalParcelPG,
    AgencyRecordPG,
    SurveyLayerPG,
    RestrictedZonePG,
    OfficerPG,
    TaxPaymentPG,
    LienPG,
)
from naksha.data.synthetic import generate_synthetic_records
from naksha.data.synthetic_spatial import (
    DEED_CLAIM_402_COORDS,
    DLRS_BS_402_COORDS,
    CS_DAG_88_COORDS,
    KHAS_CANAL_COORDS,
    NEIGHBOR_401_COORDS,
    NEIGHBOR_403_COORDS,
    calculate_polygon_area,
)
from naksha.api.routes import SEEDED_OFFICER_REGISTRY

NAMESPACE_NAKSHA = uuid.uuid5(uuid.NAMESPACE_DNS, "naksha.gov.bd")


def make_deterministic_uuid(category: str, *keys: Any) -> uuid.UUID:
    """Generate a reproducible UUIDv5 for idempotent database seeding."""
    key_str = ":".join(str(k) for k in keys)
    return uuid.uuid5(NAMESPACE_NAKSHA, f"{category}:{key_str}")


def coords_to_wkt(coords: list) -> str:
    """Convert coordinate ring [[[x, y], ...]] to WKT Polygon."""
    ring = coords[0]
    points = [f"{pt[0]} {pt[1]}" for pt in ring]
    return f"POLYGON(({', '.join(points)}))"


def check_seed_safety(db_url: str, yes: bool = False) -> None:
    """Enforce strict environment and database safety checks before seeding."""
    settings = get_settings()
    env = (settings.environment or "").strip().lower()
    if env in ("production", "prod"):
        raise RuntimeError("Seeding is strictly forbidden in production environment.")

    parsed = make_url(db_url)
    db_name = parsed.database or ""
    if not (db_name.endswith("_test") or db_name.endswith("_dev")) and not yes:
        raise RuntimeError(
            f"Database '{db_name}' does not end with '_test' or '_dev'. "
            "Pass --yes to confirm seeding against this database."
        )


def seed_postgres(target_url: str, yes: bool = False) -> Dict[str, int]:
    """Idempotently seed PostgreSQL with synthetic cohorts, layers, taxes, liens, and officers."""
    check_seed_safety(target_url, yes=yes)

    engine = create_engine(target_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    counts = {
        "parcels": 0,
        "restricted_zones": 0,
        "survey_layers": 0,
        "tax_payments": 0,
        "liens": 0,
        "officers": 0,
        "agency_records": 0,
    }

    try:
        # 1. Canonical Parcels (401, 402, 403)
        # 402 gets DEED_CLAIM_402_COORDS to demonstrate Khas canal conflict
        parcel_definitions = [
            {
                "dag": "401",
                "khatian": "88",
                "coords": NEIGHBOR_401_COORDS,
            },
            {
                "dag": "402",
                "khatian": "120",
                "coords": DEED_CLAIM_402_COORDS,
            },
            {
                "dag": "403",
                "khatian": "125",
                "coords": NEIGHBOR_403_COORDS,
            },
        ]

        parcel_id_map: Dict[str, uuid.UUID] = {}
        for pdef in parcel_definitions:
            dag = pdef["dag"]
            p_id = make_deterministic_uuid("parcel", "Kashimpur", dag)
            parcel_id_map[dag] = p_id
            wkt_geom = coords_to_wkt(pdef["coords"])

            stmt = insert(CanonicalParcelPG).values(
                id=p_id,
                mouza="Kashimpur",
                dag_number=dag,
                khatian_number=pdef["khatian"],
                jl_number="28",
                upazila="Gazipur Sadar",
                district="Gazipur",
                status="active",
                geometry=WKTElement(wkt_geom, srid=4326),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[CanonicalParcelPG.id],
                set_={
                    "khatian_number": stmt.excluded.khatian_number,
                    "geometry": stmt.excluded.geometry,
                    "status": stmt.excluded.status,
                },
            )
            session.execute(stmt)
            counts["parcels"] += 1

        # 2. Restricted Zones (Government Khas Canal)
        canal_id = make_deterministic_uuid("restricted_zone", "canal", "কাশিমপুর সরকারি নিষ্কাশন খাল")
        canal_wkt = coords_to_wkt(KHAS_CANAL_COORDS)
        rz_stmt = insert(RestrictedZonePG).values(
            id=canal_id,
            name="কাশিমপুর সরকারি নিষ্কাশন খাল",
            zone_type="canal",
            source="DLRS Gazette",
            geometry=WKTElement(canal_wkt, srid=4326),
        )
        rz_stmt = rz_stmt.on_conflict_do_update(
            index_elements=[RestrictedZonePG.id],
            set_={
                "geometry": rz_stmt.excluded.geometry,
                "source": rz_stmt.excluded.source,
            },
        )
        session.execute(rz_stmt)
        counts["restricted_zones"] += 1

        # 3. Survey Layers
        cs_88_wkt = coords_to_wkt(CS_DAG_88_COORDS)
        cs_88_dec, _ = calculate_polygon_area({"type": "Polygon", "coordinates": CS_DAG_88_COORDS})

        # Add ancestral and ground-truth survey layers
        survey_layer_defs = [
            # Parcel 402 layers
            {"dag": "402", "era": "CS", "type": "ANCESTRAL_FOOTPRINT", "coords": CS_DAG_88_COORDS, "dec": cs_88_dec},
            {"dag": "402", "era": "BS", "type": "DEED_CLAIM", "coords": DEED_CLAIM_402_COORDS, "dec": 6.00},
            {"dag": "402", "era": "BS", "type": "GROUND_TRUTH", "coords": DLRS_BS_402_COORDS, "dec": 5.10},
            # Parcel 401 layers
            {"dag": "401", "era": "CS", "type": "ANCESTRAL_FOOTPRINT", "coords": CS_DAG_88_COORDS, "dec": cs_88_dec},
            {"dag": "401", "era": "BS", "type": "GROUND_TRUTH", "coords": NEIGHBOR_401_COORDS, "dec": 4.37},
            # Parcel 403 layers
            {"dag": "403", "era": "CS", "type": "ANCESTRAL_FOOTPRINT", "coords": CS_DAG_88_COORDS, "dec": cs_88_dec},
            {"dag": "403", "era": "BS", "type": "GROUND_TRUTH", "coords": NEIGHBOR_403_COORDS, "dec": 5.53},
        ]

        for sdef in survey_layer_defs:
            p_id = parcel_id_map[sdef["dag"]]
            sl_id = make_deterministic_uuid("survey_layer", str(p_id), sdef["era"], sdef["type"])
            sl_wkt = coords_to_wkt(sdef["coords"])

            sl_stmt = insert(SurveyLayerPG).values(
                id=sl_id,
                parcel_id=p_id,
                survey_era=sdef["era"],
                layer_type=sdef["type"],
                area_decimals=sdef["dec"],
                geometry=WKTElement(sl_wkt, srid=4326),
            )
            sl_stmt = sl_stmt.on_conflict_do_update(
                index_elements=[SurveyLayerPG.id],
                set_={
                    "area_decimals": sl_stmt.excluded.area_decimals,
                    "geometry": sl_stmt.excluded.geometry,
                },
            )
            session.execute(sl_stmt)
            counts["survey_layers"] += 1

        # 4. Tax Payments
        tax_defs = [
            {"dag": "401", "year": "2023-2024", "amount": 1500.00, "status": "paid", "payer": "মোঃ রহিম শেখ"},
            {"dag": "402", "year": "2023-2024", "amount": 1800.00, "status": "paid", "payer": "মোঃ আব্দুল করিম"},
            {"dag": "403", "year": "2023-2024", "amount": 2200.00, "status": "overdue", "payer": "অজ্ঞাত করদাতা"},
        ]
        for tdef in tax_defs:
            p_id = parcel_id_map[tdef["dag"]]
            t_id = make_deterministic_uuid("tax_payment", str(p_id), tdef["year"])
            t_stmt = insert(TaxPaymentPG).values(
                id=t_id,
                parcel_id=p_id,
                fiscal_year=tdef["year"],
                amount=tdef["amount"],
                status=tdef["status"],
                payer_name=tdef["payer"],
            )
            t_stmt = t_stmt.on_conflict_do_update(
                index_elements=[TaxPaymentPG.id],
                set_={
                    "amount": t_stmt.excluded.amount,
                    "status": t_stmt.excluded.status,
                    "payer_name": t_stmt.excluded.payer_name,
                },
            )
            session.execute(t_stmt)
            counts["tax_payments"] += 1

        # 5. Liens
        lien_defs = [
            {"dag": "402", "type": "mortgage", "holder": "Sonali Bank PLC", "status": "discharged"},
            {"dag": "403", "type": "freeze", "holder": "AC Land Office", "status": "pending"},
        ]
        for ldef in lien_defs:
            p_id = parcel_id_map[ldef["dag"]]
            l_id = make_deterministic_uuid("lien", str(p_id), ldef["holder"], ldef["type"])
            l_stmt = insert(LienPG).values(
                id=l_id,
                parcel_id=p_id,
                lien_type=ldef["type"],
                holder=ldef["holder"],
                status=ldef["status"],
            )
            l_stmt = l_stmt.on_conflict_do_update(
                index_elements=[LienPG.id],
                set_={
                    "status": l_stmt.excluded.status,
                },
            )
            session.execute(l_stmt)
            counts["liens"] += 1

        # 6. Officers (Migrate active officers from SEEDED_OFFICER_REGISTRY)
        for off_id, oprofile in SEEDED_OFFICER_REGISTRY.items():
            o_uuid = make_deterministic_uuid("officer", off_id)
            o_stmt = insert(OfficerPG).values(
                id=o_uuid,
                officer_id=off_id,
                name=oprofile["name"],
                designation=oprofile["designation"],
                role=oprofile["role"],
                jurisdiction=oprofile["jurisdiction"],
                office=oprofile["office"],
                is_active=oprofile.get("trusted", True),
            )
            o_stmt = o_stmt.on_conflict_do_update(
                index_elements=[OfficerPG.id],
                set_={
                    "name": o_stmt.excluded.name,
                    "designation": o_stmt.excluded.designation,
                    "role": o_stmt.excluded.role,
                    "jurisdiction": o_stmt.excluded.jurisdiction,
                    "office": o_stmt.excluded.office,
                    "is_active": o_stmt.excluded.is_active,
                },
            )
            session.execute(o_stmt)
            counts["officers"] += 1

        # 7. Agency Records (Synthetic Benchmark Cohort)
        synthetic_records = generate_synthetic_records()
        for rec in synthetic_records:
            rec_agency = rec.source.agency.value if rec.source.agency else "unknown"
            rec_source_id = rec.source.source_record_id or rec.id
            ar_uuid = make_deterministic_uuid("agency_record", rec_agency, rec_source_id)

            # Link to canonical parcel if matching dag
            matched_p_id = None
            if rec.dag_number and rec.dag_number.normalized_value in parcel_id_map:
                matched_p_id = parcel_id_map[rec.dag_number.normalized_value]

            raw_payload = rec.model_dump(mode="json")
            normalized_fields = {
                "dag_number": rec.dag_number.normalized_value if rec.dag_number else None,
                "khatian_number": rec.khatian_number.normalized_value if rec.khatian_number else None,
                "mouza": rec.mouza.normalized_value if rec.mouza else None,
                "owner_name": rec.owner_name.normalized_value if rec.owner_name else None,
                "area_decimals": rec.area_in_decimals,
            }

            ar_stmt = insert(AgencyRecordPG).values(
                id=ar_uuid,
                parcel_id=matched_p_id,
                agency=rec_agency,
                source_record_id=rec_source_id,
                document_type=rec.source.document_type or "Unknown",
                raw_payload=raw_payload,
                normalized_fields=normalized_fields,
                extraction_confidence=rec.dag_number.confidence if rec.dag_number else 1.0,
            )
            ar_stmt = ar_stmt.on_conflict_do_update(
                index_elements=[AgencyRecordPG.id],
                set_={
                    "parcel_id": ar_stmt.excluded.parcel_id,
                    "raw_payload": ar_stmt.excluded.raw_payload,
                    "normalized_fields": ar_stmt.excluded.normalized_fields,
                    "extraction_confidence": ar_stmt.excluded.extraction_confidence,
                },
            )
            session.execute(ar_stmt)
            counts["agency_records"] += 1

        session.commit()

        # 8. Seed Trust Ledger Benchmark Blocks if only Genesis or empty
        from naksha.services.ledger import TrustLedger
        ledger = TrustLedger(database_url=target_url)
        existing_entries = ledger.get_entries(limit=100)
        counts["ledger_entries"] = len(existing_entries)
        if len(existing_entries) <= 1:
            p401 = parcel_id_map.get("401")
            p402 = parcel_id_map.get("402")
            p403 = parcel_id_map.get("403")
            ledger.record_verification(
                event_type="ACCESS_GRANTED",
                canonical_parcel_id=None,
                dag_number=None,
                mouza="কাশিমপুর",
                verdict="CLEAR",
                cited_records=["REGISTRY-MATCH:UL-2024-KSH"],
                officer_id="UL-2024-KSH",
            )
            ledger.record_verification(
                event_type="VERIFICATION_VERDICT",
                canonical_parcel_id=str(p401) if p401 else None,
                dag_number="401",
                mouza="কাশিমপুর",
                verdict="CLEAR",
                cited_records=["DEED-2024-401", "MUT-2024-401"],
                officer_id="UL-2024-KSH",
            )
            ledger.record_verification(
                event_type="ACCESS_DENIED",
                canonical_parcel_id=None,
                dag_number=None,
                mouza="Unknown",
                verdict="DENIED",
                cited_records=["UNKNOWN_OFFICER"],
                officer_id="EXT-999-HACK",
            )
            ledger.record_verification(
                event_type="VERIFICATION_VERDICT",
                canonical_parcel_id=str(p403) if p403 else None,
                dag_number="403",
                mouza="কাশিমপুর",
                verdict="REVIEW",
                cited_records=["DEED-2024-403", "TAX-ARREARS-3YR"],
                officer_id="UL-2024-KSH",
            )
            ledger.record_verification(
                event_type="VERIFICATION_VERDICT",
                canonical_parcel_id=str(p402) if p402 else None,
                dag_number="402",
                mouza="কাশিমপুর",
                verdict="BLOCK",
                cited_records=["KHAS-CANAL-OVERLAP-0.9DEC", "DLRS-BS-402"],
                officer_id="UL-2024-KSH",
            )
            counts["ledger_entries"] = len(ledger.get_entries(limit=100))

        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
