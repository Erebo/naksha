"""Trust Ledger and Cryptographic Audit Log Service for NAKSHA.

Implements an append-only, SHA-256 hash-chained audit log with Ed25519 digital
signing for statutory land record queries and verification verdicts.
Supports persistence on PostgreSQL with row-level locking and trigger-based
immutability, while maintaining an in-memory chain for SQLite/testing.
"""
import hashlib
import json
import uuid
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from cryptography.hazmat.primitives.asymmetric import ed25519

from naksha.core.config import settings

GENESIS_TIMESTAMP = "2026-01-01T00:00:00+00:00"
GENESIS_PAYLOAD = {"genesis": "NAKSHA LandTech 2026 Innovation Hackathon Trust Ledger Root"}


def format_timestamp(ts: Any) -> str:
    """Standardizes timestamp representation to ISO-8601 string."""
    if isinstance(ts, datetime):
        return ts.isoformat()
    s = str(ts)
    if s.endswith("Z"):
        return s[:-1] + "+00:00"
    return s


def compute_genesis_payload_hash() -> str:
    """Computes SHA-256 digest of normalized genesis payload."""
    return hashlib.sha256(json.dumps(GENESIS_PAYLOAD, sort_keys=True).encode("utf-8")).hexdigest()


def compute_genesis_entry_hash(timestamp_str: str, payload_hash: str) -> str:
    """Computes entry hash for block 0 linking previous hash of all zeros."""
    raw_str = f"0:{timestamp_str}:{'0' * 64}:{payload_hash}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_payload_hash(
    index: int,
    event_type: str,
    canonical_parcel_id: Optional[str],
    dag_number: Optional[str],
    mouza: Optional[str],
    officer_id: Optional[str],
    verdict: Optional[str],
    cited_records: Optional[List[str]],
) -> str:
    """Computes deterministic SHA-256 digest of normalized audit payload."""
    payload_dict = {
        "index": index,
        "event_type": event_type,
        "canonical_parcel_id": str(canonical_parcel_id) if canonical_parcel_id else None,
        "dag_number": str(dag_number) if dag_number else None,
        "mouza": mouza,
        "officer_id": officer_id or "SYSTEM",
        "verdict": verdict,
        "cited_records": sorted(cited_records or []),
    }
    payload_json = json.dumps(payload_dict, sort_keys=True)
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


class LedgerEntry(BaseModel):
    """An immutable, hash-linked block in the NAKSHA Trust Ledger."""
    index: int = Field(description="Sequential 0-indexed position in the audit chain.")
    timestamp: str = Field(description="ISO-8601 UTC timestamp of the ledger event.")
    event_type: str = Field(description="Category of action: VERIFICATION_VERDICT, RECORD_QUERY, or OVERLAY_ACCESSED.")
    canonical_parcel_id: Optional[str] = Field(default=None, description="Target parcel UUID.")
    dag_number: Optional[str] = Field(default=None, description="Plot / Dag number queried.")
    mouza: Optional[str] = Field(default=None, description="Mouza name.")
    officer_id: str = Field(default="SYSTEM", description="Authenticated officer or session identifier.")
    verdict: Optional[str] = Field(default=None, description="Automated statutory decision verdict: CLEAR, REVIEW, or BLOCK.")
    cited_records: List[str] = Field(default_factory=list, description="IDs of records cross-referenced.")
    payload_hash: str = Field(description="SHA-256 digest of normalized event data payload.")
    previous_hash: str = Field(description="SHA-256 digest of the immediately preceding ledger block.")
    entry_hash: str = Field(description="SHA-256 digest linking index, timestamp, previous_hash, and payload_hash.")
    signature_ed25519: str = Field(description="Hex-encoded Ed25519 signature over entry_hash.")
    public_key_ed25519: str = Field(default_factory=lambda: settings.get_ledger_public_key_hex(), description="Public verification key.")
    is_synthetic: bool = True


