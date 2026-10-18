"""Unit tests for the repository persistence layer."""
from naksha.repository.memory import InMemoryRecordRepository
from naksha.models.canonical import LandRecord, SourceReference, ExtractedField
from naksha.models.enums import AgencyType


def test_in_memory_repository_crud():
    repo = InMemoryRecordRepository()
    assert repo.count() == 0

    src = SourceReference(
        agency=AgencyType.SUB_REGISTRY,
        document_type="Deed",
        source_record_id="DEED-100",
    )
    rec = LandRecord(
        id="REC-TEST-REPO",
        source=src,
        mouza=ExtractedField(raw_value="Kashimpur", normalized_value="Kashimpur"),
        dag_number=ExtractedField(raw_value="500", normalized_value="500"),
    )

    repo.save(rec)
    assert repo.count() == 1

    fetched = repo.get_by_id("REC-TEST-REPO")
    assert fetched is not None
    assert fetched.id == "REC-TEST-REPO"

    # Search with filters
    mouza_match = repo.list_records(mouza="Kashimpur")
    assert len(mouza_match) == 1

    mouza_nomatch = repo.list_records(mouza="Tejgaon")
    assert len(mouza_nomatch) == 0

    dag_match = repo.list_records(dag="500")
    assert len(dag_match) == 1

    agency_match = repo.list_records(agency=AgencyType.SUB_REGISTRY)
    assert len(agency_match) == 1

    agency_nomatch = repo.list_records(agency=AgencyType.BANK)
    assert len(agency_nomatch) == 0
