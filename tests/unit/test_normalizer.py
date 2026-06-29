import pytest
from services.landbank.normalizer import normalize_record

def test_normalize_record():
    raw = {"source_id":"s1","address":"1 Main St","raw":"<div/>"}
    out = normalize_record(raw)
    assert out["listing_id"] == "s1"
