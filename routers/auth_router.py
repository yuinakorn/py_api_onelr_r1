import datetime
from typing import List

from dotenv import dotenv_values
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from controllers import pregs_controller
from routers.utils.oauth2 import create_access_token

config_env = dotenv_values(".env")

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBase(BaseModel):
    username: str
    password: str
    hosCode: str
    cid: str
    patientCid: str
    patientHosCode: str


class AuthDisplayBase(BaseModel):
    tokenViewer: str


class CheckTokenBase(BaseModel):
    token: str

    class Config:
        orm_mode = True

    def get(self, key):
        return getattr(self, key, None)


@router.post("/login")
def read_lp_user(request: LoginBase):
    try:
        if request.username == config_env['LP_USER'] and request.password == config_env['LP_PASS']:
            iat = datetime.datetime.utcnow()
            access_token = create_access_token(data={
                "iat": iat,
                "sub": request.username,
                "username": request.username,
                "hosCode": request.hosCode,
            })
            return {"status": "success", "tokenViewer": access_token}
        else:
            return HTTPException(status_code=401, detail={"status": "error", "message": "You are not allowed!!"})
    except Exception as e:
        raise HTTPException(status_code=401, detail={"status": "error", "message": str(e)})


@router.post("/check/token/")
def check_token(request: CheckTokenBase):
    return pregs_controller.token_check(request)

