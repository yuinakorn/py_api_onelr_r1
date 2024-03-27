from datetime import datetime

from sqlalchemy import Column, ForeignKey, join
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Float

from models.database import Base
from pydantic import BaseModel
from typing import Optional


class DbPreg(Base):
    __tablename__ = "t_pregancy"
    hcode = Column(String, primary_key=True, index=True)
    cid = Column(String, ForeignKey('chospital.hoscode'), primary_key=True, index=True)
    hn = Column(String)
    an = Column(String, primary_key=True, index=True)
    admit_date = Column(DateTime, nullable=True)
    title = Column(String, nullable=True)
    pname = Column(String)
    lname = Column(String)
    age_y = Column(String)
    gravida = Column(String)
    parity = Column(String)
    ga = Column(String)
    anc_check_up = Column(String)
    no_of_anc = Column(String)
    weight_before_pregancy = Column(Float, nullable=True)
    weight_at_delivery = Column(Float, nullable=True)
    weight_gain = Column(Float, nullable=True)
    height = Column(String)
    fundal_height = Column(String)
    hematocrit = Column(String)
    ultrasound = Column(String)
    cpd_risk_score = Column(String, nullable=True)
    status = Column(Integer)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    user_create = Column(String, nullable=True)
    user_last_modify = Column(String, nullable=True)
    refer_status = Column(String, nullable=True)
    refer_out_status = Column(String, nullable=True)
    image = Column(String, nullable=True)

    chospital = relationship("DbChospital", back_populates="t_pregancy")


class ProgressBase(BaseModel):
    token: str
    cid: str
    an: str
    hcode: str


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
    refer_out_status: Optional[int] = None
    image: Optional[str] = None

    class Config:
        orm_mode = True


class PregsAllBase(BaseModel):
    hcode: Optional[str] = None
    cid: Optional[str] = None
    hn: Optional[str] = None
    an: Optional[str] = None
    admit_date: Optional[datetime] = None
    title: Optional[str] = None
    pname: Optional[str] = None
    lname: Optional[str] = None
    age_y: Optional[str] = None
    gravida: Optional[str] = None
    parity: Optional[str] = None
    ga: Optional[str] = None
    anc_check_up: Optional[str] = None
    no_of_anc: Optional[str] = None
    weight_before_pregancy: Optional[float] = None
    weight_at_delivery: Optional[float] = None
    weight_gain: Optional[float] = None
    height: Optional[str] = None
    fundal_height: Optional[str] = None
    hematocrit: Optional[str] = None
    ultrasound: Optional[str] = None
    cpd_risk_score: Optional[str] = None
    status: Optional[int] = None
    create_date: Optional[datetime] = None
    modify_date: Optional[datetime] = None
    user_create: Optional[str] = None
    user_last_modify: Optional[str] = None
    refer_status: Optional[int] = None
    refer_out_status: Optional[int] = None
    image: Optional[str] = None
    hosname: Optional[str] = None

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
    refer_out_status: Optional[int] = None
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
class DbChospital(Base):
    """This class represents a hospital."""
    __tablename__ = 'chospital'
    hoscode = Column(String, primary_key=True, index=True)
    hosname = Column(String, nullable=True)

    t_pregancy = relationship("DbPreg", back_populates="chospital")


