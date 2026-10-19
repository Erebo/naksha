"""NAKSHA Pytest Configuration & Fixtures.

Provides authentication overrides for existing test suites to keep
all existing assertions passing without modification.
"""
import pytest
from naksha.api.app import app
from naksha.core.auth import get_current_officer
from naksha.models.auth import OfficerContext, OfficerRole


@pytest.fixture(autouse=True)
def default_auth_override(request):
    """Automatically provides an authorized officer context for existing test suites.
    
    Tests in tests/test_auth.py manage their own authentication and override behavior.
    """
    if "test_auth" in request.node.nodeid:
        yield
        return

    admin_officer = OfficerContext(
        officer_id="TEST-SUITE-OFFICER",
        name="তানিয়া সুলতানা",
        role=OfficerRole.SYSTEM_ADMIN,
        designation="সহকারী কমিশনার (ভূমি)",
        office="গাজীপুর সদর",
        jurisdiction="কাশিমপুর, গাজীপুর সদর",
    )
    app.dependency_overrides[get_current_officer] = lambda: admin_officer
    yield
    app.dependency_overrides.pop(get_current_officer, None)
