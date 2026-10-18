"""Expose repository interfaces and implementations."""
from naksha.repository.base import BaseRecordRepository
from naksha.repository.memory import InMemoryRecordRepository

__all__ = ["BaseRecordRepository", "InMemoryRecordRepository"]
