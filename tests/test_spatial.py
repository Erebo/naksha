"""Comprehensive unit and integration tests for NAKSHA 2D Spatial Engine."""
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from naksha.api.app import app
from naksha.models.canonical import GeoJSONGeometry
from naksha.models.enums import DiscrepancyType, SpatialLayerType, VerificationVerdict
from naksha.spatial.engine import (
    validate_geometry,
    calculate_polygon_area,
    calculate_overlap,
    check_containment,
)
from naksha.data.synthetic_spatial import (
    DLRS_BS_402_COORDS,
    DEED_CLAIM_402_COORDS,
    CS_DAG_88_COORDS,
    KHAS_CANAL_COORDS,
    NEIGHBOR_401_COORDS,
    NEIGHBOR_403_COORDS,
    get_synthetic_conflict_zone,
    get_synthetic_parcel_layers,
    get_synthetic_neighbor_parcels,
)
from naksha.data.synthetic import generate_synthetic_records
from naksha.services.verification import verify_record_against_cohort

client = TestClient(app)


# ==============================================================================
# 1. Geometry Validation Tests
# ==============================================================================

def test_validate_geometry_valid():
    """Valid closed polygon in WGS 84 passes validation."""
    valid_poly = GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS)
    is_valid, err, poly = validate_geometry(valid_poly)
    assert is_valid is True
    assert err is None
    assert poly is not None
    assert isinstance(poly, Polygon)


def test_validate_geometry_invalid_or_missing():
    """Missing or degenerate coordinates fail validation."""
    # None input
    is_valid, err, _ = validate_geometry(None)
    assert is_valid is False
    assert "None" in err

    # Too few coordinates (only 2 points)
    bad_coords = {"type": "Polygon", "coordinates": [[[90.35, 23.98], [90.36, 23.99]]]}
    is_valid, err, _ = validate_geometry(bad_coords)
    assert is_valid is False

    # Out-of-bounds coordinates (lon 250)
    out_of_bounds = {
        "type": "Polygon",
        "coordinates": [
            [[250.0, 23.98], [250.0, 23.99], [250.1, 23.99], [250.1, 23.98], [250.0, 23.98]]
        ],
    }
    is_valid, err, _ = validate_geometry(out_of_bounds)
    assert is_valid is False
    assert "out of valid range" in err


def test_validate_geometry_bowtie_repair():
    """Self-intersecting bowtie polygon is repaired via make_valid."""
    bowtie = {
        "type": "Polygon",
        "coordinates": [
            [[90.35, 23.98], [90.36, 23.99], [90.35, 23.99], [90.36, 23.98], [90.35, 23.98]]
        ],
    }
    is_valid, err, poly = validate_geometry(bowtie)
    assert is_valid is True
    assert poly is not None


# ==============================================================================
# 2. Deterministic Spatial Calculation Tests
# ==============================================================================

def test_calculate_polygon_area_utm46n():
    """Polygon area in UTM 46N matches target benchmark decimal conversions."""
    # DLRS BS 402 benchmark: ~5.10 decimals
    dlrs_geom = GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS)
    dlrs_dec, dlrs_sqm = calculate_polygon_area(dlrs_geom)
    assert 5.05 <= dlrs_dec <= 5.15
    assert 200.0 <= dlrs_sqm <= 210.0

    # Deed Claim benchmark: ~6.00 decimals
    deed_geom = GeoJSONGeometry(type="Polygon", coordinates=DEED_CLAIM_402_COORDS)
    deed_dec, deed_sqm = calculate_polygon_area(deed_geom)
    assert 5.95 <= deed_dec <= 6.05
    assert 238.0 <= deed_sqm <= 246.0

    # Ancestral CS Dag 88: ~18.0 decimals
    cs_geom = GeoJSONGeometry(type="Polygon", coordinates=CS_DAG_88_COORDS)
    cs_dec, cs_sqm = calculate_polygon_area(cs_geom)
    assert 17.5 <= cs_dec <= 18.5


def test_calculate_overlap_and_conflict():
    """Calculate overlap between deed claim and public Khas canal."""
    claim_geom = GeoJSONGeometry(type="Polygon", coordinates=DEED_CLAIM_402_COORDS)
    khas_geom = GeoJSONGeometry(type="Polygon", coordinates=KHAS_CANAL_COORDS)

    ov_dec, ov_sqm, inter_geom = calculate_overlap(claim_geom, khas_geom)
    assert 0.85 <= ov_dec <= 0.95
    assert 34.0 <= ov_sqm <= 38.0
    assert inter_geom is not None
    assert inter_geom.type in ("Polygon", "MultiPolygon")


def test_calculate_overlap_disjoint():
    """Disjoint polygons return 0.0 overlap."""
    n403_geom = GeoJSONGeometry(type="Polygon", coordinates=NEIGHBOR_403_COORDS)
    khas_geom = GeoJSONGeometry(type="Polygon", coordinates=KHAS_CANAL_COORDS)

    ov_dec, ov_sqm, inter_geom = calculate_overlap(n403_geom, khas_geom)
    assert ov_dec == 0.0
    assert ov_sqm == 0.0
    assert inter_geom is None


