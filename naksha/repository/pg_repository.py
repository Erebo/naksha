"""PostgreSQL + PostGIS implementation of Land Record and Spatial Repositories."""
import json
import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Union
from sqlalchemy import func, or_, and_, cast, text
from sqlalchemy.orm import Session, aliased
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement

from naksha.models.canonical import LandRecord
from naksha.models.enums import AgencyType
from naksha.repository.base import BaseRecordRepository
from naksha.database.connection import SessionLocal
from naksha.database.pg_models import (
    CanonicalParcelPG,
    AgencyRecordPG,
    SurveyLayerPG,
    RestrictedZonePG,
    OfficerPG,
    TaxPaymentPG,
    LienPG,
)
from naksha.normalization.area import DECIMAL_TO_SQ_METERS
from naksha.normalization.text import bangla_to_english_digits, normalize_text, normalize_identifier


def normalize_dag_key(raw_dag: Optional[str]) -> Optional[str]:
    """Normalizes a dag/plot number: strips whitespace and converts Bengali digits to English.

    Performs exact whole-string normalization with NO regex digit extraction.
    """
    if raw_dag is None:
        return None
    trimmed = str(raw_dag).strip()
    if not trimmed:
        return None
    return bangla_to_english_digits(trimmed).strip()


def normalize_mouza_key(raw_mouza: Optional[str]) -> Optional[str]:
    """Normalizes a mouza name: trims whitespace, lowercases, and handles bilingual labels."""
    if raw_mouza is None:
        return None
    trimmed = str(raw_mouza).strip()
    if not trimmed:
        return None
    lower = trimmed.lower()
    # Handle bilingual label e.g. 'কাশিমপুর (Kashimpur)' -> match on 'kashimpur'
    if "kashimpur" in lower or "কাশিমপুর" in lower:
        return "kashimpur"
    return lower


class SpatialRepository(ABC):
    """Abstract interface for PostGIS spatial queries, cadastral overlays, and parcel resolution."""

    @abstractmethod
    def get_parcel_by_key(self, mouza: str, dag: str) -> Optional[CanonicalParcelPG]:
        """Fetch canonical parcel by exact mouza and dag number."""
        pass

    @abstractmethod
    def resolve_parcel(self, mouza: str, dag: str, khatian: Optional[str] = None) -> Optional[CanonicalParcelPG]:
        """Resolve parcel with Bengali/English digit normalization. Returns None for unknown parcels."""
        pass

    @abstractmethod
    def get_survey_layers(self, parcel_id: Union[uuid.UUID, str]) -> List[SurveyLayerPG]:
        """Fetch multi-era survey history overlays associated with a parcel."""
        pass

    @abstractmethod
    def get_restricted_zones_intersecting(
        self, parcel_id: Union[uuid.UUID, str]
    ) -> List[Tuple[RestrictedZonePG, float]]:
        """Return restricted zones intersecting parcel geometry with area computed in UTM 46N (EPSG:32646) in decimals."""
        pass

    @abstractmethod
    def get_neighbors(self, parcel_id: Union[uuid.UUID, str], radius_m: float) -> List[CanonicalParcelPG]:
        """Fetch neighboring parcels within a metric radius."""
        pass

    @abstractmethod
    def get_tax_payments(self, parcel_id: Union[uuid.UUID, str]) -> List[TaxPaymentPG]:
        """Fetch LD tax payment history for a parcel."""
        pass

    @abstractmethod
    def get_liens(self, parcel_id: Union[uuid.UUID, str]) -> List[LienPG]:
        """Fetch registered mortgages and liens for a parcel."""
        pass

    @abstractmethod
    def get_officer(self, officer_id: str) -> Optional[OfficerPG]:
        """Fetch officer profile by officer_id."""
        pass


