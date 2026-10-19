"""Privacy & Anonymization Engine for NAKSHA Land Identity Protection.

Mandates that personal identifiers (such as National ID numbers, smart cards,
or birth registration certificates) are never persisted, cached, or logged in
plaintext across the system. All identifiers are deterministically salted and
hashed via HMAC-SHA256.
"""
import hmac
import hashlib
from typing import Optional
from naksha.core.config import settings


def hash_identifier(raw_id: str, secret: Optional[str] = None) -> str:
    """Hashes a personal identifier (e.g. NID) deterministically using HMAC-SHA256.

    Args:
        raw_id: Plaintext person identifier string.
        secret: Optional custom HMAC key; defaults to settings.nid_hmac_secret.

    Returns:
        Hex-encoded 64-character SHA-256 HMAC string.

    Raises:
        ValueError: If raw_id is empty or whitespace-only.
    """
    if raw_id is None:
        raise ValueError("Identifier to hash cannot be None.")
    
    clean_id = raw_id.strip()
    if not clean_id:
        raise ValueError("Identifier to hash cannot be empty or whitespace.")

    key_str = secret if secret is not None else settings.nid_hmac_secret
    key_bytes = key_str.encode("utf-8")
    val_bytes = clean_id.encode("utf-8")

    return hmac.new(key_bytes, val_bytes, hashlib.sha256).hexdigest()
