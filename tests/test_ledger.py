"""Tests for Stage 6 Cryptographic Trust Ledger & Audit Service.

Verifies:
1. Append-only SHA-256 block hash-chain linkage.
2. Ed25519 digital signature signing and cryptographic verification.
3. Tamper detection when payload, hash, or index is manipulated.
4. FastAPI endpoints (/api/v1/ledger and /api/v1/ledger/verify).
"""
import pytest
from fastapi.testclient import TestClient
from naksha.api.app import app
from naksha.services.ledger import TrustLedger, LedgerEntry, audit_ledger

client = TestClient(app)


def test_trust_ledger_genesis_block():
    """Ledger initializes with a verified Genesis block at index 0."""
    ledger = TrustLedger()
    assert len(ledger._chain) == 1
    genesis = ledger._chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash == ("0" * 64)
    assert genesis.event_type == "GENESIS"
    assert genesis.signature_ed25519 is not None

    is_valid, reason = ledger.verify_integrity()
    assert is_valid is True
    assert reason is None


def test_trust_ledger_append_and_hash_chain():
    """Entries are appended sequentially with previous_hash pointer integrity."""
    ledger = TrustLedger()

    entry1 = ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id="par-8f92-bd04-syn",
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["SYN-MATCH-01", "SYN-CONFLICT-AREA-01"],
        officer_id="UL-2024-KSH",
    )
    assert entry1.index == 1
    assert entry1.previous_hash == ledger._chain[0].entry_hash

    entry2 = ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id="par-401-west-syn",
        dag_number="401",
        mouza="কাশিমপুর",
        verdict="CLEAR",
        cited_records=["SYN-401-TAX-01"],
        officer_id="UL-2024-KSH",
    )
    assert entry2.index == 2
    assert entry2.previous_hash == entry1.entry_hash

    # Verify overall chain integrity
    is_valid, reason = ledger.verify_integrity()
    assert is_valid is True
    assert reason is None


def test_trust_ledger_tamper_detection_payload():
    """Tampering with a block's payload or hash is immediately detected."""
    ledger = TrustLedger()
    ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id="par-8f92-bd04-syn",
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["SYN-MATCH-01"],
    )

    # Maliciously modify block 1 payload hash
    ledger._chain[1].payload_hash = "deadbeef" * 8
    is_valid, reason = ledger.verify_integrity()
    assert is_valid is False
    assert "Tampered block hash" in reason


def test_trust_ledger_tamper_detection_signature():
    """Tampering with an Ed25519 signature is immediately caught."""
    ledger = TrustLedger()
    ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id="par-8f92-bd04-syn",
        dag_number="402",
        mouza="কাশিমপুর",
        verdict="BLOCK",
        cited_records=["SYN-MATCH-01"],
    )

    # Alter signature
    ledger._chain[1].signature_ed25519 = "00" * 64
    is_valid, reason = ledger.verify_integrity()
    assert is_valid is False
    assert "Invalid cryptographic signature" in reason or "Tampered" in reason


def test_api_ledger_endpoints():
    """GET /api/v1/ledger and /api/v1/ledger/verify return live cryptographic state."""
    # Record a verification to populate the global ledger
    res_verify = client.get("/api/v1/records/SYN-MATCH-01/verify")
    assert res_verify.status_code == 200
    data_verify = res_verify.json()
    assert "verdict" in data_verify

    # Fetch ledger entries
    res_ledger = client.get("/api/v1/ledger?limit=5")
    assert res_ledger.status_code == 200
    entries = res_ledger.json()
    assert len(entries) >= 2
    first = entries[0]
    assert "entry_hash" in first
    assert "signature_ed25519" in first
    assert "public_key_ed25519" in first

    # Verify ledger integrity endpoint
    res_check = client.get("/api/v1/ledger/verify")
    assert res_check.status_code == 200
    check_data = res_check.json()
    assert check_data["is_valid"] is True
    assert check_data["total_blocks"] >= 2
    assert "SHA-256" in check_data["algorithm"]
