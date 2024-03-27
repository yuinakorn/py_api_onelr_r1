# oauth2 mean "Open Authorization 2.0" is a protocol that allows a user to grant a limited access
# to their resources on one site, to another site, without having to expose their credentials.
import os
from datetime import timedelta, datetime
from typing import Optional

from dotenv import dotenv_values
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt


config_env = dotenv_values(".env")

SECRET_KEY = config_env["SECRET_KEY"]
ALGORITHM = config_env["ALGORITHM"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expire_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = generate_expire_date(expire_delta)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encode_jwt


def generate_expire_date(expire_delta: Optional[timedelta] = None):
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        # expire in 1 day
        expire = datetime.utcnow() + timedelta(days=1)
    return expire


# def access_user_token(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception()
#     except JWTError:
#         raise credentials_exception()
#
#
# def credentials_exception():
#     return HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials"
#     )
