from datetime import datetime
from pydantic import validator

from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Float

from models.database import Base
from pydantic import BaseModel
from typing import Optional


class DbProgress(Base):
    __tablename__ = "progress"
    hcode = Column(String, primary_key=True, index=True)
    cid = Column(String, primary_key=True, index=True)
    hn = Column(String)
    an = Column(String, primary_key=True, index=True)
    progress_date_time = Column(DateTime, primary_key=True)
    code = Column(String, primary_key=True)
    value = Column(String)
    value2 = Column(String, nullable=True)
    value3 = Column(String, nullable=True)
    comment = Column(String, nullable=True)


class ProgressBase(BaseModel):
    token: str
    hcode: str
    cid: str
    an: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class LoginBase(BaseModel):
    token: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class DisplayBase(BaseModel):
    hcode: str
    cid: str
    hn: str
    an: str
    progress_date_time: Optional[datetime] = None
    code: str
    value: Optional[str] = None
    value2: Optional[str] = None
    value3: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        orm_mode = True


class CreateBase(BaseModel):
    token: str
    cid: str
    hn: str
    an: str
    progress_date_time: Optional[datetime] = None
    code: str
    value: str
    value2: str
    value3: str
    comment: Optional[str] = None

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class DeleteBase(BaseModel):
    token: str
    cid: str
    an: str
    progress_date_time: Optional[datetime] = None
    code: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)
