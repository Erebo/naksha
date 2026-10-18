"""Text, Numeral, and Identifier Normalization Utilities for NAKSHA."""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional, Union

# Mapping between Bengali digits (০-৯) and ASCII digits (0-9)
BANGLA_TO_ENGLISH_DIGITS = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
}
ENGLISH_TO_BANGLA_DIGITS = {v: k for k, v in BANGLA_TO_ENGLISH_DIGITS.items()}

# Common Bangla and English name honorifics/prefixes found in legacy land records
NAME_HONORIFICS = [
    r"^\s*মোঃ\s*",
    r"^\s*মোছাঃ\s*",
    r"^\s*মোসাম্মৎ\s*",
    r"^\s*মোসাম্মদ\s*",
    r"^\s*মুহাম্মদ\s*",
    r"^\s*মোহাম্মদ\s*",
    r"^\s*মো[:\.\-]\s*",
    r"^\s*শ্রীমতি\s*",
    r"^\s*শ্রী\s*",
    r"^\s*মৃত\s*",
    r"^\s*md[\.\s]+",
    r"^\s*mohammad[\.\s]+",
    r"^\s*mohammed[\.\s]+",
    r"^\s*mst[\.\s]+",
    r"^\s*most[\.\s]+",
    r"^\s*late[\.\s]+",
]
HONORIFIC_REGEX = re.compile("|".join(NAME_HONORIFICS), re.IGNORECASE)

# Common identifier labels (dag/khatian/holding prefixes)
IDENTIFIER_PREFIXES = [
    r"^\s*দাগ\s*(নং|নম্বর)?[:\.\-\s#]*",
    r"^\s*খতিয়ান\s*(নং|নম্বর)?[:\.\-\s#]*",
    r"^\s*খতিয়ান\s*(নং|নম্বর)?[:\.\-\s#]*",
    r"^\s*হোল্ডিং\s*(নং|নম্বর)?[:\.\-\s#]*",
    r"^\s*dag\s*(no|num|number)?[:\.\-\s#]*",
    r"^\s*khatian\s*(no|num|number)?[:\.\-\s#]*",
    r"^\s*holding\s*(no|num|number)?[:\.\-\s#]*",
    r"^\s*plot\s*(no|num|number)?[:\.\-\s#]*",
]
ID_PREFIX_REGEX = re.compile("|".join(IDENTIFIER_PREFIXES), re.IGNORECASE)

# Consonants and Vowels in Bengali Script
BANGLA_CONSONANTS = set("কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ")
BANGLA_CHAR_MAP = {
    "অ": "a", "আ": "a", "ই": "i", "ঈ": "i", "উ": "u", "ঊ": "u", "ঋ": "ri",
    "এ": "e", "ঐ": "oi", "ও": "o", "ঔ": "ou",
    "ক": "k", "খ": "kh", "গ": "g", "ঘ": "gh", "ঙ": "ng",
    "চ": "ch", "ছ": "chh", "জ": "j", "ঝ": "jh", "ঞ": "n",
    "ট": "t", "ঠ": "th", "ড": "d", "ঢ": "dh", "ণ": "n",
    "ত": "t", "থ": "th", "দ": "d", "ধ": "dh", "ন": "n",
    "প": "p", "ফ": "f", "ব": "b", "ভ": "bh", "ম": "m",
    "য": "j", "র": "r", "ল": "l", "শ": "sh", "ষ": "sh", "স": "s", "হ": "h",
    "ড়": "r", "ঢ়": "rh", "য়": "y", "ৎ": "t",
    "ং": "ng", "ঃ": "", "ঁ": "",
    "া": "a", "ি": "i", "ী": "i", "ু": "u", "ূ": "u", "ৃ": "ri",
    "ে": "e", "ৈ": "oi", "ো": "o", "ৌ": "ou", "্": "",
}


def normalize_text(text: Optional[str]) -> Optional[str]:
    """Cleans and standardizes raw text:

    - Applies Unicode NFC normalization.
    - Strips zero-width characters (ZWNJ, ZWJ, BOM, ZWSP).
    - Collapses multiple whitespace characters to a single space.
    - Trims leading/trailing whitespace.
    """
    if text is None:
        return None

    # Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", str(text))

    # Remove zero-width characters
    for ch in ("\u200B", "\u200C", "\u200D", "\uFEFF", "\u00A0"):
        normalized = normalized.replace(ch, " ")

    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized if normalized else None


def bangla_to_english_digits(text: Optional[str]) -> Optional[str]:
    """Converts all Bengali numeral characters (০-৯) to standard ASCII digits (0-9)."""
    if text is None:
        return None
    res = "".join(BANGLA_TO_ENGLISH_DIGITS.get(ch, ch) for ch in str(text))
    return res


def english_to_bangla_digits(text: Optional[str]) -> Optional[str]:
    """Converts all ASCII numeral characters (0-9) to Bengali digits (০-৯)."""
    if text is None:
        return None
    res = "".join(ENGLISH_TO_BANGLA_DIGITS.get(ch, ch) for ch in str(text))
    return res


