from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, join
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Float


class EncryptInput(BaseModel):
    hcode : str
    cid: str
    hn: str
    an: str
    admit_date: str
    title: str
    pname: str
    lname: str
    age_y: str
    gravida: str
    parity: str
    ga: str
    anc_check_up: str
    no_of_anc: str
    weight_before_pregancy: str
    weight_at_delivery: str
    weight_gain: str
    height: str
    fundal_height: str
    hematocrit: str
    ultrasound: str
    cpd_risk_score: str
    status: str
    create_date: str
    modify_date: str
    user_create: str
    user_last_modify: str
    refer_status: str
    refer_out_status: str
    image: str
    
    
    
class DecryptInput(BaseModel):
    cid: str
    pname: str
    lname: str
    salt: str