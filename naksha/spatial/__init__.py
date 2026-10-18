"""Expose spatial engine methods."""
from naksha.spatial.engine import (
    validate_geometry,
    calculate_polygon_area,
    calculate_overlap,
    check_containment,
    to_shapely_polygon,
    to_geojson_geometry,
)

__all__ = [
    "validate_geometry",
    "calculate_polygon_area",
    "calculate_overlap",
    "check_containment",
    "to_shapely_polygon",
    "to_geojson_geometry",
]
