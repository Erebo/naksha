"""Integration tests for NAKSHA FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from naksha.api.app import app

client = TestClient(app)


def test_health_endpoint():
    """GET /health must return 200 with status 'ok' and app metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["synthetic_mode"] is True


def test_list_records_endpoint():
    """GET /api/v1/records must return paginated synthetic records."""
    response = client.get("/api/v1/records")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert len(data["records"]) >= 5
    assert data["is_synthetic"] is True

    # Check record fields
    first = data["records"][0]
    assert "id" in first
    assert "source" in first
    assert "is_synthetic" in first


def test_list_records_filtering():
    """GET /api/v1/records supports filtering by agency and dag."""
    # Filter by agency
    res_subreg = client.get("/api/v1/records?agency=sub_registry")
    assert res_subreg.status_code == 200
    records = res_subreg.json()["records"]
    assert all(r["source"]["agency"] == "sub_registry" for r in records)

    # Filter by dag
    res_dag = client.get("/api/v1/records?dag=402")
    assert res_dag.status_code == 200
    dag_records = res_dag.json()["records"]
    assert len(dag_records) >= 3
    for r in dag_records:
        if r.get("dag_number"):
            assert r["dag_number"]["normalized_value"] == "402"


def test_get_record_by_id_success():
    """GET /api/v1/records/{record_id} returns the specific record."""
    response = client.get("/api/v1/records/SYN-MATCH-01")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "SYN-MATCH-01"
    assert data["source"]["agency"] == "sub_registry"
    assert data["dag_number"]["normalized_value"] == "402"
    assert data["khatian_number"]["normalized_value"] == "120"
    assert data["area_in_decimals"] == 6.0


def test_list_records_pagination_validation():
    """Invalid pagination limits or offsets should fail validation with 422."""
    res_bad_limit = client.get("/api/v1/records?limit=0")
    assert res_bad_limit.status_code == 422

    res_huge_limit = client.get("/api/v1/records?limit=500")
    assert res_huge_limit.status_code == 422

    res_bad_offset = client.get("/api/v1/records?offset=-1")
    assert res_bad_offset.status_code == 422


def test_get_record_by_id_not_found():
    """GET /api/v1/records/{invalid_id} returns 404 with structured detail."""
    response = client.get("/api/v1/records/NON-EXISTENT-ID")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_demo_reconciliation_endpoint():
    """GET /api/v1/records/demo returns multi-scenario reconciliation results."""
    response = client.get("/api/v1/records/demo")
    assert response.status_code == 200
    data = response.json()
    assert len(data["benchmark_scenarios"]) == 5
    assert len(data["verification_results"]) == 5
    assert data["is_synthetic"] is True

    # Check that verdicts exist in results
    verdicts = [res["verdict"] for res in data["verification_results"]]
    assert "BLOCK" in verdicts
    assert "CLEAR" in verdicts or "REVIEW" in verdicts
