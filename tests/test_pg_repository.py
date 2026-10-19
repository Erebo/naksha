"""Tests for PostgreSQL Record and Spatial Repositories and Seeding.

Marked with custom marker `postgres`. Automatically skips if NAKSHA_TEST_DATABASE_URL
is unset or unreachable. Refuses to run against any DB name not ending with '_test'.
"""
import os
import uuid
import argparse
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

from naksha.core.config import get_settings
from naksha.repository.pg_repository import (
    PostgresRecordRepository,
    normalize_dag_key,
    normalize_mouza_key,
)
from naksha.database.repository import SQLAlchemyRecordRepository
from naksha.database.pg_models import CanonicalParcelPG, OfficerPG
from naksha.cli.seed import seed_postgres, make_deterministic_uuid
from naksha.spatial.engine import calculate_overlap
from naksha.data.synthetic_spatial import DEED_CLAIM_402_COORDS, KHAS_CANAL_COORDS
from naksha.api.app import app

pytestmark = [pytest.mark.postgres]


def get_verified_test_db_url() -> str:
    """Retrieve test DB URL, enforcing safety check that DB name ends with '_test'."""
    settings = get_settings()
    url = os.environ.get("NAKSHA_TEST_DATABASE_URL")
    if url is None:
        url = settings.test_database_url
    if not url or url.strip().lower() in ("none", "disabled", "false", "0"):
        pytest.skip("NAKSHA_TEST_DATABASE_URL is not configured; skipping postgres tests")

    parsed = make_url(url)
    db_name = parsed.database or ""
    if not db_name.endswith("_test"):
        pytest.skip(
            f"Refusing to run tests against '{db_name}': database name must end with '_test' for safety"
        )

    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL test database unreachable at {url}: {exc}")
    finally:
        engine.dispose()

    return url


@pytest.fixture(scope="module")
def pg_migrated_engine():
    """Ensure Alembic migrations are at head for the test database."""
    url = get_verified_test_db_url()
    cfg = Config("alembic.ini")
    cfg.cmd_opts = argparse.Namespace(x=["db=test"])
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def repo_fixture(pg_migrated_engine):
    """Provide a seeded Postgres repository and clean up tables after each test."""
    url = get_verified_test_db_url()
    seed_postgres(url, yes=True)

    Session = sessionmaker(bind=pg_migrated_engine)
    session = Session()
    repo = PostgresRecordRepository(session=session)

    try:
        yield repo, session, url
    finally:
        session.rollback()
        session.close()
        # Clean up data after test to ensure isolation
        with pg_migrated_engine.connect() as conn:
            conn.execute(
                text(
                    "TRUNCATE TABLE canonical_parcels, agency_records, parcel_lineage, "
                    "survey_layers, restricted_zones, officers, tax_payments, liens CASCADE;"
                )
            )
            conn.commit()


def test_seed_idempotency(pg_migrated_engine):
    """Running seed twice creates zero new rows and keeps row counts identical."""
    url = get_verified_test_db_url()

    # First run
    counts1 = seed_postgres(url, yes=True)

    with pg_migrated_engine.connect() as conn:
        rows_run1 = {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            for table in [
                "canonical_parcels",
                "restricted_zones",
                "survey_layers",
                "tax_payments",
                "liens",
                "officers",
                "agency_records",
            ]
        }

    # Second run
    counts2 = seed_postgres(url, yes=True)

    with pg_migrated_engine.connect() as conn:
        rows_run2 = {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            for table in [
                "canonical_parcels",
                "restricted_zones",
                "survey_layers",
                "tax_payments",
                "liens",
                "officers",
                "agency_records",
            ]
        }

    assert rows_run1 == rows_run2, f"Row counts differed after second seed run: {rows_run1} vs {rows_run2}"
    assert rows_run1["canonical_parcels"] == 3
    assert rows_run1["restricted_zones"] == 1
    assert rows_run1["officers"] == 4

    # Clean up
    with pg_migrated_engine.connect() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE canonical_parcels, agency_records, parcel_lineage, "
                "survey_layers, restricted_zones, officers, tax_payments, liens CASCADE;"
            )
        )
        conn.commit()


