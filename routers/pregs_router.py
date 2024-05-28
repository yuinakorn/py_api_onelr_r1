from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Header, HTTPException, Request

from sqlalchemy.orm import Session
from models.database import get_db
from models.preg_crypto.pregs_crypto_model import DecryptInput
from models.pregs.pregs_model import CreateMessage, PregBase, PregDisplayBase, LoginBase, CreateBase, PregBaseCid, DeleteBase, \
    MakeConsult, CryptoBase, DecryptBase, ReadMessage
from controllers import pregs_controller
from controllers.crypto_controller import encrypt_data, decrypt_data


# from utils.oauth2 import access_user_token

router = APIRouter(prefix="/pregs", tags=["pregs"])


@router.post("/", response_model=List[PregDisplayBase])
async def read_preg_all_by_hcode(request: LoginBase, db: Session = Depends(get_db)):
    return await pregs_controller.read_preg(request, db)


# @router.post("/")
# async def read_preg_all_by_hcode(data: DecryptInput):
#     decrypted_data = await decrypt_data(data)
#     return decrypted_data


@router.post("/search/")
async def read_preg_by_an(request: PregBase, db: Session = Depends(get_db)):
    return await pregs_controller.search(db, request)


@router.post("/his/search/")
async def read_his_preg_by_hn(request: PregBaseCid):
    return await pregs_controller.his_search(request)


@router.post("/his/search_img/")
async def read_his_preg_by_hn(request: PregBaseCid):
    return await pregs_controller.his_search_img(request)


# @router.post("/check/token/")
# def check_token(request: LoginBase):
#     return pregs_controller.token_check(request)


@router.post("/create/")
async def create_new_preg(request: CreateBase, db: Session = Depends(get_db)):
    return await pregs_controller.create(db, request)


@router.put("/update/")
def update_preg(request: CreateBase, db: Session = Depends(get_db)):
    return pregs_controller.update(db, request)


# encrypt all data in new case
@router.post("/force-encrypt/")
async def force_encrypt(request: LoginBase, db: Session = Depends(get_db)):
    return await pregs_controller.force_encrypt(db, request)


@router.delete("/delete/")
def delete_preg(request: DeleteBase, db: Session = Depends(get_db)):
    return pregs_controller.delete(db, request)


@router.post("/consult/")
async def make_consult_preg(request: MakeConsult, db: Session = Depends(get_db)):
    return await pregs_controller.consult(db, request)


@router.post("/create-message/")
async def create_message(request: CreateMessage):
    return await pregs_controller.create_message(request)


@router.post("/read-message/")
async def read_message(request: ReadMessage):
    return await pregs_controller.read_message(request)


def extract_token(Authorization: str):
    if Authorization and Authorization.startswith("Bearer "):
        try:
            # Split the header on the space, and return the second part (the token).
            return Authorization.split(" ")[1]
        except IndexError:
            # In case the header is malformed and doesn't have a space
            raise HTTPException(status_code=400, detail="Invalid Authorization header format.")
    else:
        # If the header is missing or does not start with "Bearer "
        raise HTTPException(status_code=401, detail="Authorization token is missing or improperly formatted.")


@router.post("/upload/")
async def upload_image(Authorization: str = Header(None), file: UploadFile = File(...), hoscode: str = None, an: str = None):
    token = extract_token(Authorization)
    return await pregs_controller.upload_image(token, file, hoscode, an)


# @router.post("/encrypt/")
# async def encrypt_data_with(request: CryptoBase):
#     return await encrypt_data(request)


# @router.post("/decrypt/")
# async def decrypt_data_with(request: DecryptBase):
#     return await decrypt_data(request)


# @router.post("/plain_to_cipher/")
# async def plain_to_cipher(request: CreateBase):
#     return await pregs_controller.plain_to_cipher(request)

