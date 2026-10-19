"""Phase 2 Authentication and Authorization Tests for NAKSHA."""
import time
import pytest
import jwt
from fastapi.testclient import TestClient
from pydantic import ValidationError

from naksha.api.app import app
from naksha.core.config import Settings, settings
from naksha.models.auth import OfficerContext, OfficerRole
from naksha.core.auth import create_officer_token
from naksha.services.ledger import audit_ledger
from naksha.api.routes import reset_auth_rate_limits

client = TestClient(app)


@pytest.fixture(autouse=True)
def enforce_clean_dependency_overrides():
    """Ensure tests in test_auth.py strictly run with real dependencies (no overrides)."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _make_token(
    officer_id: str = "UL-2024-KSH",
    name: str = "মোঃ ফজলুর রহমান",
    role: OfficerRole = OfficerRole.UNION_LAND_OFFICER,
    designation: str = "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    office: str = "কাশিমপুর, গাজীপুর সদর",
    jurisdiction: str = "কাশিমপুর",
    secret: str = None,
    issuer: str = None,
    expires_in: int = 900,
) -> str:
    now = int(time.time())
    payload = {
        "sub": officer_id,
        "name": name,
        "role": role.value if isinstance(role, OfficerRole) else str(role),
        "designation": designation,
        "office": office,
        "jurisdiction": jurisdiction,
        "iat": now,
        "exp": now + expires_in,
        "iss": issuer or settings.jwt_issuer,
    }
    key = secret if secret is not None else settings.secret_key
    return jwt.encode(payload, key, algorithm="HS256")


# ==============================================================================
# Token Verification & 401 Failure Modes
# ==============================================================================

def test_missing_token_returns_401():
    """Accessing protected /api/v1/* without Authorization header returns 401."""
    res = client.get("/api/v1/records")
    assert res.status_code == 401
    assert "Missing Bearer authorization token" in res.json()["detail"]


def test_malformed_token_returns_401():
    """Accessing with non-JWT string returns 401."""
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
    )
    assert res.status_code == 401
    assert "Invalid token signature or claims" in res.json()["detail"]


def test_expired_token_returns_401():
    """Token with expired timestamp returns 401 with clear message."""
    expired_token = _make_token(expires_in=-60)
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "Token has expired" in res.json()["detail"]


def test_forged_secret_token_returns_401():
    """Token signed with wrong HMAC secret returns 401."""
    forged_token = _make_token(secret="attacker-forged-secret-key-123456789")
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert res.status_code == 401
    assert "Invalid token signature" in res.json()["detail"]


def test_wrong_issuer_token_returns_401():
    """Token signed with unexpected issuer returns 401."""
    wrong_iss_token = _make_token(issuer="fraudulent-issuer")
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {wrong_iss_token}"},
    )
    assert res.status_code == 401
    assert "Invalid token issuer" in res.json()["detail"]


def test_missing_required_claims_returns_401():
    """Token missing required officer claims returns 401."""
    now = int(time.time())
    payload = {
        "sub": "UL-2024-KSH",
        "exp": now + 900,
        "iss": settings.jwt_issuer,
        # missing name, role, designation, office, jurisdiction
    }
    incomplete_token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {incomplete_token}"},
    )
    assert res.status_code == 401
    assert "Token missing required officer claims" in res.json()["detail"]


# ==============================================================================
# Valid Token & RBAC Role Enforcement (403)
# ==============================================================================

def test_valid_token_accesses_protected_route():
    """Valid token allows accessing protected route."""
    token = _make_token()
    res = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "records" in res.json()


def test_wrong_role_returns_403():
    """Surveyor attempting to access /api/v1/ledger returns 403."""
    surveyor_token = _make_token(
        officer_id="SRV-2024-01",
        name="মোঃ আমিনুল ইসলাম",
        role=OfficerRole.SURVEYOR,
        designation="সার্ভেয়ার",
        office="গাজীপুর সদর",
        jurisdiction="গাজীপুর সদর",
    )
    res = client.get(
        "/api/v1/ledger",
        headers={"Authorization": f"Bearer {surveyor_token}"},
    )
    assert res.status_code == 403
    assert "not authorized to access 'ledger'" in res.json()["detail"]


# ==============================================================================
# Jurisdiction Enforcement (403)
# ==============================================================================

def test_wrong_jurisdiction_returns_403():
    """Union Land Officer from Savar cannot access Kashimpur parcel verification."""
    savar_ulo_token = _make_token(
        officer_id="UL-2024-SVR",
        name="আব্দুল কুদ্দুস",
        role=OfficerRole.UNION_LAND_OFFICER,
        designation="ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
        office="সাভার, ঢাকা",
        jurisdiction="সাভার",
    )
    res = client.get(
        "/api/v1/spatial/parcels/par-8f92-bd04-syn/verification",
        headers={"Authorization": f"Bearer {savar_ulo_token}"},
    )
    assert res.status_code == 403
    assert "does not permit access to mouza" in res.json()["detail"]


def test_correct_jurisdiction_returns_200():
    """Union Land Officer with jurisdiction 'কাশিমপুর' can access Kashimpur parcel."""
    kashimpur_ulo_token = _make_token(
        officer_id="UL-2024-KSH",
        jurisdiction="কাশিমপুর",
    )
    res = client.get(
        "/api/v1/spatial/parcels/par-8f92-bd04-syn/verification",
        headers={"Authorization": f"Bearer {kashimpur_ulo_token}"},
    )
    assert res.status_code == 200
    assert res.json()["verdict"] in ("BLOCK", "REVIEW", "CLEAR")


def test_ac_land_has_upazila_jurisdiction():
    """AC Land with jurisdiction 'গাজীপুর সদর' can access constituent mouza parcels."""
    ac_land_token = _make_token(
        officer_id="AC-2024-GZP",
        name="তানিয়া সুলতানা",
        role=OfficerRole.AC_LAND,
        designation="সহকারী কমিশনার (ভূমি)",
        office="গাজীপুর সদর",
        jurisdiction="গাজীপুর সদর",
    )
    res = client.get(
        "/api/v1/spatial/parcels/par-8f92-bd04-syn/verification",
        headers={"Authorization": f"Bearer {ac_land_token}"},
    )
    assert res.status_code == 200


# ==============================================================================
# /auth/verify-officer Credentials and Origin Validation
# ==============================================================================

def test_verify_officer_success():
    """Matching officer_id, name, designation, and valid origin returns verified token."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://localhost:8000",
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
        "office": "কাশিমপুর, গাজীপুর সদর",
    }
    res = client.post("/auth/verify-officer", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["token"] is not None
    assert data["officer"]["officer_id"] == "UL-2024-KSH"

    # Verify ACCESS_GRANTED ledger entry
    latest = audit_ledger.latest_entry
    assert latest.event_type == "ACCESS_GRANTED"
    assert latest.officer_id == "UL-2024-KSH"


def test_verify_officer_name_mismatch():
    """Name mismatch returns denied and emits ACCESS_DENIED with claimed officer_id."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://localhost:8000",
        "officer_id": "UL-2024-KSH",
        "name": "ভুল নাম (Wrong Name)",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    }
    res = client.post("/auth/verify-officer", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "denied"
    assert data["token"] is None
    assert "নাম নিবন্ধনের তথ্যের সাথে মেলেনি" in data["reason"]

    # Verify ACCESS_DENIED in ledger
    latest = audit_ledger.latest_entry
    assert latest.event_type == "ACCESS_DENIED"
    assert latest.officer_id == "UL-2024-KSH"


def test_verify_officer_designation_mismatch():
    """Designation mismatch returns denied."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://localhost:8000",
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "সহকারী কমিশনার (ভূমি)",  # wrong designation
    }
    res = client.post("/auth/verify-officer", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "denied"
    assert data["token"] is None
    assert "পদবী নিবন্ধনের তথ্যের সাথে মেলেনি" in data["reason"]


def test_verify_officer_extension_and_portal_origins_pass(monkeypatch):
    """Extension Origin header + portal origin in body succeeds when both are allowlisted."""
    reset_auth_rate_limits()
    test_ext_origin = "chrome-extension://abcdefghijklmnopqrstuvwxyz123456"
    test_portal_origin = "http://localhost:8000"
    
    # Allow both origins
    monkeypatch.setattr(settings, "allowed_origins", settings.allowed_origins + [test_ext_origin])
    
    payload = {
        "portal_origin": test_portal_origin,
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    }
    # Chrome extension sends Origin header: chrome-extension://<id>
    res = client.post(
        "/auth/verify-officer",
        json=payload,
        headers={"Origin": test_ext_origin},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "verified"
    assert res.json()["token"] is not None


def test_verify_officer_unlisted_http_origin_header_denied():
    """Unlisted HTTP Origin header is denied even if body portal_origin is valid."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://localhost:8000",
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    }
    res = client.post(
        "/auth/verify-officer",
        json=payload,
        headers={"Origin": "http://evil-unlisted-origin.com"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "denied"
    assert "Disallowed HTTP Origin header" in data["reason"]


def test_verify_officer_unlisted_portal_origin_denied():
    """Unlisted portal_origin in body is denied."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://unauthorized-domain.com",
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    }
    res = client.post("/auth/verify-officer", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "denied"
    assert "Disallowed portal origin" in data["reason"]


def test_verify_officer_empty_portal_origin_denied():
    """Empty or missing portal_origin in body is denied."""
    reset_auth_rate_limits()
    for empty_val in ["", "   ", None]:
        payload = {
            "portal_origin": empty_val,
            "officer_id": "UL-2024-KSH",
            "name": "মোঃ ফজলুর রহমান",
            "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
        }
        res = client.post("/auth/verify-officer", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "denied"
        assert "Disallowed portal origin" in data["reason"]


def test_verify_officer_origin_bypass_attempts():
    """Exact-match origin check rejects substrings, prefixes, and suffixes."""
    reset_auth_rate_limits()
    invalid_origins = [
        "http://evil.com/http://localhost:8000",
        "http://localhost:8000.evil.com",
        "http://evil.com",
    ]
    for origin in invalid_origins:
        payload = {
            "portal_origin": origin,
            "officer_id": "UL-2024-KSH",
            "name": "মোঃ ফজলুর রহমান",
            "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
        }
        res = client.post("/auth/verify-officer", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "denied"
        assert "Disallowed portal origin" in data["reason"]


def test_prove_dependency_removal_would_fail_protection():
    """Proves that route protection strictly requires the real dependency, not an override."""
    # 1. With NO override, accessing protected route returns 401
    assert len(app.dependency_overrides) == 0
    res_real = client.get("/api/v1/records")
    assert res_real.status_code == 401

    # 2. If the dependency were bypassed (simulating what happens without auth dependency),
    # it would return 200. This proves the test exercises the real dependency.
    from naksha.core.auth import get_current_officer
    dummy_officer = OfficerContext(
        officer_id="TEST-OVERRIDE",
        name="তানিয়া সুলতানা",
        role=OfficerRole.SYSTEM_ADMIN,
        designation="সহকারী কমিশনার (ভূমি)",
        office="গাজীপুর সদর",
        jurisdiction="কাশিমপুর, গাজীপুর সদর",
    )
    app.dependency_overrides[get_current_officer] = lambda: dummy_officer
    try:
        res_override = client.get("/api/v1/records")
        assert res_override.status_code == 200
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# Rate Limiting on /auth/verify-officer
# ==============================================================================

def test_verify_officer_rate_limit():
    """6th rapid call from the same IP is rejected with 429 Too Many Requests."""
    reset_auth_rate_limits()
    payload = {
        "portal_origin": "http://localhost:8000",
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
    }

    # Calls 1 to 5 should succeed
    for i in range(settings.auth_rate_limit_max_requests):
        res = client.post("/auth/verify-officer", json=payload)
        assert res.status_code == 200

    # 6th call exceeds limit -> 429
    res_6 = client.post("/auth/verify-officer", json=payload)
    assert res_6.status_code == 429
    assert "Too many authentication requests" in res_6.json()["detail"]
    reset_auth_rate_limits()


# ==============================================================================
# Ledger Officer Attribution
# ==============================================================================

def test_ledger_records_token_officer_id():
    """Verification ledger entry records officer_id from the token, not 'SYSTEM'."""
    officer_id = "KN-2024-KSH"
    token = _make_token(
        officer_id=officer_id,
        name="মোঃ রফিকুল ইসলাম",
        role=OfficerRole.KANUNGO,
        designation="কানুনগো",
        office="কাশিমপুর, গাজীপুর সদর",
        jurisdiction="কাশিমপুর",
    )
    res = client.get(
        "/api/v1/spatial/parcels/par-8f92-bd04-syn/verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    latest = audit_ledger.latest_entry
    assert latest.event_type == "VERIFICATION_VERDICT"
    assert latest.officer_id == officer_id
    assert latest.officer_id != "SYSTEM"


# ==============================================================================
# Configuration Startup Fail-Safe in Production
# ==============================================================================

def test_production_startup_fails_with_default_secret_key(monkeypatch):
    """Settings initialization fails in production if secret_key equals default."""
    from naksha.core.config import DEFAULT_DEV_SECRET

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment="production",
            secret_key=DEFAULT_DEV_SECRET,
        )
    assert "Insecure default secret_key cannot be used in environment 'production'" in str(exc_info.value)

    # Test via environment variables
    monkeypatch.setenv("NAKSHA_ENVIRONMENT", "production")
    monkeypatch.setenv("NAKSHA_SECRET_KEY", DEFAULT_DEV_SECRET)
    with pytest.raises(ValidationError) as exc_info2:
        Settings()
    assert "Insecure default secret_key cannot be used in environment 'production'" in str(exc_info2.value)

    # But succeeds with a strong production key
    monkeypatch.setenv("NAKSHA_SECRET_KEY", "a-secure-randomly-generated-production-secret-key-123456789")
    monkeypatch.setenv("NAKSHA_NID_HMAC_SECRET", "a-secure-randomly-generated-nid-hmac-salt-key-123456789")
    prod_settings = Settings()
    assert prod_settings.environment == "production"


def test_production_startup_fails_with_default_nid_hmac_secret(monkeypatch):
    """Settings initialization fails in production if nid_hmac_secret equals default."""
    from naksha.core.config import DEFAULT_DEV_NID_SECRET

    monkeypatch.setenv("NAKSHA_ENVIRONMENT", "production")
    monkeypatch.setenv("NAKSHA_SECRET_KEY", "a-secure-production-secret-key-987654321")
    monkeypatch.setenv("NAKSHA_NID_HMAC_SECRET", DEFAULT_DEV_NID_SECRET)

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "Insecure default nid_hmac_secret cannot be used in environment 'production'" in str(exc_info.value)
