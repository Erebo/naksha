"""Runtime Route Protection Test Suite for NAKSHA.

Enumerates all routes registered in the FastAPI app at runtime to ensure:
1. Every /api/v1/* route strictly returns HTTP 401 Unauthorized without a token.
2. No dependency override is active during these checks.
3. Public routes are strictly restricted to the authorized allowlist:
   /health, /docs, /redoc, /openapi.json, /auth/verify-officer, /, /map, /portals/*, /static/*.
4. Any new route added under /api/v1/ without authentication will fail this test suite.
"""
import pytest
from fastapi.testclient import TestClient
from naksha.api.app import app

client = TestClient(app)

ALLOWED_PUBLIC_EXACT_ROUTES = {
    "/health",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
    "/auth/verify-officer",
    "/",
    "/map",
    "/static",
}

ALLOWED_PUBLIC_PREFIXES = (
    "/portals/",
    "/static/",
    "/docs",
)

VALID_DUMMY_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [90.350436, 23.984992],
            [90.350433, 23.985125],
            [90.350296, 23.985123],
            [90.350299, 23.984990],
            [90.350436, 23.984992],
        ]
    ],
}

POST_BODIES = {
    "/api/v1/spatial/calculate-area": {
        "geometry": VALID_DUMMY_POLYGON,
    },
    "/api/v1/spatial/calculate-overlap": {
        "geometry_a": VALID_DUMMY_POLYGON,
        "geometry_b": VALID_DUMMY_POLYGON,
    },
}


def get_all_routes():
    """Flattens and returns all registered route objects including nested routers."""
    routes = []
    for r in app.routes:
        if hasattr(r, "original_router"):
            routes.extend(r.original_router.routes)
        elif hasattr(r, "routes"):
            routes.extend(r.routes)
        else:
            routes.append(r)
    return routes


def _is_public_route(path: str) -> bool:
    if path in ALLOWED_PUBLIC_EXACT_ROUTES:
        return True
    return any(path.startswith(prefix) for prefix in ALLOWED_PUBLIC_PREFIXES)


def _resolve_test_path(raw_path: str) -> str:
    path = raw_path
    if "{parcel_id}" in path:
        path = path.replace("{parcel_id}", "par-8f92-bd04-syn")
    if "{record_id}" in path:
        path = path.replace("{record_id}", "SYN-MATCH-01")
    return path


@pytest.fixture(autouse=True)
def ensure_clean_overrides():
    """Ensure no dependency overrides leak into route protection tests."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_public_routes_strictly_allowlisted():
    """Ensures that all non-/api/v1/ routes belong strictly to the approved public allowlist."""
    for route in get_all_routes():
        path = getattr(route, "path", None)
        if not path:
            continue
        if path.startswith("/api/v1/"):
            continue
        assert _is_public_route(path), f"Disallowed unexpected public route found: '{path}'"


def test_all_api_v1_routes_require_authentication():
    """Enumerates every /api/v1/* route and asserts that unauthenticated requests return 401."""
    api_routes_tested = 0

    for route in get_all_routes():
        path = getattr(route, "path", None)
        if not path or not path.startswith("/api/v1/"):
            continue

        methods = getattr(route, "methods", set())
        # Filter standard HTTP methods to test (ignore HEAD, OPTIONS)
        callable_methods = [m for m in methods if m in ("GET", "POST", "PUT", "DELETE", "PATCH")]

        resolved_path = _resolve_test_path(path)

        for method in callable_methods:
            api_routes_tested += 1
            body = POST_BODIES.get(path, None)

            # Ensure dependency overrides are clean
            assert len(app.dependency_overrides) == 0

            # Execute unauthenticated request
            if method == "GET":
                res = client.get(resolved_path)
            elif method == "POST":
                res = client.post(resolved_path, json=body or {})
            elif method == "PUT":
                res = client.put(resolved_path, json=body or {})
            elif method == "DELETE":
                res = client.delete(resolved_path)
            elif method == "PATCH":
                res = client.patch(resolved_path, json=body or {})
            else:
                continue

            # Must return exactly 401 (not 404, not 422, not 200, not 403)
            assert res.status_code == 401, (
                f"Route [{method}] '{path}' (resolved: '{resolved_path}') did not return 401 when unauthenticated! "
                f"Got status {res.status_code}: {res.text}"
            )

    # Sanity check that all 13 protected endpoints were discovered and tested
    assert api_routes_tested == 13, f"Expected 13 API routes tested, but tested {api_routes_tested}."
