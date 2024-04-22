from typing import List
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from models.database import get_db
from models.pregs.pregs_model import PregBase, PregDisplayBase, LoginBase, CreateBase, PregsAllBase, CheckPreg
from controllers import dashboard_controller, pregs_controller
from routers.auth_router import CheckTokenBase

# from utils.oauth2 import access_user_token

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/provinces/")
def read_province():
    return dashboard_controller.read_province()


@router.post("/province/{hcode}")
def read_province_by_hcode(hcode: str):
    return dashboard_controller.read_province_by_hcode(hcode)


@router.get("/hospitals/")
def read_hostpitals():
    return dashboard_controller.read_hostpitals()


# เฉพาะแม่ข่าย
@router.post("/patients/")
def read_preg_all(request: LoginBase):
    return pregs_controller.read_preg_all(request)


@router.post("/hospitals/")
def read_dashboard_all():
    return dashboard_controller.read_dashboard_all()


def validate_hcode(hcode: str):
    if hcode is None or hcode.strip() == "":
        raise HTTPException(400, "Invalid hcode")
    return hcode


@router.post("/hospital/{hcode}")
def read_hospital_by_hcode(hcode: str = Depends(validate_hcode)):
    return dashboard_controller.read_hospital_by_hcode(hcode)


@router.post("/patient/")
def read_patient_by_an(request: CheckPreg):
    return dashboard_controller.read_patient_by_an(request)


# @router.post("/patient/{hcode}/{an}")
# def read_patient_by_an(hcode: str, an: str):
#     return dashboard_controller.read_patient_by_an(hcode, an)


@router.post("/chart/{hcode}/{an}")
def read_chart_by_an(hcode: str, an: str):
    return dashboard_controller.read_hospital_by_an(hcode, an)


@router.post("/hos_node/")
def read_hos_node(request: CheckTokenBase):
    return dashboard_controller.read_hos_node(request)


@router.get("/hospital_name/{hcode}")
def read_hospital_name(hcode: str = Depends(validate_hcode)):
    return dashboard_controller.read_hospital_name(hcode)


@router.post("/pregs_consult/")
def read_pregs_consult(request: CheckTokenBase):
    return dashboard_controller.read_pregs_consult(request)


@router.get("/notify_count/{hcode}")
def read_notify_count(hcode: str, db: Session = Depends(get_db)):
    return dashboard_controller.read_notify_count(hcode, db)


@router.post("/consulted/")
def update_consulted(request: LoginBase, db: Session = Depends(get_db)):
    return dashboard_controller.update_consulted(request, db)
