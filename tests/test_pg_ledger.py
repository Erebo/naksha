"""Tests for Persistent, Tamper-Evident Ledger on PostgreSQL.

Verifies:
1. Ledger chain survives an application restart.
2. Direct tampering / editing of any field is caught by cryptographic verification.
3. SQL UPDATE and DELETE operations are rejected by database triggers.
4. Concurrent appends serialize safely via row locking (SELECT ... FOR UPDATE) and maintain a valid chain.
5. Re-signed entries using an attacker / rogue key are caught by pinned public key verification.
6. Production startup validation requires a configured NAKSHA_LEDGER_PRIVATE_KEY.
"""
import os
import argparse
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, DatabaseError
from alembic.config import Config
from alembic import command
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import ValidationError

from naksha.core.config import Settings, get_settings, DEFAULT_DEV_LEDGER_KEY
from naksha.services.ledger import TrustLedger, LedgerEntry, format_timestamp

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
def clean_ledger_db(pg_migrated_engine):
    """Truncates ledger_entries before and after each test for test isolation."""
    url = get_verified_test_db_url()

    def _clean():
        with pg_migrated_engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE ledger_entries CASCADE;"))
            conn.commit()

    _clean()
    yield url
    _clean()


def test_pg_ledger_survives_app_restart(clean_ledger_db):
    """Chain entries persist across TrustLedger instance lifecycles (simulating restart)."""
    url = clean_ledger_db
    ledger1 = TrustLedger(database_url=url)

    # Append 3 verification records
    e1 = ledger1.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="401",
        mouza="কাশিমপুর",
        verdict="CLEAR",
        cited_records=["RS-401"],
        officer_id="UL-2024-KSH",
    )
    e2 = ledger1.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["RS-402-KHAS"],
        officer_id="UL-2024-KSH",
    )
    e3 = ledger1.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="403",
        mouza="কাশিমপুর",
        verdict="REVIEW",
        cited_records=["RS-403-BOUNDARY"],
        officer_id="UL-2024-KSH",
    )

    is_valid1, reason1 = ledger1.verify_integrity()
    assert is_valid1 is True
    assert reason1 is None

    # Simulate app restart by creating a new TrustLedger instance
    ledger2 = TrustLedger(database_url=url)
    entries = ledger2._chain
    assert len(entries) == 4  # genesis + 3 entries
    assert ledger2.latest_entry.index == 3
    assert ledger2.latest_entry.verdict == "REVIEW"
    assert ledger2.latest_entry.dag_number == "403"

    is_valid2, reason2 = ledger2.verify_integrity()
    assert is_valid2 is True
    assert reason2 is None


def test_pg_ledger_editing_field_is_detected(clean_ledger_db, pg_migrated_engine):
    """Direct field manipulation in PostgreSQL is detected by payload hash verification."""
    url = clean_ledger_db
    ledger = TrustLedger(database_url=url)

    ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["RS-402-KHAS"],
        officer_id="UL-2024-KSH",
    )

    # Disable trigger to simulate a database-level breach / unauthorized edit
    with pg_migrated_engine.connect() as conn:
        conn.execute(text("ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_entries_immutable;"))
        conn.execute(text("UPDATE ledger_entries SET verdict = 'CLEAR' WHERE entry_index = 1;"))
        conn.execute(text("ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_entries_immutable;"))
        conn.commit()

    is_valid, reason = ledger.verify_integrity()
    assert is_valid is False
    assert "Tampered block hash" in reason
    assert "payload mismatch" in reason


def test_pg_ledger_update_and_delete_rejected_by_trigger(clean_ledger_db, pg_migrated_engine):
    """Database trigger reject_ledger_tampering aborts any SQL UPDATE or DELETE."""
    url = clean_ledger_db
    ledger = TrustLedger(database_url=url)

    ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="401",
        mouza="কাশিমপুর",
        verdict="CLEAR",
        cited_records=["RS-401"],
    )

    # Test UPDATE rejection
    with pytest.raises(DBAPIError) as exc_update:
        with pg_migrated_engine.connect() as conn:
            conn.execute(text("UPDATE ledger_entries SET verdict = 'BLOCK' WHERE entry_index = 1;"))
            conn.commit()
    assert "Ledger entries are immutable and cannot be updated or deleted" in str(exc_update.value)

    # Test DELETE rejection
    with pytest.raises(DBAPIError) as exc_delete:
        with pg_migrated_engine.connect() as conn:
            conn.execute(text("DELETE FROM ledger_entries WHERE entry_index = 1;"))
            conn.commit()
    assert "Ledger entries are immutable and cannot be updated or deleted" in str(exc_delete.value)