class TrustLedger:
    """Manages an append-only cryptographic chain of signed audit entries."""

    def __init__(self, database_url: Optional[str] = None):
        self._custom_db_url = database_url
        self._in_memory_chain: List[LedgerEntry] = []
        if not self.is_postgres:
            self._create_genesis_block()

    @property
    def is_postgres(self) -> bool:
        url = self._custom_db_url or settings.database_url
        return bool(url and url.startswith("postgresql"))

    def _get_session(self) -> Session:
        from naksha.database.connection import get_session
        url = self._custom_db_url or settings.database_url
        return get_session(url)

    @property
    def _signing_key(self) -> ed25519.Ed25519PrivateKey:
        return settings.get_ledger_signing_key()

    @property
    def _public_key_hex(self) -> str:
        return settings.get_ledger_public_key_hex()

    def _create_genesis_block(self) -> LedgerEntry:
        timestamp = GENESIS_TIMESTAMP
        payload_hash = compute_genesis_payload_hash()
        prev_hash = "0" * 64

        entry_hash = compute_genesis_entry_hash(timestamp, payload_hash)
        signature = self._signing_key.sign(entry_hash.encode("utf-8")).hex()

        genesis = LedgerEntry(
            index=0,
            timestamp=timestamp,
            event_type="GENESIS",
            canonical_parcel_id="root-parcel-0000",
            dag_number="0",
            mouza="ROOT",
            officer_id="SYSTEM",
            verdict="CLEAR",
            cited_records=[],
            payload_hash=payload_hash,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
            signature_ed25519=signature,
            public_key_ed25519=self._public_key_hex,
        )
        self._in_memory_chain.append(genesis)
        return genesis

    def _ensure_genesis_pg(self, session: Session) -> Any:
        from naksha.database.pg_models import LedgerEntryPG
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext('naksha_ledger_entries'));"))
        existing = session.query(LedgerEntryPG).filter(LedgerEntryPG.entry_index == 0).first()
        if existing:
            return existing

        ts_dt = datetime.fromisoformat(GENESIS_TIMESTAMP)
        payload_hash = compute_genesis_payload_hash()
        entry_hash = compute_genesis_entry_hash(GENESIS_TIMESTAMP, payload_hash)
        signature = self._signing_key.sign(entry_hash.encode("utf-8")).hex()

        genesis_row = LedgerEntryPG(
            entry_index=0,
            timestamp=ts_dt,
            event_type="GENESIS",
            parcel_id=None,
            dag_number="0",
            mouza="ROOT",
            officer_id="SYSTEM",
            verdict="CLEAR",
            cited_records=[],
            payload_hash=payload_hash,
            previous_hash="0" * 64,
            entry_hash=entry_hash,
            signature=signature,
        )
        session.add(genesis_row)
        session.flush()
        return genesis_row

    def _pg_to_entry(self, row: Any) -> LedgerEntry:
        ts_str = format_timestamp(row.timestamp)
        return LedgerEntry(
            index=row.entry_index,
            timestamp=ts_str,
            event_type=row.event_type,
            canonical_parcel_id=str(row.parcel_id) if row.parcel_id else None,
            dag_number=row.dag_number,
            mouza=row.mouza,
            officer_id=row.officer_id or "SYSTEM",
            verdict=row.verdict,
            cited_records=row.cited_records or [],
            payload_hash=row.payload_hash,
            previous_hash=row.previous_hash,
            entry_hash=row.entry_hash,
            signature_ed25519=row.signature,
            public_key_ed25519=self._public_key_hex,
            is_synthetic=False,
        )

    @property
    def latest_entry(self) -> LedgerEntry:
        if not self.is_postgres:
            return self._in_memory_chain[-1]

        from naksha.database.pg_models import LedgerEntryPG
        session = self._get_session()
        try:
            self._ensure_genesis_pg(session)
            session.commit()
            last_row = (
                session.query(LedgerEntryPG)
                .order_by(LedgerEntryPG.entry_index.desc())
                .first()
            )
            return self._pg_to_entry(last_row)
        finally:
            session.close()

    @property
    def _chain(self) -> List[LedgerEntry]:
        if not self.is_postgres:
            return self._in_memory_chain

        from naksha.database.pg_models import LedgerEntryPG
        session = self._get_session()
        try:
            self._ensure_genesis_pg(session)
            session.commit()
            rows = (
                session.query(LedgerEntryPG)
                .order_by(LedgerEntryPG.entry_index.asc())
                .all()
            )
            return [self._pg_to_entry(r) for r in rows]
        finally:
            session.close()

    @_chain.setter
    def _chain(self, value: List[LedgerEntry]) -> None:
        self._in_memory_chain = value

    def record_verification(
        self,
        event_type: str,
        canonical_parcel_id: Optional[str],
        dag_number: Optional[str],
        mouza: Optional[str],
        verdict: Optional[str],
        cited_records: List[str],
        officer_id: str = "SYSTEM",
    ) -> LedgerEntry:
        """Appends a new cryptographically signed, hash-chained entry to the Trust Ledger."""
        if not self.is_postgres:
            return self._record_verification_in_memory(
                event_type=event_type,
                canonical_parcel_id=canonical_parcel_id,
                dag_number=dag_number,
                mouza=mouza,
                verdict=verdict,
                cited_records=cited_records,
                officer_id=officer_id,
            )

        from naksha.database.pg_models import LedgerEntryPG

        max_retries = 10
        for attempt in range(max_retries):
            session = self._get_session()
            try:
                # Advisory lock serializes writes across transactions
                session.execute(text("SELECT pg_advisory_xact_lock(hashtext('naksha_ledger_entries'));"))

                self._ensure_genesis_pg(session)

                # Lock the last row using FOR UPDATE as explicitly required
                last_row = (
                    session.query(LedgerEntryPG)
                    .order_by(LedgerEntryPG.entry_index.desc())
                    .with_for_update()
                    .first()
                )

                next_index = (last_row.entry_index + 1) if last_row else 0
                prev_hash = last_row.entry_hash if last_row else ("0" * 64)

                now_dt = datetime.now(timezone.utc)
                ts_str = format_timestamp(now_dt)

                payload_hash = compute_payload_hash(
                    index=next_index,
                    event_type=event_type,
                    canonical_parcel_id=canonical_parcel_id,
                    dag_number=dag_number,
                    mouza=mouza,
                    officer_id=officer_id,
                    verdict=verdict,
                    cited_records=cited_records,
                )

                raw_block_str = f"{next_index}:{ts_str}:{prev_hash}:{payload_hash}"
                entry_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
                signature = self._signing_key.sign(entry_hash.encode("utf-8")).hex()

                parcel_uuid = None
                if canonical_parcel_id:
                    try:
                        parcel_uuid = uuid.UUID(str(canonical_parcel_id))
                    except (ValueError, TypeError):
                        parcel_uuid = None

                new_row = LedgerEntryPG(
                    entry_index=next_index,
                    timestamp=now_dt,
                    event_type=event_type,
                    parcel_id=parcel_uuid,
                    dag_number=str(dag_number) if dag_number else None,
                    mouza=mouza,
                    officer_id=officer_id,
                    verdict=verdict,
                    cited_records=sorted(cited_records or []),
                    payload_hash=payload_hash,
                    previous_hash=prev_hash,
                    entry_hash=entry_hash,
                    signature=signature,
                )
                session.add(new_row)
                session.commit()
                return self._pg_to_entry(new_row)
            except Exception:
                session.rollback()
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.01 * (attempt + 1))
            finally:
                session.close()

    def _record_verification_in_memory(
        self,
        event_type: str,
        canonical_parcel_id: Optional[str],
        dag_number: Optional[str],
        mouza: Optional[str],
        verdict: Optional[str],
        cited_records: List[str],
        officer_id: str = "SYSTEM",
    ) -> LedgerEntry:
        index = len(self._in_memory_chain)
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_entry = self.latest_entry

        payload_hash = compute_payload_hash(
            index=index,
            event_type=event_type,
            canonical_parcel_id=canonical_parcel_id,
            dag_number=dag_number,
            mouza=mouza,
            officer_id=officer_id,
            verdict=verdict,
            cited_records=cited_records,
        )

        raw_block_str = f"{index}:{timestamp}:{prev_entry.entry_hash}:{payload_hash}"
        entry_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
        signature = self._signing_key.sign(entry_hash.encode("utf-8")).hex()

        entry = LedgerEntry(
            index=index,
            timestamp=timestamp,
            event_type=event_type,
            canonical_parcel_id=canonical_parcel_id,
            dag_number=str(dag_number) if dag_number else None,
            mouza=mouza,
            officer_id=officer_id,
            verdict=verdict,
            cited_records=cited_records,
            payload_hash=payload_hash,
            previous_hash=prev_entry.entry_hash,
            entry_hash=entry_hash,
            signature_ed25519=signature,
            public_key_ed25519=self._public_key_hex,
        )
        self._in_memory_chain.append(entry)
        return entry

    def get_entries(self, limit: int = 50) -> List[LedgerEntry]:
        """Returns the most recent ledger entries, latest first."""
        if not self.is_postgres:
            return list(reversed(self._in_memory_chain[-limit:]))

        from naksha.database.pg_models import LedgerEntryPG
        session = self._get_session()
        try:
            self._ensure_genesis_pg(session)
            session.commit()
            rows = (
                session.query(LedgerEntryPG)
                .order_by(LedgerEntryPG.entry_index.desc())
                .limit(limit)
                .all()
            )
            return [self._pg_to_entry(r) for r in rows]
        finally:
            session.close()

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Deterministically checks the entire hash chain and Ed25519 digital signatures.

        Validates:
        1. Genesis block link, content payload, entry hash, and cryptographic signature.
        2. Sequential index ordering.
        3. Cryptographic hash chain pointers (previous_hash == prev.entry_hash).
        4. Recomputation of payload_hash from raw stored fields.
        5. Recomputation of entry_hash.
        6. Verification of Ed25519 digital signatures against the PINNED public key from settings.

        Returns (True, None) if untampered, or (False, reason) if any violation is detected.
        """
        entries = self._chain
        if not entries:
            return False, "Chain is empty"

        pinned_pub_key = settings.get_ledger_public_key()

        # 1. Verify Genesis Block
        genesis = entries[0]
        if genesis.index != 0:
            return False, f"Broken index sequence at position 0: expected 0, got {genesis.index}"
        if genesis.previous_hash != ("0" * 64):
            return False, "Invalid Genesis Block link"
        if genesis.event_type != "GENESIS":
            return False, f"Invalid Genesis event_type: {genesis.event_type}"

        expected_gen_payload_hash = compute_genesis_payload_hash()
        if genesis.payload_hash != expected_gen_payload_hash:
            return False, "Tampered block hash at index 0: payload mismatch detected"

        ts_str = format_timestamp(genesis.timestamp)
        expected_gen_entry_hash = compute_genesis_entry_hash(ts_str, genesis.payload_hash)
        if genesis.entry_hash != expected_gen_entry_hash:
            return False, "Tampered block hash at index 0: hash mismatch detected"

        try:
            pinned_pub_key.verify(bytes.fromhex(genesis.signature_ed25519), genesis.entry_hash.encode("utf-8"))
        except Exception as e:
            return False, f"Invalid cryptographic signature at block 0: {e}"

        # 2. Walk entire chain
        for i in range(1, len(entries)):
            prev = entries[i - 1]
            curr = entries[i]

            # Index sequence
            if curr.index != prev.index + 1:
                return False, f"Broken index sequence at position {i}: expected {prev.index + 1}, got {curr.index}"

            # Hash pointer link
            if curr.previous_hash != prev.entry_hash:
                return False, f"Broken hash chain pointer at block {curr.index}: previous_hash does not match block {prev.index} entry_hash"

            # Recompute payload hash from stored fields
            expected_payload_hash = compute_payload_hash(
                index=curr.index,
                event_type=curr.event_type,
                canonical_parcel_id=curr.canonical_parcel_id,
                dag_number=curr.dag_number,
                mouza=curr.mouza,
                officer_id=curr.officer_id,
                verdict=curr.verdict,
                cited_records=curr.cited_records,
            )
            if curr.payload_hash != expected_payload_hash:
                return False, f"Tampered block hash at index {curr.index}: payload mismatch detected"

            # Recompute entry hash
            curr_ts_str = format_timestamp(curr.timestamp)
            raw_block_str = f"{curr.index}:{curr_ts_str}:{curr.previous_hash}:{curr.payload_hash}"
            expected_entry_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
            if curr.entry_hash != expected_entry_hash:
                return False, f"Tampered block hash at index {curr.index}: hash mismatch detected"

            # Verify Ed25519 signature against PINNED public key from settings
            try:
                pinned_pub_key.verify(bytes.fromhex(curr.signature_ed25519), curr.entry_hash.encode("utf-8"))
            except Exception as e:
                return False, f"Invalid cryptographic signature at block {curr.index}: {e}"

        return True, None


# Global singleton ledger instance
audit_ledger = TrustLedger()