def test_repository_parity(repo_fixture):
    """Verify list_records, count, pagination, and filtering match SQLite/SQLAlchemy behavior."""
    pg_repo, _, _ = repo_fixture
    sqlite_repo = SQLAlchemyRecordRepository()

    # 1. Total record count parity
    assert pg_repo.count() == sqlite_repo.count()

    # 2. Unfiltered list parity
    pg_all = pg_repo.list_records(limit=100)
    sqlite_all = sqlite_repo.list_records(limit=100)
    assert len(pg_all) == len(sqlite_all)

    # 3. Pagination offset parity
    pg_page = pg_repo.list_records(limit=2, offset=1)
    sqlite_page = sqlite_repo.list_records(limit=2, offset=1)
    assert len(pg_page) == 2
    assert len(sqlite_page) == 2

    # 4. Filter by agency parity
    from naksha.models.enums import AgencyType
    pg_sub = pg_repo.list_records(agency=AgencyType.SUB_REGISTRY)
    sqlite_sub = sqlite_repo.list_records(agency=AgencyType.SUB_REGISTRY)
    assert len(pg_sub) == len(sqlite_sub)

    # 5. Filter by dag parity
    pg_dag402 = pg_repo.list_records(dag="402")
    sqlite_dag402 = sqlite_repo.list_records(dag="402")
    assert len(pg_dag402) == len(sqlite_dag402)
    assert len(pg_dag402) > 0


def test_parcel_resolver(repo_fixture):
    """Test parcel resolution with Bengali/English digits and strict whole-token matching."""
    pg_repo, _, _ = repo_fixture

    # Valid Bengali and English queries resolve to 402
    p_bn = pg_repo.resolve_parcel("Kashimpur", "৪০২")
    assert p_bn is not None
    assert p_bn.dag_number == "402"

    p_en = pg_repo.resolve_parcel("Kashimpur", "402")
    assert p_en is not None
    assert p_en.dag_number == "402"

    p_spaced = pg_repo.resolve_parcel("Kashimpur", " 402 ")
    assert p_spaced is not None
    assert p_spaced.dag_number == "402"

    p_bilingual_mouza = pg_repo.resolve_parcel("কাশিমপুর (Kashimpur)", "৪০২")
    assert p_bilingual_mouza is not None
    assert p_bilingual_mouza.dag_number == "402"

    # Unknown or non-matching inputs must return None (no substring matching)
    assert pg_repo.resolve_parcel("Kashimpur", "1402") is None
    assert pg_repo.resolve_parcel("Kashimpur", "4020") is None
    assert pg_repo.resolve_parcel("Kashimpur", "x") is None
    assert pg_repo.resolve_parcel("Kashimpur", "") is None
    assert pg_repo.resolve_parcel("UnknownMouza", "402") is None


def test_khas_canal_intersection(repo_fixture):
    """Test PostGIS UTM 46N Khas canal intersection area and parity with calculate_overlap."""
    pg_repo, _, _ = repo_fixture

    p402 = pg_repo.resolve_parcel("Kashimpur", "402")
    assert p402 is not None

    zones_402 = pg_repo.get_restricted_zones_intersecting(p402.id)
    assert len(zones_402) == 1
    zone, area_dec = zones_402[0]
    assert zone.zone_type == "canal"
    # Intersection for 402 is ~0.90 decimals
    assert 0.89 <= area_dec <= 0.91

    # Parity test against naksha.spatial.engine.calculate_overlap
    expected_dec, _ = calculate_overlap(
        {"type": "Polygon", "coordinates": DEED_CLAIM_402_COORDS},
        {"type": "Polygon", "coordinates": KHAS_CANAL_COORDS},
    )[:2]
    assert abs(area_dec - expected_dec) < 0.01

    # 401 and 403 must return an EMPTY LIST []
    p401 = pg_repo.resolve_parcel("Kashimpur", "401")
    assert p401 is not None
    zones_401 = pg_repo.get_restricted_zones_intersecting(p401.id)
    assert zones_401 == []

    p403 = pg_repo.resolve_parcel("Kashimpur", "403")
    assert p403 is not None
    zones_403 = pg_repo.get_restricted_zones_intersecting(p403.id)
    assert zones_403 == []