def parse_numeric(value: Union[str, int, float, None]) -> Optional[float]:
    """Extracts and parses a float value from a numeric or text input,

    handling both Bengali and English digits, commas, and whitespace.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = normalize_text(str(value))
    if not cleaned:
        return None

    # Convert Bangla digits to English
    eng_digits = bangla_to_english_digits(cleaned)
    # Remove thousand separators
    sanitized = eng_digits.replace(",", "").strip()

    # Match numeric portion
    match = re.search(r"[-+]?\d*\.?\d+", sanitized)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def normalize_identifier(raw_id: Optional[str]) -> Optional[str]:
    """Standardizes plot/dag, khatian, and holding identifiers:

    - Strips prefixes (e.g. 'দাগ নং', 'Dag No.', 'khatian #').
    - Converts Bengali numerals to English.
    - Cleans up spacing around slashes and dashes (e.g. '402 / 1' -> '402/1').
    - Preserves meaningful sub-plot suffixes (e.g. '402/ka', '88-B').
    """
    cleaned = normalize_text(raw_id)
    if not cleaned:
        return None

    # Remove common prefix labels
    without_prefix = ID_PREFIX_REGEX.sub("", cleaned).strip()
    without_prefix = without_prefix.lstrip("#:.- ").strip()
    if not without_prefix:
        return None

    # Convert digits to standard ASCII
    standard_digits = bangla_to_english_digits(without_prefix)
    if not standard_digits:
        return None

    # Standardize separator spacing: e.g. "402 / 1" -> "402/1", "402 - 1" -> "402-1"
    normalized = re.sub(r"\s*([/\-\_])\s*", r"\1", standard_digits).strip()

    # If it ends with trailing punctuation like '.', clean it
    normalized = normalized.rstrip(".:,;")
    return normalized if normalized else None


def strip_bangla_honorifics(name: Optional[str]) -> Optional[str]:
    """Removes common Bengali and English honorifics/prefixes (e.g., 'Md.', 'মোঃ')

    to facilitate fair phonetic and orthographic matching.
    """
    cleaned = normalize_text(name)
    if not cleaned:
        return None

    stripped = HONORIFIC_REGEX.sub("", cleaned).strip()
    # Second pass for compound honorifics like "Md. Abdul" vs "মোঃ আব্দুল"
    stripped = HONORIFIC_REGEX.sub("", stripped).strip()
    return stripped if stripped else cleaned


def transliterate_bangla_to_latin(text: Optional[str]) -> str:
    """Performs phonetic romanization of Bengali script strings into Latin characters."""
    if not text:
        return ""
    norm = normalize_text(text)
    if not norm:
        return ""

    res = []
    n = len(norm)
    for i, ch in enumerate(norm):
        lat = BANGLA_CHAR_MAP.get(ch, ch)
        res.append(lat)
        if ch in BANGLA_CONSONANTS:
            # Check next character for inherent vowel
            next_ch = norm[i + 1] if i + 1 < n else None
            if next_ch and (next_ch in BANGLA_CONSONANTS or next_ch == " "):
                res.append("a")
    return "".join(res).lower()


def _consonant_skeleton(s: str) -> str:
    """Extracts non-vowel alphanumeric characters for consonant-based phonetic comparison."""
    vowels = set("aeiouy")
    return "".join(c for c in s.lower() if c.isalnum() and c not in vowels)


def phonetic_name_similarity(name_a: Optional[str], name_b: Optional[str]) -> float:
    """Computes phonetic similarity between two person names (0.0 to 1.0).

    Handles mixed Bengali/English scripts, honorific stripping, and minor spelling variations.
    """
    if not name_a or not name_b:
        return 0.0

    clean_a = strip_bangla_honorifics(name_a) or name_a
    clean_b = strip_bangla_honorifics(name_b) or name_b

    # Romanize if any characters are in Bengali script block (\u0980-\u09FF)
    has_bangla_a = bool(re.search(r"[\u0980-\u09FF]", clean_a))
    has_bangla_b = bool(re.search(r"[\u0980-\u09FF]", clean_b))

    rom_a = transliterate_bangla_to_latin(clean_a) if has_bangla_a else clean_a.lower()
    rom_b = transliterate_bangla_to_latin(clean_b) if has_bangla_b else clean_b.lower()

    # Exact romanized match
    if rom_a == rom_b:
        return 1.0

    # Consonantal skeleton matching
    skel_a = _consonant_skeleton(rom_a)
    skel_b = _consonant_skeleton(rom_b)
    if skel_a and skel_b and skel_a == skel_b:
        return 0.95

    # Sequence matchers
    seq_ratio = SequenceMatcher(None, rom_a, rom_b).ratio()
    skel_ratio = SequenceMatcher(None, skel_a, skel_b).ratio() if (skel_a and skel_b) else 0.0

    return max(seq_ratio, skel_ratio)
