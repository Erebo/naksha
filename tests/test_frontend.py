"""Tests for the Bangla-First 2D GIS Interactive Frontend."""
from fastapi.testclient import TestClient
from naksha.api.app import app

client = TestClient(app)


def test_index_serves_html():
    """GET / serves the Bangla-first GIS side panel HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    # Verify Bengali title and branding
    assert "নকশা (NAKSHA)" in html
    assert "ক্যানোনিকাল স্প্যাশিয়াল ইঞ্জিন" in html
    # Verify critical DOM elements
    assert 'id="map"' in html
    assert 'id="layer-toggles"' in html
    assert 'id="verdict-badge"' in html
    assert 'id="findings-list"' in html
    assert 'id="neighbor-list"' in html
    # Verify synthetic disclaimer in HTML
    assert "নমুনা তথ্য — বাস্তব সরকারি নথি নয়" in html


def test_map_alias_route():
    """GET /map serves the same GIS application."""
    response = client.get("/map")
    assert response.status_code == 200
    assert "নকশা" in response.text


def test_static_assets_served():
    """Static CSS and JavaScript files are accessible."""
    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]
    assert "--font-bangla" in css_res.text

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "par-8f92-bd04-syn" in js_res.text
    assert "LAYER_STYLES" in js_res.text


def test_frontend_api_data_contract():
    """Ensure all API endpoints consumed by app.js return valid payloads."""
    # 1. Survey layers
    layers_res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/layers")
    assert layers_res.status_code == 200
    layers = layers_res.json()
    assert len(layers) >= 4
    types = [l["layer_type"] for l in layers]
    assert "ancestral_footprint" in types
    assert "deed_claim" in types
    assert "ground_truth" in types
    assert "conflict_zone" in types

    # 2. Neighbors
    neighbors_res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/neighbors")
    assert neighbors_res.status_code == 200
    features = neighbors_res.json()["features"]
    assert len(features) >= 3

    # 3. Conflict zone
    conflict_res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/conflicts")
    assert conflict_res.status_code == 200
    conflict = conflict_res.json()
    assert conflict["area_in_decimals"] >= 0.85
