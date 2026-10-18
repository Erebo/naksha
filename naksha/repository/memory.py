"""In-memory implementation of the Land Record Repository."""
from typing import Optional, List, Dict
from naksha.models.canonical import LandRecord
from naksha.models.enums import AgencyType
from naksha.repository.base import BaseRecordRepository
from naksha.normalization.text import normalize_identifier, normalize_text


class InMemoryRecordRepository(BaseRecordRepository):
    """Stores records in an in-memory dictionary.

    Enables testing and prototype execution without database infrastructure.
    """

    def __init__(self, initial_records: Optional[List[LandRecord]] = None):
        self._records: Dict[str, LandRecord] = {}
        if initial_records:
            for rec in initial_records:
                self.save(rec)

    def get_by_id(self, record_id: str) -> Optional[LandRecord]:
        return self._records.get(record_id)

    def list_records(
        self,
        limit: int = 50,
        offset: int = 0,
        agency: Optional[AgencyType] = None,
        mouza: Optional[str] = None,
        dag: Optional[str] = None,
    ) -> List[LandRecord]:
        results = list(self._records.values())

        if agency:
            results = [r for r in results if r.source.agency == agency]

        if mouza:
            norm_mouza = normalize_text(mouza)
            results = [
                r for r in results
                if r.mouza and r.mouza.normalized_value and
                norm_mouza.lower() in r.mouza.normalized_value.lower()
            ]

        if dag:
            norm_dag = normalize_identifier(dag)
            results = [
                r for r in results
                if r.dag_number and r.dag_number.normalized_value == norm_dag
            ]

        return results[offset : offset + limit]

    def save(self, record: LandRecord) -> LandRecord:
        self._records[record.id] = record
        return record

    def count(self) -> int:
        return len(self._records)
