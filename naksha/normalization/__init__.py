"""Expose normalization utilities."""
from naksha.normalization.text import (
    normalize_text,
    bangla_to_english_digits,
    english_to_bangla_digits,
    parse_numeric,
    normalize_identifier,
    strip_bangla_honorifics,
    transliterate_bangla_to_latin,
    phonetic_name_similarity,
)
from naksha.normalization.area import (
    TO_DECIMALS,
    DECIMAL_TO_SQ_METERS,
    parse_unit,
    convert_land_area,
    standardize_area,
)

__all__ = [
    "normalize_text",
    "bangla_to_english_digits",
    "english_to_bangla_digits",
    "parse_numeric",
    "normalize_identifier",
    "strip_bangla_honorifics",
    "transliterate_bangla_to_latin",
    "phonetic_name_similarity",
    "TO_DECIMALS",
    "DECIMAL_TO_SQ_METERS",
    "parse_unit",
    "convert_land_area",
    "standardize_area",
]
