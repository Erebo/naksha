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
