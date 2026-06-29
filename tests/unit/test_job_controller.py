import pytest
from services.contractor.job_controller import register_contractor

def test_register_missing_fields():
    try:
        register_contractor({})
    except Exception as e:
        assert "name and email required" in str(e)
