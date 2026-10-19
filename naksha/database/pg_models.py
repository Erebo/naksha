"""PostgreSQL + PostGIS SQLAlchemy ORM Models for NAKSHA Spatial Intelligence Engine."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry

PGBase = declarative_base()


class CanonicalParcelPG(PGBase):
    """Canonical Cadastral Parcels with PostGIS Geometries."""
    __tablename__ = "canonical_parcels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mouza = Column(String(128), nullable=False, index=True)
    dag_number = Column(String(32), nullable=False, index=True)
    khatian_number = Column(String(32), nullable=False, index=True)
    jl_number = Column(String(32), nullable=True)
    upazila = Column(String(128), nullable=True)
    district = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="active")
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_canonical_parcels_mouza_dag", "mouza", "dag_number"),
        CheckConstraint("status IN ('active', 'archived', 'disputed', 'merged', 'subdivided')", name="chk_parcels_status"),
        CheckConstraint("ST_IsValid(geometry)", name="chk_parcels_geometry_valid"),
    )

    # Relationships
    agency_records = relationship("AgencyRecordPG", back_populates="parcel", cascade="all, delete-orphan")
    survey_layers = relationship("SurveyLayerPG", back_populates="parcel", cascade="all, delete-orphan")
    tax_payments = relationship("TaxPaymentPG", back_populates="parcel", cascade="all, delete-orphan")
    liens = relationship("LienPG", back_populates="parcel", cascade="all, delete-orphan")


class AgencyRecordPG(PGBase):
    """Raw and Normalized Agency Records mapped to Canonical Parcels."""
    __tablename__ = "agency_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="SET NULL"), nullable=True, index=True)
    agency = Column(String(64), nullable=False, index=True)
    source_record_id = Column(String(128), nullable=False)
    document_type = Column(String(64), nullable=False)
    raw_payload = Column(JSONB, nullable=False)
    normalized_fields = Column(JSONB, nullable=False, server_default="{}")
    extraction_confidence = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("agency", "source_record_id", name="uq_agency_records_agency_source_record_id"),
        CheckConstraint("extraction_confidence IS NULL OR (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0)", name="chk_agency_records_confidence"),
    )

    parcel = relationship("CanonicalParcelPG", back_populates="agency_records")


class ParcelLineagePG(PGBase):
    """Lineage Tracking across Historical Land Surveys (CS, SA, RS, BS, DLRS)."""
    __tablename__ = "parcel_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    child_parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    survey_era = Column(String(16), nullable=False)
    relation = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("parent_parcel_id != child_parcel_id", name="chk_parcel_lineage_no_self_link"),
        CheckConstraint("survey_era IN ('CS', 'SA', 'RS', 'BS', 'DLRS')", name="chk_parcel_lineage_survey_era"),
        CheckConstraint("relation IN ('subdivision', 'amalgamation', 'succession', 're-survey')", name="chk_parcel_lineage_relation"),
    )

    parent_parcel = relationship("CanonicalParcelPG", foreign_keys=[parent_parcel_id])
    child_parcel = relationship("CanonicalParcelPG", foreign_keys=[child_parcel_id])


class SurveyLayerPG(PGBase):
    """Historical and Cadastral Survey Overlays with Spatial Boundaries."""
    __tablename__ = "survey_layers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    survey_era = Column(String(16), nullable=False)
    layer_type = Column(String(64), nullable=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False)
    area_decimals = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("survey_era IN ('CS', 'SA', 'RS', 'BS', 'DLRS')", name="chk_survey_layers_survey_era"),
        CheckConstraint("ST_IsValid(geometry)", name="chk_survey_layers_geometry_valid"),
    )

    parcel = relationship("CanonicalParcelPG", back_populates="survey_layers")


class RestrictedZonePG(PGBase):
    """Restricted and Statutory Zones (Khas, Canals, Rivers, Embankments)."""
    __tablename__ = "restricted_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    zone_type = Column(String(64), nullable=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False)
    source = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("zone_type IN ('khas', 'canal', 'river', 'forest', 'wetland', 'railway', 'embankment', 'vested_property')", name="chk_restricted_zones_zone_type"),
        CheckConstraint("ST_IsValid(geometry)", name="chk_restricted_zones_geometry_valid"),
    )


class OfficerPG(PGBase):
    """Verified Government Land Officers and Cadastral Personnel."""
    __tablename__ = "officers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    officer_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    designation = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False)
    jurisdiction = Column(String(128), nullable=False)
    office = Column(String(256), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('ac_land', 'kanungo', 'surveyor', 'sub_registrar', 'dc', 'admin', 'auditor')", name="chk_officers_role"),
    )


class TaxPaymentPG(PGBase):
    """Land Development Tax (LD Tax) Payment Ledger."""
    __tablename__ = "tax_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    fiscal_year = Column(String(16), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(32), nullable=False)
    payer_name = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('paid', 'unpaid', 'overdue', 'exempt', 'partial')", name="chk_tax_payments_status"),
    )

    parcel = relationship("CanonicalParcelPG", back_populates="tax_payments")


class LienPG(PGBase):
    """Registered Mortgages, Liens, Court Attachments, and Caveats."""
    __tablename__ = "liens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("canonical_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    lien_type = Column(String(64), nullable=False)
    holder = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("lien_type IN ('mortgage', 'court_attachment', 'government_charge', 'freeze', 'dispute')", name="chk_liens_lien_type"),
        CheckConstraint("status IN ('active', 'discharged', 'pending', 'cancelled')", name="chk_liens_status"),
    )

    parcel = relationship("CanonicalParcelPG", back_populates="liens")
