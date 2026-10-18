"""Abstract repository interface for land record persistence."""
from abc import ABC, abstractmethod
from typing import Optional, List
from naksha.models.canonical import LandRecord
from naksha.models.enums import AgencyType


class BaseRecordRepository(ABC):
    """Abstract interface decoupling business services from data persistence."""

    @abstractmethod
    def get_by_id(self, record_id: str) -> Optional[LandRecord]:
        """Fetch a record by its internal unique identifier."""
        pass

    @abstractmethod
    def list_records(
        self,
        limit: int = 50,
        offset: int = 0,
        agency: Optional[AgencyType] = None,
        mouza: Optional[str] = None,
        dag: Optional[str] = None,
    ) -> List[LandRecord]:
        """Query land records with optional filtering and pagination."""
        pass

    @abstractmethod
    def save(self, record: LandRecord) -> LandRecord:
        """Persist or update a land record."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored records."""
        pass
