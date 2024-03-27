from typing import List
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from models.database import get_db
from models.pregs.pregs_model import PregBase, PregDisplayBase, LoginBase, CreateBase, PregBaseCid, DeleteBase, ProgressBase
from controllers import pregs_controller


# from utils.oauth2 import access_user_token

router = APIRouter(prefix="/pregs", tags=["pregs"])


@router.post("/", response_model=List[PregDisplayBase])
def read_preg_all_by_hcode(request: LoginBase, db: Session = Depends(get_db)):
    return pregs_controller.read_preg(request, db)


@router.post("/search/")
def read_preg_by_an(request: PregBase, db: Session = Depends(get_db)):
    return pregs_controller.search(db, request)


@router.post("/his/search/")
def read_his_preg_by_cid(request: PregBaseCid):
    return pregs_controller.his_search(request)


# @router.post("/check/token/")
# def check_token(request: LoginBase):
#     return pregs_controller.token_check(request)


@router.post("/create/")
def create_new_preg(request: CreateBase, db: Session = Depends(get_db)):
    return pregs_controller.create(db, request)


@router.put("/update/")
def update_preg(request: CreateBase, db: Session = Depends(get_db)):
    return pregs_controller.update(db, request)


@router.delete("/delete/")
def delete_preg(request: DeleteBase, db: Session = Depends(get_db)):
    return pregs_controller.delete(db, request)


