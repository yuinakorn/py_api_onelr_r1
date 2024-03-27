from typing import List
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from models.database import get_db
from models.progress.progress_model import ProgressBase, CreateBase, DisplayBase, DeleteBase
from controllers import progress_controller

router = APIRouter(prefix="/progress", tags=["progress"])


# @router.post("/", response_model=List[DisplayBase])
# async def read_progress(request: LoginBase, db: Session = Depends(get_db)):
#     return progress_controller.read_progress(request, db)
#

@router.post("/search/", response_model=List[DisplayBase])
async def read_progress_by_an(request: ProgressBase, db: Session = Depends(get_db)):
    return progress_controller.search(db, request)


@router.post("/create/")
async def create_new_progress(request: CreateBase, db: Session = Depends(get_db)):
    return progress_controller.create(db, request)


@router.put("/update/")
def update_progress(request: CreateBase, db: Session = Depends(get_db)):
    return progress_controller.update(db, request)


@router.delete("/delete/")
def delete_progress(request: DeleteBase, db: Session = Depends(get_db)):
    return progress_controller.delete(db, request)


@router.post("/table/")
def show_progress(request: ProgressBase):
    return progress_controller.show_progress(request)
