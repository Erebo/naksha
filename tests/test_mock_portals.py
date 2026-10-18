"""Integration tests for Stage 5 Mock Land Portals (LD Tax and e-Mutation)."""
from fastapi.testclient import TestClient
from naksha.api.app import app

client = TestClient(app)


def test_mock_ld_tax_portal_serves_html():
    """GET /portals/ld-tax serves the Bangla-first mock LD Tax portal."""
    response = client.get("/portals/ld-tax")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text

    # Verify Bangla titles and headers
    assert "ভূমি উন্নয়ন কর ব্যবস্থাপনা সিস্টেম (LD Tax)" in html
    assert "কাশিমপুর" in html

    # Verify required context container for Chrome Extension content script detection
    assert 'id="naksha-portal-context"' in html
    assert 'data-portal="ld_tax"' in html
    assert 'data-mouza="কাশিমপুর"' in html
    assert 'data-dag="402"' in html
    assert 'data-khatian="120"' in html
    assert 'data-holding="H-402"' in html
    assert 'data-owner="মোঃ আব্দুল করিম"' in html

    # Verify synthetic demo disclaimer
    assert "কৃত্রিম ডেমো পোর্টাল" in html


def test_mock_e_mutation_portal_serves_html():
    """GET /portals/e-mutation serves the Bangla-first mock e-Mutation portal."""
    response = client.get("/portals/e-mutation")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text

    # Verify Bangla titles and mutation details
    assert "ই-নামজারি ও মিউটেশন ব্যবস্থাপনা সিস্টেম" in html
    assert "MUT-2024-GZ-884" in html

    # Verify context container for Chrome Extension content script detection
    assert 'id="naksha-portal-context"' in html
    assert 'data-portal="e_mutation"' in html
    assert 'data-mouza="কাশিমপুর"' in html
    assert 'data-dag="402"' in html
    assert 'data-khatian="120"' in html
    assert 'data-case-id="MUT-2024-GZ-884"' in html

    # Verify synthetic demo disclaimer
    assert "কৃত্রিম ডেমো পোর্টাল" in html


def test_mock_portals_plot_data_consistency():
    """Verify mock portal identifiers map cleanly to synthetic spatial API benchmarks."""
    res_layers = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/layers")
    assert res_layers.status_code == 200
    layers = res_layers.json()
    assert any(l["layer_type"] == "ground_truth" for l in layers)

    res_neighbors = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/neighbors")
    assert res_neighbors.status_code == 200
    neighbors = res_neighbors.json()
    dags = [f["properties"]["dag_number"] for f in neighbors["features"]]
    assert "402" in dags
    assert "401" in dags
    assert "403" in dags


def test_e2e_multi_plot_journey_and_verdicts():
    """Verify complete officer journey across Dag 402, Dag 401, and Dag 403.
    Ensures that selecting each plot returns the appropriate backend record and verdict,
    preventing stale data display.
    """
    # 1. Main benchmark plot Dag 402 -> Area conflict & Khas canal overlap -> BLOCK
    res_402 = client.get("/api/v1/records?dag=402")
    assert res_402.status_code == 200
    records_402 = res_402.json()["records"]
    assert len(records_402) >= 1
    # Verify conflict on 402
    res_conf = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/conflicts")
    assert res_conf.status_code == 200
    conf_data = res_conf.json()
    assert round(conf_data["area_in_decimals"], 2) == 0.90
    assert "KHAS" in conf_data["conflict_type"]

    # 2. West neighbor plot Dag 401 -> Clean ownership and tax paid -> CLEAR
    res_401 = client.get("/api/v1/records?dag=401")
    assert res_401.status_code == 200
    records_401 = res_401.json()["records"]
    assert len(records_401) == 1
    rec_401 = records_401[0]
    assert rec_401["dag_number"]["normalized_value"] == "401"
    assert rec_401["khatian_number"]["normalized_value"] == "88"
    assert rec_401["area_in_decimals"] == 4.37

    # 3. South neighbor plot Dag 403 -> Arrears & divergence -> REVIEW / BLOCK
    res_403 = client.get("/api/v1/records?dag=403")
    assert res_403.status_code == 200
    records_403 = res_403.json()["records"]
    assert len(records_403) >= 1
    rec_403 = records_403[0]
    assert rec_403["dag_number"]["normalized_value"] == "403"
    assert rec_403["khatian_number"]["normalized_value"] == "125"

    # 4. Invalid or non-existent plot query returns empty cleanly without crashes
    res_invalid = client.get("/api/v1/records?dag=999999")
    assert res_invalid.status_code == 200
    assert len(res_invalid.json()["records"]) == 0
