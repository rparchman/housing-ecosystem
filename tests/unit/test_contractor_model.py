import pytest
from services.contractor.contractor_model import Contractor

def test_contractor_fields():
    c = Contractor()
    assert hasattr(c, "__tablename__")
