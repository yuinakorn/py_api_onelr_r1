import jwt
import logging
import pymysql
from dotenv import dotenv_values
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from models.progress.progress_model import DbProgress

config_env = dotenv_values(".env")


def get_connection():
    connection = pymysql.connect(host=config_env["DB_HOST"],
                                 user=config_env["DB_USER"],
                                 password=config_env["DB_PASSWORD"],
                                 db=config_env["DB_NAME"],
                                 charset=config_env["CHARSET"],
                                 port=int(config_env["DB_PORT"]),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    return connection


def token_decode(token):
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=[config_env["ALGORITHM"]])
        return {"token_data": decoded_token, "is_valid": True}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


def read_progress(request, db: Session):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        return db.query(DbProgress).filter(DbProgress.hcode == token_decode(token)['token_data']['hosCode']).all()

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def search(db: Session, request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        # shorted code
        hcode = request.get("hcode") if token_decode(token)['token_data']['hosCode'] == '10714' else \
        token_decode(token)['token_data']['hosCode']

        result = db.query(DbProgress).filter(DbProgress.hcode == hcode,
                                             DbProgress.cid == request.get("cid"),
                                             DbProgress.an == request.get("an")).all()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูลของ an {request.get('an')} ในระบบ"
                }
            )
        else:
            return result

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def token_check(request):
    token = request.get("token")
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_data = {
            "hoscode": decoded_token["hosCode"],
            "username": decoded_token["username"],
            "user_cid": decoded_token["cid"]
        }
        # print(user_data)
        message = "Token is valid"
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"status": "ok", "message": message, "data": user_data})

    except jwt.InvalidTokenError:
        message = "Token is invalid!!"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": message})


def create(db: Session, request):
    token = request.token
    if token_decode(token)['is_valid']:
        new_progress = DbProgress(
            hcode=token_decode(token)['token_data']['hosCode'],
            cid=request.cid,
            hn=request.hn,
            an=request.an,
            progress_date_time=request.progress_date_time,
            code=request.code,
            value=request.value,
            value2=request.value2,
            value3=request.value3,
            comment=request.comment
        )
        try:
            db.add(new_progress)
            db.commit()
            db.refresh(new_progress)
            return {"message": "ok", "detail": new_progress}
        except SQLAlchemyError as e:
            db.rollback()
            error_message = f"Error creating Progress: {str(e)}"
            logging.error(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def update(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        result = db.query(DbProgress).filter(DbProgress.hcode == token_decode(token)['token_data']['hosCode'],
                                             DbProgress.cid == request.cid,
                                             DbProgress.an == request.an).first()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูลของ an {request.an}"
                }
            )
        else:
            # now = datetime.now()
            # modify_date = now.strftime("%Y-%m-%d %H:%M:%S")
            result.hcode = token_decode(token)['token_data']['hosCode']
            result.cid = request.cid
            result.hn = request.hn
            result.an = request.an
            result.progress_date_time = request.progress_date_time
            result.code = request.code
            result.value = request.value
            result.value2 = request.value2
            result.value3 = request.value3
            result.comment = request.comment

            try:
                db.commit()
                db.refresh(result)
                return {"message": "ok", "detail": result}
            except SQLAlchemyError as e:
                db.rollback()
                error_message = f"Error updating Progress: {str(e)}"
                logging.error(error_message)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def delete(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        result = db.query(DbProgress).filter(DbProgress.hcode == token_decode(token)['token_data']['hosCode'],
                                             DbProgress.cid == request.cid,
                                             DbProgress.an == request.an,
                                             DbProgress.progress_date_time == request.progress_date_time,
                                             DbProgress.code == request.code).first()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูลของ an {request.an}"
                }
            )
        else:
            try:
                db.delete(result)
                db.commit()
                return {"message": "ok", "detail": result}
            except SQLAlchemyError as e:
                db.rollback()
                error_message = f"Error deleting Progress: {str(e)}"
                logging.error(error_message)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def show_progress(request):
    token = request.get("token")
    hcode = request.get("hcode")
    an = request.get("an")
    cid = request.get("cid")
    if token_decode(token)['is_valid']:
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = f"SELECT p.progress_date_time,max(p.C06_v1) as vs,max(p.C02_v1) as uc_i,max(p.C02_v2) as uc_d, " \
                      "max(p.C02_v3) as uc_stage,max(p.C03_v1) as fhs ,max(p.C01_v1) as cervix_open,max(p.C01_com) as cervix_open_com " \
                      "FROM (" \
                      " SELECT progress_date_time FROM progress" \
                      " WHERE hcode = %s" \
                      " AND an = %s" \
                      " AND cid = %s" \
                      " GROUP BY progress_date_time" \
                      " ORDER BY progress_date_time,`code`) t" \
                      " LEFT JOIN (" \
                      " SELECT progress.progress_date_time," \
                      " if(progress.`code` = 'C06' AND progress.`value` is not NULL,progress.`value`,null) as 'C06_v1'," \
                      " if(progress.`code` = 'C02' AND progress.`value` is not NULL,progress.`value`,null) as 'C02_v1'," \
                      " if(progress.`code` = 'C02' and progress.value2 is NOT NULL,progress.value2,null) as 'C02_v2'," \
                      " if(progress.`code` = 'C02' and progress.value3 is NOT NULL,progress.value3,null) as 'C02_v3'," \
                      " if(progress.`code` = 'C03' and progress.`value3` is NOT NULL,progress.`value3`,null) as 'C03_v1'," \
                      " if(progress.`code` = 'C01' and progress.value is NOT NULL,progress.value,null) as 'C01_v1'," \
                      " if(progress.`code` = 'C01' and progress.`comment` is NOT NULL,progress.`comment`,null) as 'C01_com'" \
                      " FROM progress" \
                      " INNER JOIN ccode ON ccode.`code` = progress.`code`" \
                      " WHERE hcode = %s" \
                      " AND an = %s" \
                      " AND cid = %s" \
                      " ORDER BY progress.progress_date_time,ccode.`code`" \
                      " ) p ON t.progress_date_time = p.progress_date_time" \
                      " GROUP BY p.progress_date_time"

                cursor.execute(sql, (hcode, an, cid, hcode, an, cid))
                result = cursor.fetchall()
            return result
        except SQLAlchemyError as e:
            error_message = f"Error reading progress: {str(e)}"
            logging.error(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"status": "error", "message": error_message})