def test_neighbor_spatial_query(repo_fixture):
    """Test ST_DWithin neighbor query returns only parcels within metric radius."""
    pg_repo, session, _ = repo_fixture

    p402 = pg_repo.resolve_parcel("Kashimpur", "402")
    assert p402 is not None

    # Insert a distant parcel ~10 km away
    from geoalchemy2.elements import WKTElement
    distant_wkt = "POLYGON((90.450 23.990, 90.455 23.990, 90.455 23.995, 90.450 23.995, 90.450 23.990))"
    distant_p = CanonicalParcelPG(
        id=uuid.uuid4(),
        mouza="Kashimpur",
        dag_number="999",
        khatian_number="999",
        geometry=WKTElement(distant_wkt, srid=4326),
    )
    session.add(distant_p)
    session.commit()

    # Within 50m: 401 (west neighbor) and 403 (south neighbor) are adjacent; 999 is excluded
    neighbors_50m = pg_repo.get_neighbors(p402.id, radius_m=50.0)
    neighbor_dags = {n.dag_number for n in neighbors_50m}
    assert "401" in neighbor_dags
    assert "403" in neighbor_dags
    assert "402" not in neighbor_dags  # Target parcel excluded
    assert "999" not in neighbor_dags  # Distant parcel excluded

    # Within 15,000m: distant parcel is included
    neighbors_wide = pg_repo.get_neighbors(p402.id, radius_m=15000.0)
    wide_dags = {n.dag_number for n in neighbors_wide}
    assert "999" in wide_dags


def test_officer_lookup(repo_fixture, monkeypatch):
    """Test officer verification: active verified, inactive denied, unknown denied."""
    pg_repo, session, url = repo_fixture
    settings = get_settings()

    # 1. Repository-level officer query
    active_off = pg_repo.get_officer("UL-2024-KSH")
    assert active_off is not None
    assert active_off.is_active is True
    assert active_off.name == "মোঃ ফজলুর রহমান"

    # 2. Add an inactive test officer in test fixture only
    inact_uuid = uuid.uuid4()
    inactive_off = OfficerPG(
        id=inact_uuid,
        officer_id="INACT-TEST-01",
        name="নিষ্ক্রিয় কর্মকর্তা",
        designation="সহকারী কমিশনার (ভূমি)",
        role="ac_land",
        jurisdiction="গাজীপুর সদর",
        office="গাজীপুর সদর",
        is_active=False,
    )
    session.add(inactive_off)
    session.commit()

    inact_fetched = pg_repo.get_officer("INACT-TEST-01")
    assert inact_fetched is not None
    assert inact_fetched.is_active is False

    # 3. HTTP endpoint /auth/verify-officer with Postgres active
    from naksha.database.connection import get_db
    monkeypatch.setattr(settings, "database_url", url)
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)

        # Active officer verifies successfully
        res_active = client.post(
            "/auth/verify-officer",
            json={
                "officer_id": "UL-2024-KSH",
                "name": "মোঃ ফজলুর রহমান",
                "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
                "office": "কাশিমপুর, গাজীপুর সদর",
                "portal_origin": "http://localhost:8000",
            },
        )
        assert res_active.status_code == 200
        assert res_active.json()["status"] == "verified"
        assert "token" in res_active.json()

        # Inactive officer is denied
        res_inactive = client.post(
            "/auth/verify-officer",
            json={
                "officer_id": "INACT-TEST-01",
                "name": "নিষ্ক্রিয় কর্মকর্তা",
                "designation": "সহকারী কমিশনার (ভূমি)",
                "office": "গাজীপুর সদর",
                "portal_origin": "http://localhost:8000",
            },
        )
        assert res_inactive.status_code == 200
        assert res_inactive.json()["status"] == "denied"
        assert "নিষ্ক্রিয়" in res_inactive.json()["reason"]

        # Unknown officer is denied
        res_unknown = client.post(
            "/auth/verify-officer",
            json={
                "officer_id": "UNKNOWN-999",
                "name": "অজ্ঞাত ব্যক্তি",
                "designation": "সহকারী কমিশনার (ভূমি)",
                "office": "গাজীপুর সদর",
                "portal_origin": "http://localhost:8000",
            },
        )
        assert res_unknown.status_code == 200
        assert res_unknown.json()["status"] == "denied"
    finally:
        app.dependency_overrides.clear()


def test_seed_safety_checks(monkeypatch):
    """Seed refuses non-dev/non-test DB without --yes, and refuses in production even with --yes."""
    settings = get_settings()

    # 1. Refuses non-test / non-dev database without --yes
    with pytest.raises(RuntimeError, match="does not end with '_test' or '_dev'"):
        seed_postgres("postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_prod_corp", yes=False)

    # 2. Refuses always when environment is production, even with --yes=True
    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(RuntimeError, match="strictly forbidden in production"):
        seed_postgres("postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test", yes=True)
