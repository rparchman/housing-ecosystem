from sqlalchemy import Column, Integer, String, JSON, DateTime
from services.shared.db import Base
import datetime

class Contractor(Base):
    __tablename__ = "contractors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    profile = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
