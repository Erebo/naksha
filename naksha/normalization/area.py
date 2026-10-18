"""Standardized Land Area Conversion and Normalization Utilities.

Implements explicit, mathematically verified conversion factors used in
Bangladesh land administration:
- 1 Decimal (শতক/ডেসিমেল) = 435.60 sq ft = 40.4685642 m²
- 1 Acre (একর) = 100 Decimals
- 1 Standard Bigha (বিঘা) = 33 Decimals = 20 Kathas = 14,374.80 sq ft
- 1 Katha (কাঠা) = 1.65 Decimals = 720.00 sq ft
- 1 Chhatak (ছটাক) = 0.103125 Decimals = 45.00 sq ft
- 1 Sq Meter (বর্গমিটার) = ~0.0247105 Decimals
- 1 Sq Foot (বর্গফুট) = 1 / 435.6 Decimals
"""
import re
from typing import Optional, Union, Tuple
from naksha.models.enums import LandAreaUnit
from naksha.normalization.text import parse_numeric, normalize_text

# Exact conversion factors: Multiplier to convert 1 unit of X into standard Bangladesh revenue DECIMALS
TO_DECIMALS: dict[LandAreaUnit, float] = {
    LandAreaUnit.DECIMAL: 1.0,
    LandAreaUnit.SHOTOK: 1.0,
    LandAreaUnit.ACRE: 100.0,
    LandAreaUnit.BIGHA: 33.0,
    LandAreaUnit.KATHA: 1.65,
    LandAreaUnit.CHHATAK: 0.103125,
    LandAreaUnit.SQ_FEET: 1.0 / 435.6,
    LandAreaUnit.SQ_METERS: 1.0 / 40.4685642,
}

# 1 Decimal in metric square meters
DECIMAL_TO_SQ_METERS = 40.4685642

# Unit string aliases in Bengali and English
UNIT_ALIASES: dict[str, LandAreaUnit] = {
    "decimal": LandAreaUnit.DECIMAL,
    "decimals": LandAreaUnit.DECIMAL,
    "dec": LandAreaUnit.DECIMAL,
    "শতক": LandAreaUnit.DECIMAL,
    "শতাংশ": LandAreaUnit.DECIMAL,
    "ডেসিমেল": LandAreaUnit.DECIMAL,
    "shotok": LandAreaUnit.SHOTOK,
    "acre": LandAreaUnit.ACRE,
    "acres": LandAreaUnit.ACRE,
    "একর": LandAreaUnit.ACRE,
    "bigha": LandAreaUnit.BIGHA,
    "বিঘা": LandAreaUnit.BIGHA,
    "katha": LandAreaUnit.KATHA,
    "কাঠা": LandAreaUnit.KATHA,
    "katta": LandAreaUnit.KATHA,
    "chhatak": LandAreaUnit.CHHATAK,
    "ছটাক": LandAreaUnit.CHHATAK,
    "sq_feet": LandAreaUnit.SQ_FEET,
    "sqft": LandAreaUnit.SQ_FEET,
    "sq ft": LandAreaUnit.SQ_FEET,
    "square feet": LandAreaUnit.SQ_FEET,
    "বর্গফুট": LandAreaUnit.SQ_FEET,
    "sq_meters": LandAreaUnit.SQ_METERS,
    "sqm": LandAreaUnit.SQ_METERS,
    "sq m": LandAreaUnit.SQ_METERS,
    "square meters": LandAreaUnit.SQ_METERS,
    "বর্গমিটার": LandAreaUnit.SQ_METERS,
}


def parse_unit(unit_str: Union[str, LandAreaUnit, None]) -> Optional[LandAreaUnit]:
    """Resolves arbitrary unit strings (Bangla or English) to a canonical LandAreaUnit enum."""
    if unit_str is None:
        return None
    if isinstance(unit_str, LandAreaUnit):
        return unit_str

    cleaned = normalize_text(str(unit_str))
    if not cleaned:
        return None
    lowered = cleaned.lower()
    return UNIT_ALIASES.get(lowered, None)


def convert_land_area(
    value: float,
    from_unit: Union[LandAreaUnit, str],
    to_unit: Union[LandAreaUnit, str],
) -> float:
    """Converts a land area from any supported unit to another using explicit conversion factors.

    Raises:
        ValueError: If either unit is unrecognized or value is negative.
    """
    if value < 0:
        raise ValueError(f"Land area cannot be negative: {value}")

    parsed_from = parse_unit(from_unit)
    if not parsed_from:
        raise ValueError(f"Unrecognized source land area unit: '{from_unit}'")

    parsed_to = parse_unit(to_unit)
    if not parsed_to:
        raise ValueError(f"Unrecognized target land area unit: '{to_unit}'")

    if parsed_from == parsed_to:
        return float(value)

    # Convert to base Decimals first
    decimals = value * TO_DECIMALS[parsed_from]
    # Convert from Decimals to target unit
    result = decimals / TO_DECIMALS[parsed_to]
    return result


def standardize_area(
    value: Union[float, str, None],
    unit: Union[LandAreaUnit, str, None],
    precision_decimals: int = 4,
    precision_sqm: int = 2,
) -> Tuple[Optional[float], Optional[float]]:
    """Takes a raw or parsed value and unit, and returns a tuple of:

    (standardized_decimals, standardized_sq_meters).
    Returns (None, None) if value or unit is missing or unparseable.
    """
    numeric_val = parse_numeric(value)
    if numeric_val is None or numeric_val < 0:
        return None, None

    parsed_unit = parse_unit(unit)
    if parsed_unit is None:
        return None, None

    decimals = numeric_val * TO_DECIMALS[parsed_unit]
    sq_meters = decimals * DECIMAL_TO_SQ_METERS

    return (
        round(decimals, precision_decimals),
        round(sq_meters, precision_sqm),
    )
