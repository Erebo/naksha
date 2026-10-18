"""Synthetic Spatial Geometries and Multi-Era Survey Layers for NAKSHA 2D GIS.

All spatial geometries in this module are 100% SYNTHETIC benchmarks calibrated
around Mouza Kashimpur, Gazipur Sadar.
NOT AN OFFICIAL GOVERNMENT CADASTRAL BOUNDARY.
FOR HACKATHON DEMONSTRATION AND TESTING PURPOSES ONLY.
"""
from typing import List, Optional, Dict, Any
from naksha.models.enums import SpatialLayerType, SurveyEra, TaxPaymentStatus
from naksha.models.canonical import (
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    SpatialConflictZone,
    SurveyLayerSnapshot,
)
from naksha.spatial.engine import calculate_polygon_area, calculate_overlap

DISCLAIMER = "SYNTHETIC BENCHMARK GEOMETRY: NOT AN OFFICIAL GOVERNMENT CADASTRAL BOUNDARY"

# ==============================================================================
# Calibrated Synthetic Coordinate Rings in WGS 84 (EPSG:4326)
# ==============================================================================

# 1. DLRS Surveyed Boundary (BS Dag 402 ground-truth: 5.1 decimals = ~206.4 m²)
DLRS_BS_402_COORDS = [
    [
        [90.350436, 23.984992],
        [90.350433, 23.985125],
        [90.350296, 23.985123],
        [90.350299, 23.984990],
        [90.350436, 23.984992],
    ]
]

# 2. Registered Deed Claim (Deed DEED-2024-DH-402: 6.0 decimals claimed, overlaps into canal)
DEED_CLAIM_402_COORDS = [
    [
        [90.350436, 23.984992],
        [90.350433, 23.985149],
        [90.350296, 23.985146],
        [90.350299, 23.984990],
        [90.350436, 23.984992],
    ]
]

# 3. Ancestral CS Dag 88 Footprint (Large historical parcel before family subdivision: ~18.0 dec)
CS_DAG_88_COORDS = [
    [
        [90.350496, 23.984939],
        [90.350491, 23.985192],
        [90.350236, 23.985187],
        [90.350241, 23.984935],
        [90.350496, 23.984939],
    ]
]

# 4. Government Khas Canal Strip (Public canal running along north edge of plot)
KHAS_CANAL_COORDS = [
    [
        [90.350492, 23.985126],
        [90.350491, 23.985192],
        [90.350246, 23.985187],
        [90.350247, 23.985122],
        [90.350492, 23.985126],
    ]
]

# 5. Neighboring Parcel: BS Dag 401 (West neighbor: ~4.4 decimals, Tax Status: Paid)
NEIGHBOR_401_COORDS = [
    [
        [90.350299, 23.984990],
        [90.350296, 23.985123],
        [90.350178, 23.985121],
        [90.350181, 23.984988],
        [90.350299, 23.984990],
    ]
]

# 6. Neighboring Parcel: BS Dag 403 (South neighbor: ~5.5 decimals, Tax Status: Arrears)
NEIGHBOR_403_COORDS = [
    [
        [90.350439, 23.984848],
        [90.350436, 23.984992],
        [90.350299, 23.984990],
        [90.350302, 23.984845],
        [90.350439, 23.984848],
    ]
]


def get_synthetic_conflict_zone(parcel_id: str = "par-8f92-bd04-syn") -> Optional[SpatialConflictZone]:
    """Computes the exact conflict zone where the deed claim overlaps the public Khas canal."""
    claim_geom = GeoJSONGeometry(type="Polygon", coordinates=DEED_CLAIM_402_COORDS)
    khas_geom = GeoJSONGeometry(type="Polygon", coordinates=KHAS_CANAL_COORDS)

    overlap_dec, overlap_sqm, inter_geom = calculate_overlap(claim_geom, khas_geom)
    if overlap_dec <= 0.0 or inter_geom is None:
        return None

    return SpatialConflictZone(
        conflict_type="KHAS_CANAL_OVERLAP",
        area_in_decimals=overlap_dec,
        area_in_sq_meters=overlap_sqm,
        geometry=inter_geom,
        description=(
            f"কাগজে দাবিকৃত ৬.০০ শতকের মধ্যে ০.৯০ শতক সরকারি খাস খাল/জলমহালের সীমানার অন্তর্ভুক্ত "
            f"(Paper claim of 6.00 dec overlaps public Khas canal by {overlap_dec:.2f} dec / {overlap_sqm:.1f} m²)."
        ),
    )


