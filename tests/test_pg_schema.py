"""Tests for PostgreSQL + PostGIS Schema, Constraints, and Spatial Operations.

Marked with custom marker `postgres`. Automatically skips if NAKSHA_TEST_DATABASE_URL
is unset or unreachable. Refuses to run against any DB name not ending with '_test'.
"""
import os
import uuid
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, DBAPIError
from geoalchemy2.elements import WKTElement
from alembic.config import Config
from alembic import command

from naksha.core.config import get_settings
from naksha.core.privacy import hash_identifier
from naksha.database.pg_models import (
    CanonicalParcelPG,
    AgencyRecordPG,
    ParcelLineagePG,
    SurveyLayerPG,
    RestrictedZonePG,
    OfficerPG,
    TaxPaymentPG,
    LienPG,
)

pytestmark = [pytest.mark.postgres]


def get_verified_test_db_url() -> str:
    """Retrieve test DB URL, enforcing safety check that DB name ends with '_test'."""
    settings = get_settings()
    url = settings.test_database_url or os.environ.get("NAKSHA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("NAKSHA_TEST_DATABASE_URL is not configured; skipping postgres tests")

    parsed = make_url(url)
    db_name = parsed.database or ""
    if not db_name.endswith("_test"):
        pytest.skip(
            f"Refusing to run tests against '{db_name}': database name must end with '_test' for safety"
        )

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL test database unreachable at {url}: {exc}")
    finally:
        engine.dispose()

    return url


import argparse

@pytest.fixture(scope="module")
def pg_migrated_engine():
    """Ensure Alembic migrations are at head for the test database."""
    url = get_verified_test_db_url()
    cfg = Config("alembic.ini")
    cfg.cmd_opts = argparse.Namespace(x=["db=test"])
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_migrated_engine):
    """Provide a transactional SQLAlchemy session with clean-up between tests."""
    Session = sessionmaker(bind=pg_migrated_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        # Truncate all tables between tests
        with pg_migrated_engine.connect() as conn:
            conn.execute(
                text(
                    "TRUNCATE TABLE canonical_parcels, agency_records, parcel_lineage, "
                    "survey_layers, restricted_zones, officers, tax_payments, liens CASCADE;"
                )
            )
            conn.commit()
        session.close()


def test_migration_creates_tables_and_extension(pg_migrated_engine):
    """Test that upgrade head creates all 8 PostGIS tables and the postgis extension."""
    inspector = inspect(pg_migrated_engine)
    tables = set(inspector.get_table_names())
    expected_tables = {
        "canonical_parcels",
        "agency_records",
        "parcel_lineage",
        "survey_layers",
        "restricted_zones",
        "officers",
        "tax_payments",
        "liens",
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    with pg_migrated_engine.connect() as conn:
        ext = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'postgis'")).scalar()
        assert ext == "postgis", "PostGIS extension is not installed"


def test_invalid_self_intersecting_polygon_rejected(pg_session):
    """Test that self-intersecting polygon is rejected by ST_IsValid CHECK constraint."""
    # Classic bowtie self-intersecting polygon
    bowtie_wkt = "POLYGON((0 0, 0 2, 2 0, 2 2, 0 0))"

    parcel = CanonicalParcelPG(
        mouza="Tejgaon",
        dag_number="401",
        khatian_number="120",
        jl_number="28",
        status="active",
        geometry=WKTElement(bowtie_wkt, srid=4326),
    )
    pg_session.add(parcel)

    with pytest.raises((IntegrityError, DBAPIError)) as exc_info:
        pg_session.commit()

    err_msg = str(exc_info.value).lower()
    assert "chk_parcels_geometry_valid" in err_msg or "check constraint" in err_msg


def test_unique_agency_and_source_record_id_enforced(pg_session):
    """Test that unique(agency, source_record_id) constraint is enforced."""
    rec1 = AgencyRecordPG(
        agency="AC_LAND",
        source_record_id="MUT-2026-999",
        document_type="mutation_record",
        raw_payload={"khatian": "120", "dag": "401"},
    )
    pg_session.add(rec1)
    pg_session.commit()

    rec2 = AgencyRecordPG(
        agency="AC_LAND",
        source_record_id="MUT-2026-999",
        document_type="duplicate_filing",
        raw_payload={"khatian": "120", "dag": "401"},
    )
    pg_session.add(rec2)

    with pytest.raises(IntegrityError) as exc_info:
        pg_session.commit()

    assert "uq_agency_records_agency_source_record_id" in str(exc_info.value)


def test_lineage_self_link_rejected(pg_session):
    """Test that lineage self-linking (parent == child) is rejected by CHECK constraint."""
    valid_wkt = "POLYGON((90.410 23.810, 90.415 23.810, 90.415 23.815, 90.410 23.815, 90.410 23.810))"
    parcel = CanonicalParcelPG(
        mouza="Tejgaon",
        dag_number="402",
        khatian_number="121",
        geometry=WKTElement(valid_wkt, srid=4326),
    )
    pg_session.add(parcel)
    pg_session.commit()

    # Attempt self-link
    lineage = ParcelLineagePG(
        parent_parcel_id=parcel.id,
        child_parcel_id=parcel.id,
        survey_era="RS",
        relation="subdivision",
    )
    pg_session.add(lineage)

    with pytest.raises(IntegrityError) as exc_info:
        pg_session.commit()

    assert "chk_parcel_lineage_no_self_link" in str(exc_info.value)


def test_spatial_query_intersects_and_area(pg_session):
    """Test ST_Intersects and ST_Area(geography) on inserted polygons."""
    wkt_p1 = "POLYGON((90.4100 23.8100, 90.4200 23.8100, 90.4200 23.8200, 90.4100 23.8200, 90.4100 23.8100))"
    wkt_p2 = "POLYGON((90.4150 23.8150, 90.4250 23.8150, 90.4250 23.8250, 90.4150 23.8250, 90.4150 23.8150))"

    p1 = CanonicalParcelPG(
        mouza="Dhanmondi",
        dag_number="101",
        khatian_number="50",
        geometry=WKTElement(wkt_p1, srid=4326),
    )
    p2 = CanonicalParcelPG(
        mouza="Dhanmondi",
        dag_number="102",
        khatian_number="51",
        geometry=WKTElement(wkt_p2, srid=4326),
    )
    pg_session.add_all([p1, p2])
    pg_session.commit()

    # Query intersection and area in geography (square meters)
    stmt = text("""
        SELECT 
            ST_Intersects(p1.geometry, p2.geometry) AS is_intersecting,
            ST_Area(p1.geometry::geography) AS area_sq_m
        FROM canonical_parcels p1, canonical_parcels p2
        WHERE p1.id = :id1 AND p2.id = :id2
    """)
    row = pg_session.execute(stmt, {"id1": p1.id, "id2": p2.id}).one()

    assert row.is_intersecting is True
    # ~0.01 deg by ~0.01 deg at 23.8N latitude is roughly 1.1 - 1.2 sq km (1.1e6 - 1.3e6 m^2)
    assert 1_000_000 < row.area_sq_m < 1_400_000


def test_downgrade_base_then_upgrade_head():
    """Test full downgrade to base and upgrade back to head on the test database."""
    url = get_verified_test_db_url()
    cfg = Config("alembic.ini")
    cfg.cmd_opts = argparse.Namespace(x=["db=test"])
    cfg.set_main_option("sqlalchemy.url", url)

    # Downgrade to base
    command.downgrade(cfg, "base")

    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        # Base schema has no application tables
        assert "canonical_parcels" not in tables
        assert "agency_records" not in tables
    finally:
        engine.dispose()

    # Upgrade back to head
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "canonical_parcels" in tables
        assert "agency_records" in tables
        assert "survey_layers" in tables
    finally:
        engine.dispose()


def test_hash_identifier_properties():
    """Test HMAC-SHA256 identifier hashing: deterministic, secret-dependent, never raw input."""
    raw_id = "19901234567890123"

    h1 = hash_identifier(raw_id, secret="secret-alpha")
    h2 = hash_identifier(raw_id, secret="secret-alpha")
    h3 = hash_identifier(raw_id, secret="secret-beta")

    # Deterministic with same secret
    assert h1 == h2
    # Distinct with different secrets
    assert h1 != h3
    # Never leaks or returns raw input
    assert h1 != raw_id
    assert raw_id not in h1
    # Standard 64-char hex digest (HMAC-SHA256)
    assert len(h1) == 64
    assert isinstance(h1, str)

    # Works with default configured secret
    h_default = hash_identifier(raw_id)
    assert len(h_default) == 64
    assert h_default != raw_id
