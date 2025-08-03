# app/models.py

from sqlalchemy import Column, Integer, String, Date
from .database import Base

class SevaEntry(Base):
    __tablename__ = "seva_entries"

    id = Column(Integer, primary_key=True, index=True)
    paath_name = Column(String)
    person_name = Column(String)
    gotra_name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
