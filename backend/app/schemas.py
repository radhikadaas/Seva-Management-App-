# app/schemas.py

from pydantic import BaseModel
from datetime import date

class SevaEntryBase(BaseModel):
    paath_name: str
    person_name: str
    gotra_name: str
    start_date: date
    end_date: date

class SevaEntryCreate(SevaEntryBase):
    pass

class SevaEntryOut(SevaEntryBase):
    id: int

    class Config:
        orm_mode = True