def test_pg_ledger_concurrent_appends_keep_valid_chain(clean_ledger_db):
    """Concurrent append requests serialize properly and result in a contiguous, valid hash chain."""
    url = clean_ledger_db
    ledger = TrustLedger(database_url=url)

    num_threads = 5
    items_per_thread = 3
    total_appends = num_threads * items_per_thread

    def worker(worker_id: int):
        results = []
        for i in range(items_per_thread):
            entry = ledger.record_verification(
                event_type="VERIFICATION_VERDICT",
                canonical_parcel_id=None,
                dag_number=f"{1000 + worker_id * 10 + i}",
                mouza="কাশিমপুর",
                verdict="CLEAR" if i % 2 == 0 else "BLOCK",
                cited_records=[f"REC-{worker_id}-{i}"],
                officer_id=f"OFFICER-{worker_id}",
            )
            results.append(entry)
        return results

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, w) for w in range(num_threads)]
        for f in as_completed(futures):
            f.result()

    # Total rows = 1 (genesis) + total_appends
    chain = ledger._chain
    assert len(chain) == total_appends + 1

    # Verify sequential indices
    indices = [e.index for e in chain]
    assert indices == list(range(total_appends + 1))

    # Verify cryptographic integrity
    is_valid, reason = ledger.verify_integrity()
    assert is_valid is True
    assert reason is None


def test_pg_ledger_resigned_entry_with_different_key_detected(clean_ledger_db, pg_migrated_engine):
    """An entry modified and re-signed with a rogue Ed25519 key fails verification against pinned public key."""
    url = clean_ledger_db
    ledger = TrustLedger(database_url=url)

    ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=None,
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["RS-402-KHAS"],
    )

    # Attacker generates their own private key
    rogue_private_key = ed25519.Ed25519PrivateKey.generate()
    rogue_public_key_hex = rogue_private_key.public_key().public_bytes_raw().hex()

    # Get block 1 entry hash
    block1 = ledger._chain[1]
    rogue_signature = rogue_private_key.sign(block1.entry_hash.encode("utf-8")).hex()

    # Update block 1 signature in database with rogue signature
    with pg_migrated_engine.connect() as conn:
        conn.execute(text("ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_entries_immutable;"))
        conn.execute(
            text(f"UPDATE ledger_entries SET signature = '{rogue_signature}' WHERE entry_index = 1;")
        )
        conn.execute(text("ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_entries_immutable;"))
        conn.commit()

    is_valid, reason = ledger.verify_integrity()
    assert is_valid is False
    assert "Invalid cryptographic signature" in reason


def test_production_startup_validation_for_ledger_key(monkeypatch):
    """Settings initialization fails in production if ledger_private_key is missing or equal to dev default."""
    # 1. Fails when using default dev key
    with pytest.raises(ValidationError) as exc1:
        Settings(
            environment="production",
            secret_key="a-secure-production-secret-key-123456789",
            nid_hmac_secret="a-secure-production-nid-hmac-salt-987654321",
            ledger_private_key=DEFAULT_DEV_LEDGER_KEY,
        )
    assert "Insecure default or missing ledger_private_key cannot be used in environment 'production'" in str(exc1.value)

    # 2. Fails when empty
    with pytest.raises(ValidationError) as exc2:
        Settings(
            environment="production",
            secret_key="a-secure-production-secret-key-123456789",
            nid_hmac_secret="a-secure-production-nid-hmac-salt-987654321",
            ledger_private_key="",
        )
    assert "Insecure default or missing ledger_private_key cannot be used in environment 'production'" in str(exc2.value)

    # 3. Succeeds when provided with a strong 32-byte hex key
    priv = ed25519.Ed25519PrivateKey.generate()
    valid_key_hex = priv.private_bytes_raw().hex()

    prod_settings = Settings(
        environment="production",
        secret_key="a-secure-production-secret-key-123456789",
        nid_hmac_secret="a-secure-production-nid-hmac-salt-987654321",
        ledger_private_key=valid_key_hex,
    )
    assert prod_settings.environment == "production"
    assert prod_settings.ledger_private_key == valid_key_hex
