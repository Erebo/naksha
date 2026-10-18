"""Unit tests for text, numeral, identifier, and area normalization utilities."""
import pytest
from naksha.models.enums import LandAreaUnit
from naksha.normalization.text import (
    normalize_text,
    bangla_to_english_digits,
    english_to_bangla_digits,
    parse_numeric,
    normalize_identifier,
    strip_bangla_honorifics,
    phonetic_name_similarity,
)
from naksha.normalization.area import (
    convert_land_area,
    standardize_area,
    parse_unit,
    DECIMAL_TO_SQ_METERS,
)


# ==========================================
# 1. Text & Numeral Tests
# ==========================================

def test_normalize_text_whitespace_and_unicode():
    """Verify whitespace collapsing and zero-width character removal."""
    assert normalize_text(None) is None
    assert normalize_text("   ") is None
    assert normalize_text("  ঢাকা   জেলা  ") == "ঢাকা জেলা"
    # Zero-width non-joiner (\u200C) and zero-width space (\u200B)
    assert normalize_text("গা\u200Cজী\u200Bপুর") == "গা জী পুর"
    # Tab and newline
    assert normalize_text("মৌজা\tকাশিমপুর\n") == "মৌজা কাশিমপুর"


def test_bangla_and_english_digits_bidirectional():
    """Verify bidirectional conversion of Bengali and English digits."""
    assert bangla_to_english_digits("০১২৩৪৫৬৭৮৯") == "0123456789"
    assert english_to_bangla_digits("0123456789") == "০১২৩৪৫৬৭৮৯"
    assert bangla_to_english_digits("দাগ-৪০২") == "দাগ-402"
    assert bangla_to_english_digits(None) is None
    assert english_to_bangla_digits(None) is None


def test_parse_numeric():
    """Verify numeric parsing from ints, floats, and strings with English or Bangla digits."""
    assert parse_numeric(10) == 10.0
    assert parse_numeric(12.75) == 12.75
    assert parse_numeric("10.5") == 10.5
    assert parse_numeric("৬.০০") == 6.0
    assert parse_numeric("১,২৫০.৭৫") == 1250.75
    assert parse_numeric(" 402 ") == 402.0
    assert parse_numeric("Total 5.1 decimals") == 5.1
    assert parse_numeric("invalid_text") is None
    assert parse_numeric(None) is None


def test_normalize_identifier():
    """Verify dag, khatian, and holding identifier normalization."""
    assert normalize_identifier("দাগ নং ৪০২") == "402"
    assert normalize_identifier("দাগ নম্বর-৪০২") == "402"
    assert normalize_identifier("Dag No. 402") == "402"
    assert normalize_identifier("খতিয়ান নং ১২০") == "120"
    assert normalize_identifier("khatian # 120") == "120"
    assert normalize_identifier("402 / 1") == "402/1"
    assert normalize_identifier("৪০২ / ১") == "402/1"
    assert normalize_identifier("দাগ ৪০২/ক") == "402/ক"
    assert normalize_identifier("  88-B. ") == "88-B"
    assert normalize_identifier(None) is None
    assert normalize_identifier("") is None


def test_strip_bangla_honorifics():
    """Verify stripping of common name honorifics for phonetic matching."""
    assert strip_bangla_honorifics("মোঃ আব্দুল করিম") == "আব্দুল করিম"
    assert strip_bangla_honorifics("মোছাঃ ফাতেমা খাতুন") == "ফাতেমা খাতুন"
    assert strip_bangla_honorifics("মোহাম্মদ রফিক") == "রফিক"
    assert strip_bangla_honorifics("Md. Abdul Karim") == "Abdul Karim"
    assert strip_bangla_honorifics("Mohammad A. Karim") == "A. Karim"
    assert strip_bangla_honorifics("Late Rahim Uddin") == "Rahim Uddin"
    assert strip_bangla_honorifics("Karim") == "Karim"
    assert strip_bangla_honorifics(None) is None


def test_phonetic_name_similarity():
    """Verify cross-lingual Bengali-Latin phonetic name matching."""
    # Exact match across scripts with honorifics
    sim = phonetic_name_similarity("মোঃ আব্দুল করিম", "Md. Abdul Karim")
    assert sim >= 0.85

    # Slight vowel variation in English transliteration
    assert phonetic_name_similarity("Abdul Karim", "Abdool Kareem") >= 0.80

    # Completely different names should have low similarity (below 0.60, well below 0.80 match threshold)
    assert phonetic_name_similarity("Md. Abdul Karim", "Tariqul Islam") < 0.60

    # None or empty handling
    assert phonetic_name_similarity(None, "Karim") == 0.0
    assert phonetic_name_similarity("", "") == 0.0


