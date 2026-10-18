"""Enumerations for the NAKSHA canonical land data model."""
from enum import Enum

class AgencyType(str, Enum):
    """Originating government agency or stakeholder body."""
    SUB_REGISTRY = "sub_registry"
    AC_LAND = "ac_land"
    UNION_LAND_OFFICE = "union_land_office"
    DLRS = "dlrs"
    DC_OFFICE = "dc_office"
    BANK = "bank"
    OTHER = "other"


class LandAreaUnit(str, Enum):
    """Standardized land measurement units used in Bangladesh land records."""
    DECIMAL = "decimal"      # শতক / ডেসিমেল (1 dec = 40.4686 m² = 435.6 sq ft)
    SHOTOK = "shotok"        # Bengali synonym for decimal
    ACRE = "acre"            # একর (1 acre = 100 decimals)
    BIGHA = "bigha"          # বিঘা (1 standard bigha = 33 decimals = 20 kathas)
    KATHA = "katha"          # কাঠা (1 katha = 1.65 decimals = 720 sq ft)
    CHHATAK = "chhatak"      # ছটাক (1 chhatak = 1/16 katha = 0.103125 decimals = 45 sq ft)
    SQ_FEET = "sq_feet"      # বর্গফুট
    SQ_METERS = "sq_meters"  # বর্গমিটার


class SurveyEra(str, Enum):
    """The four major historical survey operations across Bangladesh."""
    CS = "CS"        # Cadastral Survey (1888-1940)
    SA = "SA"        # State Acquisition Survey (1956-1963)
    RS = "RS"        # Revisional Survey (1965-present)
    BS = "BS"        # Bangladesh Survey / City Survey (modern ground-truth)
    DIARA = "DIARA"  # Riverine formation survey


class LandClass(str, Enum):
    """Primary land classification categories in Bangladesh revenue administration."""
    NAL = "nal"          # Agricultural / lowland
    VITI = "viti"        # Homestead / raised / commercial
    PUKUR = "pukur"      # Pond / waterbody
    CHALA = "chala"      # High agricultural land
    BAID = "baid"        # Low agricultural valley
    DOBA = "doba"        # Small ditch / water collection
    PATIT = "patit"      # Fallow land
    KHAS = "khas"        # Government public land / water canal
    ROAD = "road"        # Public road / right of way
    OTHER = "other"


class VerificationVerdict(str, Enum):
    """Decision verdict produced by the integrity engine."""
    CLEAR = "CLEAR"    # All records match within statutory tolerances
    REVIEW = "REVIEW"  # Non-blocking anomaly; human review required
    BLOCK = "BLOCK"    # Critical conflict detected (e.g. double sale, encroachment, lien)


class DiscrepancyType(str, Enum):
    """Types of discrepancies between disparate land records."""
    DAG_MISMATCH = "DAG_MISMATCH"
    KHATIAN_MISMATCH = "KHATIAN_MISMATCH"
    AREA_MISMATCH = "AREA_MISMATCH"
    OWNER_MISMATCH = "OWNER_MISMATCH"
    CLASS_CONFLICT = "CLASS_CONFLICT"
    UNMUTATED_DEED = "UNMUTATED_DEED"
    INCOMPLETE_RECORD = "INCOMPLETE_RECORD"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"


class DiscrepancySeverity(str, Enum):
    """Severity classification for audit and decision logic."""
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"
