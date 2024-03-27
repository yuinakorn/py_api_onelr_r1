from typing import List
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from models.database import get_db
from models.pregs.pregs_model import PregBase, PregDisplayBase, LoginBase, CreateBase, PregBaseCid, DeleteBase
from controllers import infants_controller

# from utils.oauth2 import access_user_token

router = APIRouter(prefix="/infants", tags=["infants"])


@router.post("/labours_100/")
def read_labours_100(request: LoginBase,):
    return infants_controller.read_labours_100(request)


@router.post("/")
def read_infants_by_an(request: PregBase):
    return infants_controller.read_infants(request)

