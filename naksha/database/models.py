"""SQLAlchemy ORM Models for NAKSHA Persistent Spatial & Land Record Engine."""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from naksha.database.connection import Base


class CanonicalParcelModel(Base):
    """Stores authoritative canonical parcel geometries and identifiers."""
    __tablename__ = "canonical_parcels"

    id = Column(String(64), primary_key=True, index=True)
    dag_number = Column(String(32), index=True, nullable=False)
    khatian_number = Column(String(32), index=True, nullable=False)
    mouza = Column(String(128), index=True, nullable=False)
    jl_number = Column(String(32), default="28")
    upazila = Column(String(128), default="Gazipur Sadar")
    district = Column(String(128), default="Gazipur")
    area_decimals = Column(Float, nullable=False)
    geometry_geojson = Column(Text, nullable=False)
    geometry_wkt = Column(Text, nullable=True)
    survey_era = Column(String(32), default="BS")
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to multi-era survey snapshots
    survey_layers = relationship(
        "SurveyHistoryModel",
        back_populates="parcel",
        cascade="all, delete-orphan",
    )


class SurveyHistoryModel(Base):
    """Stores multi-era cadastral survey layers linked to a canonical parcel."""
    __tablename__ = "survey_history_layers"

    id = Column(String(64), primary_key=True, index=True)
    parcel_id = Column(String(64), ForeignKey("canonical_parcels.id"), index=True, nullable=False)
    survey_era = Column(String(32), nullable=False)  # CS, SA, RS, BS, DLRS
    layer_type = Column(String(64), nullable=False)  # ancestral_footprint, deed_claim, ground_truth, conflict_zone, restricted_khas
    layer_name = Column(String(256), nullable=False)
    geometry_geojson = Column(Text, nullable=False)
    geometry_wkt = Column(Text, nullable=True)
    area_decimals = Column(Float, nullable=True)
    properties_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parcel = relationship("CanonicalParcelModel", back_populates="survey_layers")


class AgencyRecordModel(Base):
    """Stores disparate land records originating from external government agencies."""
    __tablename__ = "agency_records"

    id = Column(String(64), primary_key=True, index=True)
    agency = Column(String(64), index=True, nullable=False)  # sub_registry, ac_land, union_land_office, dlrs, dc_office, bank
    document_type = Column(String(128), nullable=False)
    source_record_id = Column(String(64), index=True, nullable=False)
    canonical_parcel_id = Column(String(64), index=True, nullable=True)
    dag_number = Column(String(32), index=True, nullable=True)
    khatian_number = Column(String(32), index=True, nullable=True)
    mouza = Column(String(128), index=True, nullable=True)
    owner_name = Column(String(256), nullable=True)
    area_decimals = Column(Float, nullable=True)
    land_class = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLedgerModel(Base):
    """Stores immutable, SHA-256 hash-chained and Ed25519-signed verification events."""
    __tablename__ = "audit_ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_index = Column(Integer, unique=True, index=True, nullable=False)
    timestamp = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    canonical_parcel_id = Column(String(64), index=True, nullable=True)
    dag_number = Column(String(32), index=True, nullable=True)
    mouza = Column(String(128), nullable=True)
    officer_id = Column(String(64), default="UL-2024-KSH")
    verdict = Column(String(32), nullable=True)
    cited_records_json = Column(Text, default="[]")
    payload_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), unique=True, nullable=False)
    signature_ed25519 = Column(String(128), nullable=False)
    public_key_ed25519 = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Spatial indexes and compound index definitions
Index("idx_parcel_dag_khatian", CanonicalParcelModel.dag_number, CanonicalParcelModel.khatian_number)
Index("idx_record_dag_agency", AgencyRecordModel.dag_number, AgencyRecordModel.agency)
Index("idx_survey_parcel_layer", SurveyHistoryModel.parcel_id, SurveyHistoryModel.layer_type)