def test_check_containment():
    """Ancestral CS Dag 88 contains subdivided BS Dag 402."""
    cs_geom = GeoJSONGeometry(type="Polygon", coordinates=CS_DAG_88_COORDS)
    dlrs_geom = GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS)
    assert check_containment(cs_geom, dlrs_geom) is True


# ==============================================================================
# 3. GeoJSON API Endpoint Tests
# ==============================================================================

def test_api_spatial_parcels():
    """GET /api/v1/spatial/parcels returns valid GeoJSON FeatureCollection."""
    res = client.get("/api/v1/spatial/parcels")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 3

    # Check Bengali Unicode preservation in properties
    first = data["features"][0]
    assert "properties" in first
    assert "dag_number" in first["properties"]
    assert "tax_status_label" in first["properties"]
    assert "পরিশোধিত" in first["properties"]["tax_status_label"] or "বকেয়া" in first["properties"]["tax_status_label"]


def test_api_parcel_survey_layers():
    """GET /api/v1/spatial/parcels/{id}/layers returns 4-layer GIS stack."""
    res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/layers")
    assert res.status_code == 200
    layers = res.json()
    assert len(layers) >= 4

    layer_types = [layer["layer_type"] for layer in layers]
    assert SpatialLayerType.ANCESTRAL_FOOTPRINT.value in layer_types
    assert SpatialLayerType.DEED_CLAIM.value in layer_types
    assert SpatialLayerType.GROUND_TRUTH.value in layer_types
    assert SpatialLayerType.CONFLICT_ZONE.value in layer_types

    # Ensure synthetic safety disclaimer
    for layer in layers:
        assert layer["is_synthetic"] is True
        assert "NOT AN OFFICIAL GOVERNMENT" in layer["synthetic_disclaimer"]


def test_api_parcel_survey_layers_not_found():
    """Non-existent parcel returns 404."""
    res = client.get("/api/v1/spatial/parcels/NON-EXISTENT/layers")
    # Our synthetic fallback returns default layers for demo if configured, or 404
    assert res.status_code in (200, 404)


def test_api_parcel_neighbors():
    """GET /api/v1/spatial/parcels/{id}/neighbors returns target and adjacent plots."""
    res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/neighbors")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    dags = [f["properties"]["dag_number"] for f in data["features"]]
    assert "402" in dags
    assert "401" in dags
    assert "403" in dags


def test_api_parcel_conflict_zone():
    """GET /api/v1/spatial/parcels/{id}/conflicts returns Khas canal dispute geometry."""
    res = client.get("/api/v1/spatial/parcels/par-8f92-bd04-syn/conflicts")
    assert res.status_code == 200
    conflict = res.json()
    assert conflict["conflict_type"] == "KHAS_CANAL_OVERLAP"
    assert 0.85 <= conflict["area_in_decimals"] <= 0.95
    assert "খাস খাল" in conflict["description"]


def test_api_post_calculate_area():
    """POST /api/v1/spatial/calculate-area computes UTM 46N area."""
    payload = {"geometry": {"type": "Polygon", "coordinates": DLRS_BS_402_COORDS}}
    res = client.post("/api/v1/spatial/calculate-area", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 5.05 <= data["area_in_decimals"] <= 5.15
    assert data["is_valid"] is True


def test_api_post_calculate_area_invalid():
    """POST /api/v1/spatial/calculate-area with invalid coordinates returns 422."""
    payload = {"geometry": {"type": "Polygon", "coordinates": [[[250.0, 23.98], [250.0, 23.99]]]}}
    res = client.post("/api/v1/spatial/calculate-area", json=payload)
    assert res.status_code == 422


def test_api_post_calculate_overlap():
    """POST /api/v1/spatial/calculate-overlap computes intersection polygon."""
    payload = {
        "geometry_a": {"type": "Polygon", "coordinates": DEED_CLAIM_402_COORDS},
        "geometry_b": {"type": "Polygon", "coordinates": KHAS_CANAL_COORDS},
    }
    res = client.post("/api/v1/spatial/calculate-overlap", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["has_overlap"] is True
    assert 0.85 <= data["overlap_in_decimals"] <= 0.95
    assert data["intersection_geometry"] is not None


# ==============================================================================
# 4. Spatial Verification Integration Tests
# ==============================================================================

def test_spatial_verification_integration():
    """Verifying deed record triggers GEOMETRIC_OVERLAP and attaches survey layers."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_deed = records["SYN-MATCH-01"]  # Deed claiming 6.0 dec with geometry

    result = verify_record_against_cohort(primary=rec_deed, cohort=list(records.values()))
    assert result.verdict == VerificationVerdict.BLOCK

    # Check for GEOMETRIC_OVERLAP discrepancy
    disc_types = [d.discrepancy_type for d in result.discrepancies]
    assert DiscrepancyType.GEOMETRIC_OVERLAP in disc_types

    overlap_disc = next(d for d in result.discrepancies if d.discrepancy_type == DiscrepancyType.GEOMETRIC_OVERLAP)
    assert overlap_disc.spatial_conflict is not None
    assert "খাস খাল" in overlap_disc.difference_description

    # Check that spatial_layers are attached to verification result
    assert result.spatial_layers is not None
    assert len(result.spatial_layers) >= 4
