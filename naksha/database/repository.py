"""Persistent SQLAlchemy implementation of the Land Record Repository."""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from naksha.models.canonical import (
    LandRecord,
    SourceReference,
    ExtractedField,
    GeoJSONGeometry,
)
from naksha.models.enums import AgencyType, LandAreaUnit, LandClass, SurveyEra
from naksha.repository.base import BaseRecordRepository
from naksha.database.connection import SessionLocal
from naksha.database.models import AgencyRecordModel
from naksha.normalization.text import normalize_identifier, normalize_text


class SQLAlchemyRecordRepository(BaseRecordRepository):
    """Persists LandRecord objects in the relational database (PostgreSQL/SQLite)."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        if self._session is not None:
            return self._session
        return SessionLocal()

    def _model_to_entity(self, model: AgencyRecordModel) -> LandRecord:
        """Hydrates a Pydantic LandRecord from the database model."""
        data = json.loads(model.payload_json)
        return LandRecord.model_validate(data)

    def _entity_to_model(self, record: LandRecord) -> AgencyRecordModel:
        """Serializes a Pydantic LandRecord into an ORM model."""
        return AgencyRecordModel(
            id=record.id,
            agency=record.source.agency.value if record.source.agency else "unknown",
            document_type=record.source.document_type or "Unknown",
            source_record_id=record.source.source_record_id or record.id,
            canonical_parcel_id=record.canonical_parcel_id,
            dag_number=record.dag_number.normalized_value if record.dag_number else None,
            khatian_number=record.khatian_number.normalized_value if record.khatian_number else None,
            mouza=record.mouza.normalized_value if record.mouza else None,
            owner_name=record.owner_name.normalized_value if record.owner_name else None,
            area_decimals=record.area_in_decimals,
            land_class=record.land_class.value if record.land_class else None,
            notes=record.source.notes,
            payload_json=record.model_dump_json(),
        )

    def get_by_id(self, record_id: str) -> Optional[LandRecord]:
        session = self._get_session()
        try:
            model = session.query(AgencyRecordModel).filter(AgencyRecordModel.id == record_id).first()
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
            query = session.query(AgencyRecordModel)

            if agency:
                query = query.filter(AgencyRecordModel.agency == agency.value)

            if mouza:
                norm_mouza = normalize_text(mouza)
                query = query.filter(AgencyRecordModel.mouza.ilike(f"%{norm_mouza}%"))

            if dag:
                norm_dag = normalize_identifier(dag)
                query = query.filter(AgencyRecordModel.dag_number == norm_dag)

            models = query.offset(offset).limit(limit).all()
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._session is None:
                session.close()

    def save(self, record: LandRecord) -> LandRecord:
        session = self._get_session()
        try:
            existing = session.query(AgencyRecordModel).filter(AgencyRecordModel.id == record.id).first()
            if existing:
                existing.payload_json = record.model_dump_json()
                existing.dag_number = record.dag_number.normalized_value if record.dag_number else None
                existing.khatian_number = record.khatian_number.normalized_value if record.khatian_number else None
                existing.area_decimals = record.area_in_decimals
                existing.notes = record.source.notes
            else:
                new_model = self._entity_to_model(record)
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
            return session.query(AgencyRecordModel).count()
        finally:
            if self._session is None:
                session.close()