def get_synthetic_parcel_layers(parcel_id: str = "par-8f92-bd04-syn") -> List[SurveyLayerSnapshot]:
    """Builds the 4-layer 2D GIS visual stack for the Naksha Side Panel:

    Layer 1: Ancestral CS Dag 88 footprint (historical root)
    Layer 2: Deed Claim boundary (6.0 decimals claimed)
    Layer 3: DLRS surveyed ground truth (5.1 decimals polygon)
    Layer 4: Computed conflict zone (0.9 decimals Khas canal overlap)
    """
    layers: List[SurveyLayerSnapshot] = []

    # 1. Ancestral CS Dag 88 Footprint
    cs_geom = GeoJSONGeometry(type="Polygon", coordinates=CS_DAG_88_COORDS)
    cs_dec, cs_sqm = calculate_polygon_area(cs_geom)
    layers.append(
        SurveyLayerSnapshot(
            layer_type=SpatialLayerType.ANCESTRAL_FOOTPRINT,
            layer_name="১. সিএস ৮৮ দাগের পৈত্রিক সীমানা (Ancestral CS 88 Footprint)",
            survey_era=SurveyEra.CS,
            geometry=cs_geom,
            properties={
                "dag_number": "88",
                "survey_era": "CS",
                "recorded_area_decimals": 18.0,
                "calculated_area_decimals": cs_dec,
                "calculated_area_sqm": cs_sqm,
                "mouza": "কাশিমপুর (Kashimpur)",
                "color": "#8b5cf6",  # Purple
                "stroke_style": "dashed",
                "description": "১৯৪০ সালের মূল সিএস ৮৮ দাগের অখণ্ড পৈত্রিক সীমানা",
            },
        )
    )

    # 2. Registered Deed Claim Footprint
    deed_geom = GeoJSONGeometry(type="Polygon", coordinates=DEED_CLAIM_402_COORDS)
    deed_dec, deed_sqm = calculate_polygon_area(deed_geom)
    layers.append(
        SurveyLayerSnapshot(
            layer_type=SpatialLayerType.DEED_CLAIM,
            layer_name="২. সাব-রেজিস্ট্রি দলিলের দাবি (Deed Claim 6.00 dec)",
            survey_era=SurveyEra.BS,
            geometry=deed_geom,
            properties={
                "dag_number": "402",
                "deed_number": "DEED-2024-DH-402",
                "claimed_area_decimals": 6.00,
                "calculated_area_decimals": deed_dec,
                "calculated_area_sqm": deed_sqm,
                "color": "#3b82f6",  # Blue
                "stroke_style": "solid",
                "description": "দলিল নং DEED-2024-DH-402 অনুযায়ী দাবিকৃত সীমানা",
            },
        )
    )

    # 3. DLRS Ground Truth Polygon
    dlrs_geom = GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS)
    dlrs_dec, dlrs_sqm = calculate_polygon_area(dlrs_geom)
    layers.append(
        SurveyLayerSnapshot(
            layer_type=SpatialLayerType.GROUND_TRUTH,
            layer_name="৩. ডিএলআরএস জরিপকৃত প্রকৃত নকশা (DLRS Ground Truth 5.10 dec)",
            survey_era=SurveyEra.BS,
            geometry=dlrs_geom,
            properties={
                "dag_number": "402",
                "khatian_number": "120",
                "survey_era": "BS",
                "calculated_area_decimals": dlrs_dec,
                "calculated_area_sqm": dlrs_sqm,
                "color": "#10b981",  # Green
                "stroke_style": "solid",
                "description": "ডিএলআরএস ডিজিটাল বিএস জরিপকৃত প্রকৃত মাঠ সীমানা",
            },
        )
    )

    # 4. Conflict Zone (Khas Overlap)
    conflict = get_synthetic_conflict_zone(parcel_id)
    if conflict and conflict.geometry:
        layers.append(
            SurveyLayerSnapshot(
                layer_type=SpatialLayerType.CONFLICT_ZONE,
                layer_name="৪. বিরোধপূর্ণ এলাকা (Computed Conflict Zone 0.90 dec)",
                survey_era=SurveyEra.BS,
                geometry=conflict.geometry,
                properties={
                    "conflict_type": conflict.conflict_type,
                    "area_in_decimals": conflict.area_in_decimals,
                    "area_in_sq_meters": conflict.area_in_sq_meters,
                    "color": "#ef4444",  # Red alert
                    "fill_opacity": 0.6,
                    "stroke_style": "solid",
                    "description": conflict.description,
                },
            )
        )

    # 5. Public Khas Canal Boundary Layer
    khas_geom = GeoJSONGeometry(type="Polygon", coordinates=KHAS_CANAL_COORDS)
    khas_dec, khas_sqm = calculate_polygon_area(khas_geom)
    layers.append(
        SurveyLayerSnapshot(
            layer_type=SpatialLayerType.RESTRICTED_KHAS,
            layer_name="সরকারি খাস নিষ্কাশন খাল (Public Khas Canal)",
            geometry=khas_geom,
            properties={
                "class": "khas",
                "name": "কাশিমপুর সরকারি নিষ্কাশন খাল",
                "area_in_decimals": khas_dec,
                "color": "#0ea5e9",  # Cyan / Water
                "description": "সরকারি খাস জলমহাল / নিষ্কাশন খাল (অহস্তান্তরযোগ্য)",
            },
        )
    )

    return layers


