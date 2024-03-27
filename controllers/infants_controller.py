import jwt
import logging
import requests
from dotenv import dotenv_values
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from models.pregs.pregs_model import DbPreg, DbChospital


config_env = dotenv_values(".env")


def token_decode(token):
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=[config_env["ALGORITHM"]])
        return {"token_data": decoded_token, "is_valid": True}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


def read_labours_100(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        auth = {}
        api_url = f"{config_env['HIS_URL']}/labours_100/{token_decode(token)['token_data']['hosCode']}"
        response = requests.get(api_url, auth=auth)
        result = response.json()

        if response is None or result == []:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูล {request.get('hcode')} ในระบบ"
                }
            )
        else:
            return result

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})



def read_infants(request):
    token = request.get("token")
    cid = request.get("cid")
    an = request.get("an")
    if token_decode(token)['is_valid']:
        auth = {}
        api_url = f"{config_env['HIS_URL']}/infants/{token_decode(token)['token_data']['hosCode']}?cid={cid}&an={an}"
        response = requests.get(api_url, auth=auth)
        result = response.json()

        if response is None or result == []:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูล {request.get('an')} ในระบบ"
                }
            )
        else:
            return result

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})
