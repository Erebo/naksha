"""Database Initialization and Controlled Seeding for NAKSHA."""
import json
from shapely.geometry import shape
from naksha.database.connection import engine, Base, SessionLocal
from naksha.database.models import (
    CanonicalParcelModel,
    SurveyHistoryModel,
    AgencyRecordModel,
    AuditLedgerModel,
)
from naksha.data.synthetic import generate_synthetic_records
from naksha.data.synthetic_spatial import (
    DLRS_BS_402_COORDS,
    NEIGHBOR_401_COORDS,
    NEIGHBOR_403_COORDS,
    get_synthetic_parcel_layers,
)
from naksha.services.ledger import audit_ledger


def init_database(drop_existing: bool = False):
    """Initializes tables and seeds canonical parcels, survey layers, and records."""
    if drop_existing:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # Check if already seeded
        if session.query(CanonicalParcelModel).count() == 0:
            seed_canonical_parcels(session)
            seed_survey_layers(session)
            seed_agency_records(session)
            seed_audit_ledger(session)
            session.commit()
            print("[NAKSHA Database] Initialized and seeded successfully.")
        else:
            print("[NAKSHA Database] Database already initialized.")
    except Exception as e:
        session.rollback()
        print(f"[NAKSHA Database] Error seeding database: {e}")
        raise
    finally:
        session.close()


def seed_canonical_parcels(session):
    """Seeds canonical benchmark parcels: BS-401, BS-402, BS-403."""
    parcels = [
        CanonicalParcelModel(
            id="par-8f92-bd04-syn",
            dag_number="402",
            khatian_number="120",
            mouza="কাশিমপুর (Kashimpur)",
            jl_number="28",
            upazila="Gazipur Sadar",
            district="Gazipur",
            area_decimals=5.10,
            geometry_geojson=json.dumps({"type": "Polygon", "coordinates": DLRS_BS_402_COORDS}),
            geometry_wkt=shape({"type": "Polygon", "coordinates": DLRS_BS_402_COORDS}).wkt,
            survey_era="BS",
            status="active",
        ),
        CanonicalParcelModel(
            id="par-401-west-syn",
            dag_number="401",
            khatian_number="88",
            mouza="কাশিমপুর (Kashimpur)",
            jl_number="28",
            upazila="Gazipur Sadar",
            district="Gazipur",
            area_decimals=4.37,
            geometry_geojson=json.dumps({"type": "Polygon", "coordinates": NEIGHBOR_401_COORDS}),
            geometry_wkt=shape({"type": "Polygon", "coordinates": NEIGHBOR_401_COORDS}).wkt,
            survey_era="BS",
            status="active",
        ),
        CanonicalParcelModel(
            id="par-403-south-syn",
            dag_number="403",
            khatian_number="125",
            mouza="কাশিমপুর (Kashimpur)",
            jl_number="28",
            upazila="Gazipur Sadar",
            district="Gazipur",
            area_decimals=5.53,
            geometry_geojson=json.dumps({"type": "Polygon", "coordinates": NEIGHBOR_403_COORDS}),
            geometry_wkt=shape({"type": "Polygon", "coordinates": NEIGHBOR_403_COORDS}).wkt,
            survey_era="BS",
            status="active",
        ),
    ]
    session.add_all(parcels)
    session.flush()


def seed_survey_layers(session):
    """Seeds multi-era survey snapshots for parcels 401, 402, and 403."""
    parcel_ids = ["par-8f92-bd04-syn", "par-401-west-syn", "par-403-south-syn"]
    for pid in parcel_ids:
        layers = get_synthetic_parcel_layers(pid)
        for idx, snap in enumerate(layers):
            geom_dict = snap.geometry.model_dump()
            wkt_str = shape(geom_dict).wkt
            model = SurveyHistoryModel(
                id=f"{pid}-lyr-{idx}-{snap.layer_type.value}",
                parcel_id=pid,
                survey_era=snap.survey_era.value if snap.survey_era else "BS",
                layer_type=snap.layer_type.value,
                layer_name=snap.layer_name,
                geometry_geojson=json.dumps(geom_dict),
                geometry_wkt=wkt_str,
                area_decimals=snap.properties.get("calculated_area_decimals"),
                properties_json=json.dumps(snap.properties or {}),
            )
            session.add(model)
    session.flush()


def seed_agency_records(session):
    """Seeds normalized synthetic records from all participating government agencies."""
    records = generate_synthetic_records()
    for rec in records:
        model = AgencyRecordModel(
            id=rec.id,
            agency=rec.source.agency.value if rec.source.agency else "unknown",
            document_type=rec.source.document_type or "Unknown",
            source_record_id=rec.source.source_record_id or rec.id,
            canonical_parcel_id=rec.canonical_parcel_id,
            dag_number=rec.dag_number.normalized_value if rec.dag_number else None,
            khatian_number=rec.khatian_number.normalized_value if rec.khatian_number else None,
            mouza=rec.mouza.normalized_value if rec.mouza else None,
            owner_name=rec.owner_name.normalized_value if rec.owner_name else None,
            area_decimals=rec.area_in_decimals,
            land_class=rec.land_class.value if rec.land_class else None,
            notes=rec.source.notes,
            payload_json=rec.model_dump_json(),
        )
        session.add(model)
    session.flush()


def seed_audit_ledger(session):
    """Seeds the genesis block and audit ledger chain into persistent storage."""
    for entry in audit_ledger._chain:
        model = AuditLedgerModel(
            entry_index=entry.index,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            canonical_parcel_id=entry.canonical_parcel_id,
            dag_number=entry.dag_number,
            mouza=entry.mouza,
            officer_id=entry.officer_id,
            verdict=entry.verdict,
            cited_records_json=json.dumps(entry.cited_records),
            payload_hash=entry.payload_hash,
            previous_hash=entry.previous_hash,
            entry_hash=entry.entry_hash,
            signature_ed25519=entry.signature_ed25519,
            public_key_ed25519=entry.public_key_ed25519,
        )
        session.add(model)
    session.flush()


if __name__ == "__main__":
    init_database()
