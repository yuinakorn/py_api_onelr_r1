from datetime import datetime

from sqlalchemy import Column, ForeignKey, join
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Float

from models.database import Base
from pydantic import BaseModel
from typing import Optional


class DbInfant(Base):
    __tablename__ = "t_infant"
    hcode = Column(String, primary_key=True, index=True)
    cid = Column(String, primary_key=True, index=True)
    an = Column(String, primary_key=True, index=True)
    infant_no = Column(Integer, primary_key=True, index=True)
    bw = Column(Integer, nullable=True)

    # Relationship with Chospital
    # hcode = Column(String, ForeignKey('chospital.id'))

    # hcode = relationship("Chospital", back_populates="hoscode")


class PregBase(BaseModel):
    token: str
    cid: str
    an: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class PregBaseCid(BaseModel):
    token: str
    cid: str
    hcode: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class PregDisplayBase(BaseModel):
    hcode: str
    cid: str
    hn: str
    an: str
    admit_date: Optional[datetime] = None
    title: Optional[str] = None
    pname: str
    lname: str
    age_y: str
    gravida: str
    parity: str
    ga: str
    anc_check_up: str
    no_of_anc: str
    weight_before_pregancy: float
    weight_at_delivery: float
    weight_gain: float
    height: str
    fundal_height: str
    hematocrit: str
    ultrasound: str
    cpd_risk_score: Optional[str] = None
    status: int
    create_date: datetime
    modify_date: Optional[datetime] = None
    user_create: Optional[str] = None
    user_last_modify: Optional[str] = None
    refer_status: Optional[int] = None
    image: Optional[str] = None

    class Config:
        orm_mode = True


class LoginBase(BaseModel):
    token: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class CreateBase(BaseModel):
    token: str
    cid: str
    hn: str
    an: str
    admit_date: datetime
    title: Optional[str] = None
    pname: str
    lname: str
    age_y: str
    gravida: str
    parity: str
    ga: str
    anc_check_up: str
    no_of_anc: str
    weight_before_pregancy: float
    weight_at_delivery: float
    weight_gain: float
    height: str
    fundal_height: str
    hematocrit: str
    ultrasound: str
    cpd_risk_score: Optional[str] = None
    status: int
    create_date: datetime
    modify_date: datetime
    user_create: Optional[str] = None
    user_last_modify: Optional[str] = None
    refer_status: Optional[int] = None
    image: Optional[str] = None

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


class DeleteBase(BaseModel):
    token: str
    cid: str
    an: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


# Define your Chospital model
class Chospital(Base):
    """This class represents a hospital."""
    __tablename__ = 'chospital'
    hoscode = Column(String, primary_key=True, index=True)
    hosname = Column(String, nullable=True)
    # hoscode = Column(Integer, ForeignKey("t_pregancy.hcode"))

    # owner = relationship("DbPreg", back_populates="hcode")