class PostgresRecordRepository(BaseRecordRepository, SpatialRepository):
    """PostgreSQL + PostGIS implementation of Land Record and Spatial Repositories."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        if self._session is not None:
            return self._session
        return SessionLocal()

    def _model_to_entity(self, model: AgencyRecordPG) -> LandRecord:
        """Hydrates a Pydantic LandRecord from JSONB payload."""
        payload = model.raw_payload
        if isinstance(payload, str):
            payload = json.loads(payload)
        return LandRecord.model_validate(payload)

    # -------------------------------------------------------------------------
    # BaseRecordRepository Implementation
    # -------------------------------------------------------------------------

    def get_by_id(self, record_id: str) -> Optional[LandRecord]:
        session = self._get_session()
        try:
            # Match either primary key UUID or source_record_id
            query = session.query(AgencyRecordPG)
            try:
                rec_uuid = uuid.UUID(record_id)
                model = query.filter(or_(AgencyRecordPG.id == rec_uuid, AgencyRecordPG.source_record_id == record_id)).first()
            except ValueError:
                model = query.filter(AgencyRecordPG.source_record_id == record_id).first()

            if not model:
                return None
            return self._model_to_entity(model)
        finally:
            if self._session is None:
                session.close()

    def list_records(
        self,
        limit: int = 50,
        offset: int = 0,
        agency: Optional[AgencyType] = None,
        mouza: Optional[str] = None,
        dag: Optional[str] = None,
    ) -> List[LandRecord]:
        session = self._get_session()
        try:
            query = session.query(AgencyRecordPG)

            if agency:
                query = query.filter(AgencyRecordPG.agency == agency.value)

            if mouza:
                norm_mouza = normalize_text(mouza)
                query = query.filter(
                    func.lower(AgencyRecordPG.normalized_fields["mouza"].astext).contains(norm_mouza.lower())
                )

            if dag:
                norm_dag = normalize_identifier(dag)
                query = query.filter(
                    AgencyRecordPG.normalized_fields["dag_number"].astext == norm_dag
                )

            models = query.order_by(AgencyRecordPG.recorded_at.desc()).offset(offset).limit(limit).all()
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._session is None:
                session.close()

    def save(self, record: LandRecord) -> LandRecord:
        session = self._get_session()
        try:
            # Deterministic UUID from agency and source_record_id
            rec_agency = record.source.agency.value if record.source.agency else "unknown"
            rec_source_id = record.source.source_record_id or record.id

            existing = (
                session.query(AgencyRecordPG)
                .filter(AgencyRecordPG.agency == rec_agency, AgencyRecordPG.source_record_id == rec_source_id)
                .first()
            )

            raw_payload = record.model_dump(mode="json")
            normalized_fields = {
                "dag_number": record.dag_number.normalized_value if record.dag_number else None,
                "khatian_number": record.khatian_number.normalized_value if record.khatian_number else None,
                "mouza": record.mouza.normalized_value if record.mouza else None,
                "owner_name": record.owner_name.normalized_value if record.owner_name else None,
                "area_decimals": record.area_in_decimals,
            }

            if existing:
                existing.raw_payload = raw_payload
                existing.normalized_fields = normalized_fields
                existing.document_type = record.source.document_type or existing.document_type
            else:
                new_model = AgencyRecordPG(
                    agency=rec_agency,
                    source_record_id=rec_source_id,
                    document_type=record.source.document_type or "Unknown",
                    raw_payload=raw_payload,
                    normalized_fields=normalized_fields,
                    extraction_confidence=record.dag_number.confidence if record.dag_number else 1.0,
                )
                session.add(new_model)

            session.commit()
            return record
        except Exception:
            session.rollback()
            raise
        finally:
            if self._session is None:
                session.close()

    def count(self) -> int:
        session = self._get_session()
        try:
            return session.query(AgencyRecordPG).count()
        finally:
            if self._session is None:
                session.close()

    # -------------------------------------------------------------------------
    # SpatialRepository Implementation
    # -------------------------------------------------------------------------

    def get_parcel_by_key(self, mouza: str, dag: str) -> Optional[CanonicalParcelPG]:
        return self.resolve_parcel(mouza=mouza, dag=dag)

    def resolve_parcel(self, mouza: str, dag: str, khatian: Optional[str] = None) -> Optional[CanonicalParcelPG]:
        norm_dag = normalize_dag_key(dag)
        norm_mouza = normalize_mouza_key(mouza)
        if not norm_dag or not norm_mouza:
            return None

        session = self._get_session()
        try:
            query = session.query(CanonicalParcelPG).filter(CanonicalParcelPG.dag_number == norm_dag)
            query = query.filter(func.lower(CanonicalParcelPG.mouza).contains(norm_mouza))

            if khatian:
                norm_khatian = normalize_dag_key(khatian)
                if norm_khatian:
                    query = query.filter(CanonicalParcelPG.khatian_number == norm_khatian)

            return query.first()
        finally:
            if self._session is None:
                session.close()

    def get_survey_layers(self, parcel_id: Union[uuid.UUID, str]) -> List[SurveyLayerPG]:
        session = self._get_session()
        try:
            pid = uuid.UUID(str(parcel_id)) if not isinstance(parcel_id, uuid.UUID) else parcel_id
            return session.query(SurveyLayerPG).filter(SurveyLayerPG.parcel_id == pid).all()
        finally:
            if self._session is None:
                session.close()

    def get_restricted_zones_intersecting(
        self, parcel_id: Union[uuid.UUID, str]
    ) -> List[Tuple[RestrictedZonePG, float]]:
        session = self._get_session()
        try:
            pid = uuid.UUID(str(parcel_id)) if not isinstance(parcel_id, uuid.UUID) else parcel_id

            # Compute intersection area in UTM Zone 46N (EPSG:32646) divided by DECIMAL_TO_SQ_METERS
            stmt = (
                session.query(
                    RestrictedZonePG,
                    func.ST_Area(
                        func.ST_Transform(
                            func.ST_Intersection(CanonicalParcelPG.geometry, RestrictedZonePG.geometry),
                            32646,
                        )
                    ) / DECIMAL_TO_SQ_METERS,
                )
                .join(
                    CanonicalParcelPG,
                    and_(
                        CanonicalParcelPG.id == pid,
                        func.ST_Intersects(CanonicalParcelPG.geometry, RestrictedZonePG.geometry),
                    ),
                )
            )

            results: List[Tuple[RestrictedZonePG, float]] = []
            for zone, area_dec in stmt.all():
                if area_dec is not None and float(area_dec) > 0.01:
                    results.append((zone, round(float(area_dec), 4)))
            return results
        finally:
            if self._session is None:
                session.close()

    def get_neighbors(self, parcel_id: Union[uuid.UUID, str], radius_m: float) -> List[CanonicalParcelPG]:
        session = self._get_session()
        try:
            pid = uuid.UUID(str(parcel_id)) if not isinstance(parcel_id, uuid.UUID) else parcel_id
            target_alias = aliased(CanonicalParcelPG)

            return (
                session.query(CanonicalParcelPG)
                .join(
                    target_alias,
                    and_(
                        target_alias.id == pid,
                        CanonicalParcelPG.id != pid,
                        func.ST_DWithin(
                            cast(CanonicalParcelPG.geometry, Geography),
                            cast(target_alias.geometry, Geography),
                            radius_m,
                        ),
                    ),
                )
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def get_tax_payments(self, parcel_id: Union[uuid.UUID, str]) -> List[TaxPaymentPG]:
        session = self._get_session()
        try:
            pid = uuid.UUID(str(parcel_id)) if not isinstance(parcel_id, uuid.UUID) else parcel_id
            return (
                session.query(TaxPaymentPG)
                .filter(TaxPaymentPG.parcel_id == pid)
                .order_by(TaxPaymentPG.fiscal_year.desc())
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def get_liens(self, parcel_id: Union[uuid.UUID, str]) -> List[LienPG]:
        session = self._get_session()
        try:
            pid = uuid.UUID(str(parcel_id)) if not isinstance(parcel_id, uuid.UUID) else parcel_id
            return (
                session.query(LienPG)
                .filter(LienPG.parcel_id == pid)
                .order_by(LienPG.recorded_at.desc())
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def get_officer(self, officer_id: str) -> Optional[OfficerPG]:
        session = self._get_session()
        try:
            return session.query(OfficerPG).filter(OfficerPG.officer_id == officer_id).first()
        finally:
            if self._session is None:
                session.close()
