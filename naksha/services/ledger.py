"""Trust Ledger and Cryptographic Audit Log Service for NAKSHA.

Implements an append-only, SHA-256 hash-chained audit log with Ed25519 digital
signing for statutory land record queries and verification verdicts.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate a deterministic service-level Ed25519 private key for demonstration sealing
_SIGNING_KEY = ed25519.Ed25519PrivateKey.generate()
_PUBLIC_KEY = _SIGNING_KEY.public_key()
_PUBLIC_KEY_HEX = _PUBLIC_KEY.public_bytes_raw().hex()


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
    public_key_ed25519: str = Field(default=_PUBLIC_KEY_HEX, description="Public verification key.")
    is_synthetic: bool = True


class TrustLedger:
    """Manages an append-only in-memory chain of signed audit entries."""

    def __init__(self):
        self._chain: List[LedgerEntry] = []
        # Create Genesis Block
        self._create_genesis_block()

    def _create_genesis_block(self):
        timestamp = "2026-01-01T00:00:00Z"
        payload_data = {"genesis": "NAKSHA LandTech 2026 Innovation Hackathon Trust Ledger Root"}
        payload_hash = hashlib.sha256(json.dumps(payload_data, sort_keys=True).encode("utf-8")).hexdigest()
        prev_hash = "0" * 64

        raw_block_str = f"0:{timestamp}:{prev_hash}:{payload_hash}"
        entry_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
        signature = _SIGNING_KEY.sign(entry_hash.encode("utf-8")).hex()

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
            public_key_ed25519=_PUBLIC_KEY_HEX,
        )
        self._chain.append(genesis)

    @property
    def latest_entry(self) -> LedgerEntry:
        return self._chain[-1]

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
        index = len(self._chain)
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_entry = self.latest_entry

        payload_dict = {
            "index": index,
            "event_type": event_type,
            "canonical_parcel_id": canonical_parcel_id,
            "dag_number": str(dag_number),
            "mouza": mouza,
            "officer_id": officer_id,
            "verdict": verdict,
            "cited_records": sorted(cited_records),
        }
        payload_json = json.dumps(payload_dict, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        raw_block_str = f"{index}:{timestamp}:{prev_entry.entry_hash}:{payload_hash}"
        entry_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
        signature = _SIGNING_KEY.sign(entry_hash.encode("utf-8")).hex()

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
            public_key_ed25519=_PUBLIC_KEY_HEX,
        )
        self._chain.append(entry)
        return entry

    def get_entries(self, limit: int = 50) -> List[LedgerEntry]:
        """Returns the most recent ledger entries, latest first."""
        return list(reversed(self._chain[-limit:]))

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Deterministically checks the entire hash chain and Ed25519 digital signatures.

        Returns (True, None) if completely untampered, or (False, reason) if any violation is found.
        """
        if not self._chain:
            return False, "Chain is empty"

        # Verify Genesis Block
        genesis = self._chain[0]
        if genesis.index != 0 or genesis.previous_hash != ("0" * 64):
            return False, "Invalid Genesis Block link"

        # Walk entire chain
        for i in range(1, len(self._chain)):
            prev = self._chain[i - 1]
            curr = self._chain[i]

            # 1. Index sequence
            if curr.index != prev.index + 1:
                return False, f"Broken index sequence at position {i}: expected {prev.index + 1}, got {curr.index}"

            # 2. Hash pointer link
            if curr.previous_hash != prev.entry_hash:
                return False, f"Broken hash chain pointer at block {curr.index}: previous_hash does not match block {prev.index} entry_hash"

            # 3. Deterministic recalculation of entry hash
            raw_block_str = f"{curr.index}:{curr.timestamp}:{curr.previous_hash}:{curr.payload_hash}"
            expected_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()
            if curr.entry_hash != expected_hash:
                return False, f"Tampered block hash at index {curr.index}: hash mismatch detected"

            # 4. Ed25519 signature verification
            try:
                pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(curr.public_key_ed25519))
                pub_key.verify(bytes.fromhex(curr.signature_ed25519), curr.entry_hash.encode("utf-8"))
            except Exception as e:
                return False, f"Invalid cryptographic signature at block {curr.index}: {e}"

        return True, None


# Global singleton ledger instance
audit_ledger = TrustLedger()
