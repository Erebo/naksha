"""Deterministic Spatial Engine for NAKSHA.

Implements pure geometric operations, area calculations in UTM 46N (EPSG:32646),
polygon validations, overlap/intersection detections, and GeoJSON conversions.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import pyproj
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from shapely.validation import make_valid
import shapely

from naksha.models.canonical import GeoJSONGeometry, SpatialConflictZone
from naksha.normalization.area import DECIMAL_TO_SQ_METERS

import numpy as np

# Forward & Inverse Coordinate Transformers: WGS84 (EPSG:4326) <-> UTM Zone 46N (EPSG:32646)
_TRANSFORMER_4326_TO_32646 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32646", always_xy=True)
_TRANSFORMER_32646_TO_4326 = pyproj.Transformer.from_crs("EPSG:32646", "EPSG:4326", always_xy=True)


def _transform_wgs84_to_utm(geom: Union[Polygon, MultiPolygon]) -> Union[Polygon, MultiPolygon]:
    """Projects a Shapely geometry from WGS84 (EPSG:4326) to UTM Zone 46N (EPSG:32646)."""
    def _proj(coords):
        x, y = _TRANSFORMER_4326_TO_32646.transform(coords[:, 0], coords[:, 1])
        return np.column_stack((x, y))
    return shapely.transform(geom, _proj)


def _transform_utm_to_wgs84(geom: Union[Polygon, MultiPolygon]) -> Union[Polygon, MultiPolygon]:
    """Projects a Shapely geometry from UTM Zone 46N (EPSG:32646) to WGS84 (EPSG:4326)."""
    def _proj(coords):
        x, y = _TRANSFORMER_32646_TO_4326.transform(coords[:, 0], coords[:, 1])
        return np.column_stack((x, y))
    return shapely.transform(geom, _proj)


def to_shapely_polygon(geom: Union[Polygon, GeoJSONGeometry, Dict[str, Any], None]) -> Optional[Polygon]:
    """Converts a GeoJSONGeometry object or dictionary into a Shapely Polygon."""
    if geom is None:
        return None
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, GeoJSONGeometry):
        d = geom.model_dump()
        s = shape(d)
        return s if isinstance(s, Polygon) else None
    if isinstance(geom, dict):
        s = shape(geom)
        return s if isinstance(s, Polygon) else None
    return None


def to_geojson_geometry(poly: Union[Polygon, MultiPolygon, None]) -> Optional[GeoJSONGeometry]:
    """Converts a Shapely geometry back to a canonical GeoJSONGeometry model."""
    if poly is None or poly.is_empty:
        return None
    geo_dict = mapping(poly)
    return GeoJSONGeometry(
        type=geo_dict["type"],
        coordinates=geo_dict["coordinates"],
    )


def validate_geometry(
    geom_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any], None]
) -> Tuple[bool, Optional[str], Optional[Polygon]]:
    """Validates a polygon geometry:

    - Checks that coordinates form a closed ring with at least 4 points.
    - Validates bounds within global lat/long limits.
    - Evaluates topological validity (preventing self-intersections or bowtie polygons).
    - If self-intersecting, attempts repair via `make_valid`.

    Returns:
        (is_valid, error_message, validated_or_repaired_polygon)
    """
    if geom_input is None:
        return False, "Geometry input is None or empty.", None

    try:
        poly = to_shapely_polygon(geom_input)
    except Exception as e:
        return False, f"Failed to parse geometry structure: {str(e)}", None

    if poly is None or poly.is_empty:
        return False, "Parsed geometry is not a valid non-empty Polygon.", None

    # Check minimum coordinates
    coords = list(poly.exterior.coords)
    if len(coords) < 4:
        return False, "Polygon exterior ring must have at least 4 coordinate vertices.", None

    # Check coordinate bounds (Longitude in [-180, 180], Latitude in [-90, 90])
    min_x, min_y, max_x, max_y = poly.bounds
    if not (-180.0 <= min_x <= 180.0 and -180.0 <= max_x <= 180.0):
        return False, f"Longitude coordinates out of valid range [-180, 180]: [{min_x}, {max_x}].", None
    if not (-90.0 <= min_y <= 90.0 and -90.0 <= max_y <= 90.0):
        return False, f"Latitude coordinates out of valid range [-90, 90]: [{min_y}, {max_y}].", None

    # Topological validity
    if not poly.is_valid:
        repaired = make_valid(poly)
        if isinstance(repaired, Polygon):
            return True, "Polygon had topological anomalies (e.g. self-intersection) and was repaired.", repaired
        elif isinstance(repaired, MultiPolygon) and len(repaired.geoms) > 0:
            largest = max(repaired.geoms, key=lambda g: g.area)
            return True, "Self-intersecting geometry converted to primary polygon.", largest
        else:
            return False, "Topologically invalid polygon could not be normalized into a single polygon.", None

    return True, None, poly


def calculate_polygon_area(
    geom_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any]],
    precision_decimals: int = 4,
    precision_sqm: int = 2,
) -> Tuple[float, float]:
    """Calculates ground area deterministically by projecting WGS84 coordinates

    into the national UTM Zone 46N (EPSG:32646) metric projection.

    Returns:
        (area_in_decimals, area_in_sq_meters)
    """
    valid, err, poly = validate_geometry(geom_input)
    if not valid or poly is None:
        raise ValueError(f"Cannot calculate area: {err}")

    # Project to UTM 46N
    utm_poly = _transform_wgs84_to_utm(poly)
    area_sqm = utm_poly.area
    area_decimals = area_sqm / DECIMAL_TO_SQ_METERS

    return round(area_decimals, precision_decimals), round(area_sqm, precision_sqm)


def calculate_overlap(
    poly_a_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any]],
    poly_b_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any]],
) -> Tuple[float, float, Optional[GeoJSONGeometry]]:
    """Calculates the geometric intersection / overlap between two polygons.

    Returns:
        (overlap_decimals, overlap_sq_meters, intersection_geometry)
    """
    val_a, err_a, poly_a = validate_geometry(poly_a_input)
    if not val_a or poly_a is None:
        raise ValueError(f"Invalid primary polygon: {err_a}")

    val_b, err_b, poly_b = validate_geometry(poly_b_input)
    if not val_b or poly_b is None:
        raise ValueError(f"Invalid secondary polygon: {err_b}")

    if not poly_a.intersects(poly_b):
        return 0.0, 0.0, None

    intersection = poly_a.intersection(poly_b)
    if intersection.is_empty or intersection.area == 0:
        return 0.0, 0.0, None

    # Calculate metric area in UTM 46N
    utm_intersection = _transform_wgs84_to_utm(intersection)
    area_sqm = utm_intersection.area
    area_dec = area_sqm / DECIMAL_TO_SQ_METERS

    geojson_geom = to_geojson_geometry(intersection)
    return round(area_dec, 4), round(area_sqm, 2), geojson_geom


def check_containment(
    container_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any]],
    contained_input: Union[Polygon, GeoJSONGeometry, Dict[str, Any]],
) -> bool:
    """Returns True if container polygon geometrically contains the contained polygon."""
    val_a, _, poly_a = validate_geometry(container_input)
    val_b, _, poly_b = validate_geometry(contained_input)
    if not val_a or not val_b or poly_a is None or poly_b is None:
        return False
    return poly_a.contains(poly_b)