def get_synthetic_neighbor_parcels(parcel_id: str = "par-8f92-bd04-syn") -> GeoJSONFeatureCollection:
    """Returns surrounding/neighboring plots for the LD Tax context map."""
    features: List[GeoJSONFeature] = []

    # Target Plot: BS 402
    dlrs_geom = GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS)
    features.append(
        GeoJSONFeature(
            id="BS-402",
            geometry=dlrs_geom,
            properties={
                "dag_number": "402",
                "khatian_number": "120",
                "owner_name": "মোঃ আব্দুল করিম (Md. Abdul Karim)",
                "area_decimals": 5.10,
                "tax_status": TaxPaymentStatus.PAID.value,
                "tax_status_label": "পরিশোধিত (Paid)",
                "is_target_parcel": True,
                "holding_number": "H-402",
            },
        )
    )

    # West Neighbor: BS 401
    n401_geom = GeoJSONGeometry(type="Polygon", coordinates=NEIGHBOR_401_COORDS)
    features.append(
        GeoJSONFeature(
            id="BS-401",
            geometry=n401_geom,
            properties={
                "dag_number": "401",
                "khatian_number": "88",
                "owner_name": "মোঃ রহিম শেখ (Md. Rahim Sheikh)",
                "area_decimals": 4.37,
                "tax_status": TaxPaymentStatus.PAID.value,
                "tax_status_label": "পরিশোধিত (Paid)",
                "is_target_parcel": False,
                "holding_number": "H-401",
            },
        )
    )

    # South Neighbor: BS 403
    n403_geom = GeoJSONGeometry(type="Polygon", coordinates=NEIGHBOR_403_COORDS)
    features.append(
        GeoJSONFeature(
            id="BS-403",
            geometry=n403_geom,
            properties={
                "dag_number": "403",
                "khatian_number": "125",
                "owner_name": "আব্দুল মজিদ (Abdul Majid)",
                "area_decimals": 5.53,
                "tax_status": TaxPaymentStatus.ARREARS.value,
                "tax_status_label": "বকেয়া (Arrears)",
                "is_target_parcel": False,
                "holding_number": "H-403",
            },
        )
    )

    return GeoJSONFeatureCollection(
        features=features,
        metadata={
            "target_parcel_id": parcel_id,
            "mouza": "কাশিমপুর (Kashimpur)",
            "disclaimer": DISCLAIMER,
        },
    )


def get_synthetic_all_parcels_geojson() -> GeoJSONFeatureCollection:
    """Returns a unified GeoJSON FeatureCollection of all synthetic parcels."""
    neighbors = get_synthetic_neighbor_parcels()
    return neighbors