# ==========================================
# 2. Land Area Unit & Conversion Tests
# ==========================================

def test_parse_unit():
    """Verify unit parsing from various Bangla and English string aliases."""
    assert parse_unit("decimal") == LandAreaUnit.DECIMAL
    assert parse_unit("শতক") == LandAreaUnit.DECIMAL
    assert parse_unit("ডেসিমেল") == LandAreaUnit.DECIMAL
    assert parse_unit("একর") == LandAreaUnit.ACRE
    assert parse_unit("bigha") == LandAreaUnit.BIGHA
    assert parse_unit("বিঘা") == LandAreaUnit.BIGHA
    assert parse_unit("কাঠা") == LandAreaUnit.KATHA
    assert parse_unit("katha") == LandAreaUnit.KATHA
    assert parse_unit("ছটাক") == LandAreaUnit.CHHATAK
    assert parse_unit("sqft") == LandAreaUnit.SQ_FEET
    assert parse_unit("বর্গমিটার") == LandAreaUnit.SQ_METERS
    assert parse_unit("unknown_unit") is None
    assert parse_unit(None) is None


def test_convert_land_area_standards():
    """Verify statutory mathematical conversion rules between Bangladesh land units."""
    # 1 Acre = 100 Decimals
    assert convert_land_area(1.0, LandAreaUnit.ACRE, LandAreaUnit.DECIMAL) == 100.0
    assert convert_land_area(100.0, LandAreaUnit.DECIMAL, LandAreaUnit.ACRE) == 1.0

    # 1 Standard Bigha = 33 Decimals = 20 Kathas
    assert convert_land_area(1.0, LandAreaUnit.BIGHA, LandAreaUnit.DECIMAL) == 33.0
    assert convert_land_area(1.0, LandAreaUnit.BIGHA, LandAreaUnit.KATHA) == 20.0

    # 1 Katha = 1.65 Decimals
    assert convert_land_area(1.0, LandAreaUnit.KATHA, LandAreaUnit.DECIMAL) == 1.65
    assert convert_land_area(20.0, LandAreaUnit.KATHA, LandAreaUnit.BIGHA) == 1.0

    # 1 Katha = 16 Chhataks
    assert round(convert_land_area(1.0, LandAreaUnit.KATHA, LandAreaUnit.CHHATAK), 2) == 16.0
    assert convert_land_area(1.0, LandAreaUnit.CHHATAK, LandAreaUnit.DECIMAL) == 0.103125

    # Identity conversion
    assert convert_land_area(6.0, LandAreaUnit.DECIMAL, LandAreaUnit.DECIMAL) == 6.0


def test_convert_land_area_errors():
    """Verify conversion errors on negative values or invalid units."""
    with pytest.raises(ValueError, match="negative"):
        convert_land_area(-5.0, LandAreaUnit.DECIMAL, LandAreaUnit.ACRE)

    with pytest.raises(ValueError, match="Unrecognized source"):
        convert_land_area(10.0, "invalid_unit", LandAreaUnit.DECIMAL)

    with pytest.raises(ValueError, match="Unrecognized target"):
        convert_land_area(10.0, LandAreaUnit.DECIMAL, "invalid_unit")


def test_standardize_area():
    """Verify standardization to base Decimals and Square Meters."""
    # 6 decimals
    dec, sqm = standardize_area(6.0, LandAreaUnit.DECIMAL)
    assert dec == 6.0
    assert sqm == round(6.0 * DECIMAL_TO_SQ_METERS, 2)

    # 1 acre -> 100 decimals
    dec, sqm = standardize_area("১.০০", "একর")
    assert dec == 100.0
    assert sqm == round(100.0 * DECIMAL_TO_SQ_METERS, 2)

    # Incomplete or invalid input returns (None, None)
    assert standardize_area(None, LandAreaUnit.DECIMAL) == (None, None)
    assert standardize_area(5.0, None) == (None, None)
    assert standardize_area(-1.0, LandAreaUnit.DECIMAL) == (None, None)
