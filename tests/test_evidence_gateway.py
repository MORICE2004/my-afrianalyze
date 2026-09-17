import pytest
from datetime import date
from uuid import uuid4
from pydantic import HttpUrl
from packages.evidence_gateway.manual_ingestion import IngestionProcessor, VerificationState
from packages.evidence_gateway.conflict_engine import ConflictEngine

def test_submit_and_verify_entry():
    processor = IngestionProcessor()
    entry = processor.submit_entry(
        metric_name="GDP",
        value=100.5,
        source_url="https://example.com/gdp",
        publication_date=date(2023, 1, 1),
        document_page=1
    )
    assert entry.state == VerificationState.PENDING_VERIFICATION

    with pytest.raises(PermissionError):
        processor.verify_entry(entry, "RESEARCHER", uuid4())

    verifier_id = uuid4()
    verified_entry = processor.verify_entry(entry, "VERIFIER", verifier_id)
    assert verified_entry.state == VerificationState.VERIFIED
    assert verified_entry.verifier_id == verifier_id

def test_conflict_engine():
    engine = ConflictEngine()
    processor = IngestionProcessor()
    
    entry1 = processor.submit_entry("GDP", 100.5, "https://example.com/gdp1", date(2023, 1, 1), 1)
    entry1 = processor.verify_entry(entry1, "VERIFIER", uuid4())
    
    conflict1 = engine.process_entry(entry1)
    assert conflict1 is None # No conflict initially

    entry2 = processor.submit_entry("GDP", 101.0, "https://example.com/gdp2", date(2023, 1, 1), 2)
    entry2 = processor.verify_entry(entry2, "VERIFIER", uuid4())
    
    conflict2 = engine.process_entry(entry2)
    assert conflict2 is not None
    assert conflict2.metric_name == "GDP"
    assert conflict2.existing_value == 100.5
    assert conflict2.new_value == 101.0
