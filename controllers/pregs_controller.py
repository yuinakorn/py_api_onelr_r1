import jwt
import logging
import httpx

import pymysql
import requests
from dotenv import dotenv_values
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse

from controllers.crypto_controller import decrypt_data, encrypt_data
from models.preg_crypto.pregs_crypto_model import DecryptInput
from models.pregs.pregs_model import DbPreg, DbConsult

from controllers.dashboard_controller import read_hostpitals, decrypt_result


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


def line_notify(token, new_preg, fullname):
    global cpd_icon
    url = config_env["LINE_NOTIFY_URL"]
    decoded_token = jwt.decode(token, config_env["SECRET_KEY"], algorithms=[config_env["ALGORITHM"]])
    hoscode = decoded_token["hosCode"]

    connection = get_connection()
    with connection.cursor() as cursor:
        sql = f"""
            SELECT * FROM hos_main_group
            WHERE FIND_IN_SET(%s, hoscode_group) > 0
            AND is_node = 'Y'
            """
        # print(sql % hoscode)
        cursor.execute(sql, hoscode)
        result = cursor.fetchone()
        # print("result: ", result)
        line_token = result["line_token"]
        # print("line token: ", line_token)

    hospital_data = read_hostpitals()
    hoscode_to_find = hoscode
    hosname = next((hospital["hosname"] for hospital in hospital_data if hospital["hoscode"] == hoscode_to_find), None)
    str_admit_date = str(new_preg.admit_date)
    admit_date = str_admit_date[:16]

    if 0 <= new_preg.cpd_risk_score < 5:
        cpd_icon = "🟢"
    elif 5 <= new_preg.cpd_risk_score <= 9.5:
        cpd_icon = "🟡"
    elif new_preg.cpd_risk_score > 9.5:
        cpd_icon = "🔴"

    msg = f"\n มีการลงทะเบียนคลอดรายใหม่จาก: *{hosname}* \n " \
          f"HN: {new_preg.hn} \n " \
          f"AN: {new_preg.an} \n " \
          f"ชื่อ: { fullname } \n " \
          f"{cpd_icon}CPD Risk: {new_preg.cpd_risk_score} \n " \
          f"อายุมารดา: {new_preg.age_y} ปี \n " \
          f"ส่วนสูงมารดา: {new_preg.height} ซม. \n " \
          f"จำนวนคลอดบุตร: {new_preg.parity} \n " \
          f"น้ำหนักที่เพิ่มขึ้น: {new_preg.weight_gain} กก. \n " \
          f"ขนาดยอดมดลูก: {new_preg.fundal_height} ซม. \n " \
          f"HCT: {new_preg.hematocrit} % \n " \
          f"น้ำหนักเด็ก(U/S): {new_preg.ultrasound} กรัม \n " \
          f"วันที่แอดมิท {admit_date} น. \n \n " \
          f"กรุณาเปิดลิงค์ในคอม: {config_env['FRONTEND_URL']}/#/patient/{hoscode_to_find}/{new_preg.an}/{new_preg.cid}"
    payload = {"message": msg}
    headers = {"Authorization": "Bearer " + line_token}
    httpx.post(url, data=payload, headers=headers)


async def line_notify_consult(hoscode_main, cid, an):
    url = config_env["LINE_NOTIFY_URL"]

    try:
        connection = pymysql.connect(
            host=config_env["DB_HOST"],
            user=config_env["DB_USER"],
            password=config_env["DB_PASSWORD"],
            db=config_env["DB_NAME"],
            charset=config_env["CHARSET"],
            port=int(config_env["DB_PORT"]),
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            sql = """
                SELECT p.*, c.*, h2.hosname AS hosname_main, h.hosname AS hosname_consult, h.line_token
                FROM t_pregancy p
                LEFT JOIN t_consult c ON p.hcode = c.hoscode_main AND p.cid = c.cid AND p.an = c.an
                LEFT JOIN hos_main_group h ON c.hoscode_consult = h.hoscode_main
                LEFT JOIN hos_main_group h2 ON c.hoscode_main = h2.hoscode_main
                WHERE c.hoscode_main = %s AND c.cid = %s AND c.an = %s
                LIMIT 1
            """
            cursor.execute(sql, (hoscode_main, cid, an))
            result = cursor.fetchall()
            
            print(f"SQL Query: {sql % (hoscode_main, cid, an)}")  # Debug print

            if result:
                result = result[0]
                
                # decrypt data
                # convert result to list
                decrypted_data = await decrypt_result([result])
                decrypt_data = decrypted_data[0]
                decrypt_pname = decrypt_data["pname"]
                decrypt_lname = decrypt_data["lname"]
                fullname = decrypt_data["title"] + decrypt_pname + " " + decrypt_lname[:1] + 'x' * (len(decrypt_lname) - 1)
                
                if 0 <= result['cpd_risk_score'] < 5:
                    cpd_icon = "🟢"
                elif 5 <= result['cpd_risk_score'] <= 9.5:
                    cpd_icon = "🟡"
                elif result['cpd_risk_score'] > 9.5:
                    cpd_icon = "🔴"

                msg = f"มีการปรึกษาคลอดรายใหม่จาก: *{result['hosname_main']}* \n" \
                    f"มายัง: *{result['hosname_consult']}* \n" \
                    f"HN: {result['hn']} \n" \
                    f"AN: {result['an']} \n" \
                    f"ชื่อ: {fullname} \n" \
                    f"{cpd_icon} CPD Risk: {result['cpd_risk_score']} \n" \
                    f"อายุมารดา: {result['age_y']} ปี \n" \
                    f"ส่วนสูงมารดา: {result['height']} ซม. \n" \
                    f"จำนวนคลอดบุตร: {result['parity']} \n" \
                    f"น้ำหนักเพิ่มขึ้น: {result['weight_gain']} กก. \n" \
                    f"ขนาดยอดมดลูก: {result['fundal_height']} ซม. \n" \
                    f"HCT: {result['hematocrit']} % \n" \
                    f"น้ำหนักเด็ก(U/S): {result['ultrasound']} กรัม \n" \
                    f"วันที่แอดมิท: {result['admit_date']} \n \n" \
                    f"กรุณาเปิดลิงค์ในคอมฯ: {config_env['FRONTEND_URL']}/#/patient/{hoscode_main}/{an}/{cid}"

                payload = {"message": msg}
                print("payload => ",payload)
                headers = {"Authorization": "Bearer " + result["line_token"]}
                httpx.post(url, data=payload, headers=headers)
                
                return result
            else:
                print("No result found")
                

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error", "message line": str(e)})
    finally:
        connection.close()


def token_decode(token):
    try:
        decoded_token = jwt.decode(token, config_env["SECRET_KEY"], algorithms=[config_env["ALGORITHM"]])
        return {"token_data": decoded_token, "is_valid": True}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})



# def read_preg(request, db: Session):
#     token = request.get("token")
#     if token_decode(token)['is_valid']:
#         return db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode']).all()

#     else:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail={"status": "error", "message": "You are not allowed!!"})


async def read_preg(request, db: Session):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        predata = db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode']).all()
        # Decrypt data for each entry in predata
        decrypted_predata = []
        for data in predata:
            data.cid_crypto = data.cid
            data.pname_crypto = data.pname
            data.lname_crypto = data.lname
            if data.cid and data.pname and data.lname and data.s_id:
                encrypted_data = DecryptInput(
                    cid=data.cid,
                    pname=data.pname,
                    lname=data.lname,
                    salt=data.s_id
                )
                decrypted_data = await decrypt_data(encrypted_data)
                # Assign decrypted values back to the data object or a new object
                data.cid = decrypted_data["cid"]
                data.pname = decrypted_data["pname"]
                data.lname = decrypted_data["lname"]
                # append ข้อมูลที่เข้ารหัสแล้วเข้าไปใน decrypted_predata
                decrypted_predata.append(data)
                
                
        print(decrypted_predata)
        return decrypted_predata

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})
        

# for main hospital (Pregs)
async def read_preg_all(request):
    token = request.get("token")
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=[config_env["ALGORITHM"]])

        if decoded_token:  # if token is valid
            # stmt = "" if decoded_token['hosCode'] == config_env['ADMIN_HOSCODE'] \
            #             else f"WHERE t_pregancy.hcode = {decoded_token['hosCode']} "

            connection = get_connection()
            with connection.cursor() as cursor:
                sql0 = f"""
                            SELECT hoscode_group FROM hos_main_group WHERE hoscode_main = {decoded_token['hosCode']}
                            """
                cursor.execute(sql0)
                result0 = cursor.fetchone()
                stmt = f""" WHERE t_pregancy.hcode IN({result0['hoscode_group']}) """
                sql = f"""SELECT t_pregancy.*,hos_main_group.hosname hosname_consult,chospital.hosname FROM t_pregancy 
                  INNER JOIN chospital ON chospital.hoscode = t_pregancy.hcode AND left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) AND CURRENT_DATE 
                  LEFT JOIN t_consult ON t_pregancy.hcode = t_consult.hoscode_main AND t_pregancy.cid = t_consult.cid AND t_pregancy.an = t_consult.an 
                  LEFT JOIN hos_main_group ON t_consult.hoscode_consult = hos_main_group.hoscode_main
                  {stmt}
                  ORDER BY admit_date DESC"""
                cursor.execute(sql)
                result = cursor.fetchall()
                
                # call function decrypt_result
                decrypted_data = await decrypt_result(result)
                
            return decrypted_data
        
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={"status": "error", "message": "You are not allowed!"})

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


async def search(db: Session, request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        data = db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode'],
                                         DbPreg.cid == request.get("cid"), DbPreg.an == request.get("an")).first()
        
        # Decrypt data onece
        if data.cid and data.pname and data.lname and data.s_id:
                data.cid_crypto = data.cid
                data.pname_crypto = data.pname
                data.lname_crypto = data.lname
                encrypted_data = DecryptInput(
                    cid=data.cid,
                    pname=data.pname,
                    lname=data.lname,
                    salt=data.s_id
                )
                decrypted_data = await decrypt_data(encrypted_data)
                # Assign decrypted values back to the data object or a new object
                data.cid = decrypted_data["cid"]
                data.pname = decrypted_data["pname"]
                data.lname = decrypted_data["lname"]
                return data
            
        
        # if result is None:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND, detail={
        #             "status": "error",
        #             "message": f"ไม่พบข้อมูลของ an {request.get('an')} ในระบบ"
        #         }
        #     )
        # else:
        #     return result

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


async def his_search(request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        api_url = f"{config_env['HIS_URL']}/person_anc/{request.get('hcode')}?cid={request.get('cid')}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=7)  # กำหนดเวลาในการรอ response 7 วินาที
                response.raise_for_status()  # Raise HTTPError for non-2xx responses
                result = response.json()

                if response is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail={
                            "status": "error",
                            "message": f"ไม่พบข้อมูลของ an {request.get('an')} ในระบบ"
                        }
                    )
                else:
                    return result
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={"status": "error", "message": f"Request timed out or query error"}
            )
        except httpx.HTTPError as http_err:
            raise HTTPException(
                status_code=http_err.response.status_code,
                detail={"status": "error", "message": http_err.response.text}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": str(e)}
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "You are not allowed!!"}
        )


async def his_search_img(request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        api_url = f"{config_env['HIS_URL']}/person_anc_img/{request.get('hcode')}?cid={request.get('cid')}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=7)  # กำหนดเวลาในการรอ response 7 วินาที
                response.raise_for_status()  # Raise HTTPError for non-2xx responses
                result = response.json()[0]
                return result
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={"status": "error", "message": f"Request timed out or query error"}
            )
        except httpx.HTTPError as http_err:
            raise HTTPException(
                status_code=http_err.response.status_code,
                detail={"status": "error", "message": http_err.response.text}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": str(e)}
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "You are not allowed!!"}
        )


def token_check(request):
    token = request.get("token")
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_data = {
            "hoscode": decoded_token["hosCode"],
            # "username": decoded_token["username"],
            # "user_cid": decoded_token["cid"]
        }
        # print(user_data)
        message = "Token is valid"
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"status": "ok", "message": message, "data": user_data})

    except jwt.InvalidTokenError:
        message = "Token is invalid!!"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": message})


async def create(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        current_date = datetime.now()
        image = str(request.image).replace("\n", "")
        if image == 'None':
            image = None

        encrypt_datas = await encrypt_data(request)
        encrypted_cid = encrypt_datas["encrypted_cid"]
        encrypted_pname = encrypt_datas["encrypted_pname"]
        encrypted_lname = encrypt_datas["encrypted_lname"]
        salt = encrypt_datas["salt"]

        new_preg = DbPreg(
            hcode=token_decode(token)['token_data']['hosCode'],
            # cid=request.cid,
            cid=encrypted_cid,
            hn="".join(request.hn.split("/")),
            an="".join(request.an.split("/")),
            admit_date=request.admit_date,
            title=request.title,
            # pname=request.pname,
            pname=encrypted_pname,
            # lname=request.lname,
            lname=encrypted_lname,
            age_y=request.age_y,
            gravida=request.gravida,
            parity=request.parity,
            ga=request.ga,
            anc_check_up=request.anc_check_up,
            no_of_anc=request.no_of_anc,
            weight_before_pregancy=request.weight_before_pregancy,
            weight_at_delivery=request.weight_at_delivery,
            weight_gain=request.weight_gain,
            height=request.height,
            fundal_height=request.fundal_height,
            hematocrit=request.hematocrit,
            ultrasound=request.ultrasound,
            cpd_risk_score=request.cpd_risk_score,
            status=request.status,
            create_date=current_date,
            modify_date=request.modify_date,
            user_create=request.user_create,
            user_last_modify=request.user_last_modify,
            refer_status=request.refer_status,
            refer_out_status=request.refer_out_status,
            image=image,
            s_id=salt
        )
        try:
            db.add(new_preg)
            db.commit()
            db.refresh(new_preg)
            if new_preg:
                lname = request.lname[:1] + 'x' * (len(request.lname) - 1)
                fullname = request.title + request.pname + " " + lname
                line_notify(token, new_preg, fullname)
            return {"message": "ok", "detail": new_preg}
        except SQLAlchemyError as e:
            db.rollback()
            error_message = f"Error creating preg: {str(e)}"
            logging.error(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


def update(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        print("request =>", request)
        result = db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode'],
                                         DbPreg.cid == request.cid,
                                         DbPreg.an == request.an).first()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": f"ไม่พบข้อมูลของ an {request.an}"
                }
            )
        else:
            now = datetime.now()
            modify_date = now.strftime("%Y-%m-%d %H:%M:%S")
            result.hcode = token_decode(token)['token_data']['hosCode']
            # image = request.image.replce("\n", "")
            image = str(request.image).replace("\n", "")
            result.cid = request.cid
            result.hn = request.hn
            result.an = request.an
            result.admit_date = request.admit_date
            result.title = request.title
            result.pname = request.pname
            result.lname = request.lname
            result.age_y = request.age_y
            result.gravida = request.gravida
            result.parity = request.parity
            result.ga = request.ga
            result.anc_check_up = request.anc_check_up
            result.no_of_anc = request.no_of_anc
            result.weight_before_pregancy = request.weight_before_pregancy
            result.weight_at_delivery = request.weight_at_delivery
            result.weight_gain = request.weight_gain
            result.height = request.height
            result.fundal_height = request.fundal_height
            result.hematocrit = request.hematocrit
            result.ultrasound = request.ultrasound
            result.cpd_risk_score = request.cpd_risk_score
            result.status = request.status
            result.modify_date = modify_date
            result.user_last_modify = request.user_last_modify
            result.refer_status = request.refer_status
            result.refer_out_status = request.refer_out_status
            result.image = image

            try:
                db.commit()
                db.refresh(result)
                return {"message": "ok", "detail": result}
            except SQLAlchemyError as e:
                db.rollback()
                error_message = f"Error updating preg: {str(e)}"
                logging.error(error_message)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})

# ฟังก์ชั่นที่ใช้ในการเข้ารหัสข้อมูลทั้งหมด
async def force_encrypt(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        # เฉพาะที่ cid = 13 หลัก
        result = db.query(DbPreg).filter(func.length(DbPreg.cid) == 13).all()
        # create loop for encrypt data
        for data in result:
            encrypt_datas = await encrypt_data(data)
            encrypted_cid = encrypt_datas["encrypted_cid"]
            encrypted_pname = encrypt_datas["encrypted_pname"]
            encrypted_lname = encrypt_datas["encrypted_lname"]
            salt = encrypt_datas["salt"]
            data.cid = encrypted_cid
            data.pname = encrypted_pname
            data.lname = encrypted_lname
            data.s_id = salt
        try:
            db.commit()
            connection = get_connection()
            with connection.cursor() as cursor:
                # update ตาราง progress
                sql = """
                        UPDATE progress
                        INNER JOIN t_pregancy ON progress.hcode = t_pregancy.hcode AND progress.an = t_pregancy.an
                        SET progress.cid = t_pregancy.cid
                        """
                cursor.execute(sql)
                connection.commit()
                # update ตาราง t_consult
                sql2 = """
                        UPDATE t_consult
                        INNER JOIN t_pregancy ON t_consult.hoscode_main = t_pregancy.hcode AND t_consult.an = t_pregancy.an
                        SET t_consult.cid = t_pregancy.cid
                        """
                cursor.execute(sql2)
                connection.commit()
            return {"message": "encrypted all", "status": "done"}
        except SQLAlchemyError as e:
            db.rollback()
            error_message = f"Error force encrypting preg: {str(e)}"
            logging.error(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"status": "error", "message": error_message})
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})

def delete(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        result = db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode'],
                                         DbPreg.cid == request.cid,
                                         DbPreg.an == request.an).first()
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
                error_message = f"Error deleting preg: {str(e)}"
                logging.error(error_message)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": error_message})

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


# def consult(db: Session, request):
#     global new_consult
#     try:
#         token = request.get("token")
#         if not token_decode(token)['is_valid']:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#         else:
#             print("token is valid")

#         cid = token_decode(token)['token_data']['cid']

#         # Check if the consult record already exists
#         existing_consult = db.query(DbConsult).filter_by(
#             hoscode_main=request.hoscode_main,
#             cid=request.cid,
#             an=request.an
#         ).first()

#         if existing_consult:
#             # If exists, update the existing record
#             print("Updating existing consult record")
#             existing_consult.by_user_cid = cid
#             existing_consult.hoscode_consult = request.hoscode_consult
#             existing_consult.datetime_created = datetime.now()
#         else:
#             # Otherwise, create a new consult record
#             print("Creating new consult record")
#             new_consult = DbConsult(
#                 hoscode_main=request.hoscode_main,
#                 cid=request.cid,
#                 an=request.an,
#                 hoscode_consult=request.hoscode_consult,
#                 by_user_cid=cid,
#                 datetime_created=datetime.now(),
#                 seen='N'
#             )
#             db.add(new_consult)

        
#             db.commit()
#             db.refresh(existing_consult if existing_consult else new_consult)

#             line_notify_consult(request.hoscode_main, request.cid, request.an)

#             return {"message": "ok", "detail": existing_consult if existing_consult else new_consult}
#     except SQLAlchemyError as e:
#         db.rollback()
#         error_message = f"Error in consult operation: {str(e)}"
#         logging.error(error_message)
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail={"status": "error sqlalchemy", "message": error_message})
#     except HTTPException as e:
#         logging.error(f"HTTPException: {str(e.detail)}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail={"status": "error exception", "message": str(e)})


async def consult(db: Session, request):
    global new_consult
    
    try:
        token = request.get("token")
        if token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is missing in the request")

        token_data = token_decode(token)
        if not token_data['is_valid']:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        logging.info("Token is valid")

        cid = token_data.get('token_data', {}).get('cid')

        if cid is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CID is missing in the token data")

        # Ensure that request has required attributes
        if not all(hasattr(request, attr) for attr in ['hoscode_main', 'cid', 'an', 'hoscode_consult']):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is missing one or more required attributes")
        
        else:
            print("Request has all required attributes")
        
        # Check if the consult record already exists
        existing_consult = db.query(DbConsult).filter_by(
            hoscode_main=request.hoscode_main,
            cid=request.cid,
            an=request.an
        ).first()

        if existing_consult:
            # If exists, update the existing record
            print("Updating existing consult record")
            existing_consult.by_user_cid = cid
            existing_consult.hoscode_consult = request.hoscode_consult
            existing_consult.datetime_created = datetime.now()
        else:
            # Otherwise, create a new consult record
            print("Creating new consult record")
            new_consult = DbConsult(
                hoscode_main=request.hoscode_main,
                cid=request.cid,
                an=request.an,
                hoscode_consult=request.hoscode_consult,
                by_user_cid=cid,
                datetime_created=datetime.now(),
                seen='N'
            )
            db.add(new_consult)

        
        db.commit()
        db.refresh(existing_consult if existing_consult else new_consult)

        result_notify = await line_notify_consult(request.hoscode_main, request.cid, request.an)
        
        if result_notify:
            return {"message": "ok", "detail": existing_consult if existing_consult else new_consult}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error sending line notification")

        # return {"message": "ok", "detail": existing_consult if existing_consult else new_consult}
    except SQLAlchemyError as e:
        db.rollback()
        error_message = f"SQLAlchemy Error in consult operation: {str(e)}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error sqlalchemy", "message": error_message})
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e.detail)}")
        raise
    except Exception as e:
        error_message = f"Unexpected error in consult operation: {str(e)}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error exception", "message": error_message})


def hoscode_group(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        decoded_token = jwt.decode(token, config_env["SECRET_KEY"], algorithms=[config_env["ALGORITHM"]])
        hoscode = decoded_token["hosCode"]

        connection = get_connection()
        with connection.cursor() as cursor:
            sql = f"""
                    SELECT * FROM hos_main_group
                    WHERE hoscode_main = %s
                    AND is_node_master = 'Y'
                """
            cursor.execute(sql, hoscode)

            # ถ้า hoscode นั้นเป็น node master จะได้ hoscode ของลูกข่ายทั้งจังหวัด
            result = cursor.fetchone()
            if result is not None:
                hoscode_group = result["hoscode_group"]

                return {"status": "success", "hoscode_group": hoscode_group}
            # ถ้าไม่ใช่ node master จะต้องเช็คว่าเป็น node หรือไม่
            elif result is None:
                sql2 = f"""
                            SELECT * FROM hos_main_group
                            WHERE hoscode_main = %s
                        """
                # print(sql2 % hoscode)
                cursor.execute(sql2, hoscode)
                # ถ้าใช่ node จะได้ hoscode ของลูกข่ายในอำเภอ
                result2 = cursor.fetchone()
                if result2 is not None:
                    hoscode_group = result2["hoscode_group"]

                    return {"status": "success", "hoscode_group": hoscode_group}
                else:
                    return {"status": "error", "message": "You are not allowed!!"}

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}


async def upload_image(token: str = None, file: UploadFile = File(...), hoscode: str = None, an: str = None):

    if token_decode(token)['is_valid']:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        try:
            contents = await file.read()

            file_type = file.content_type.split("/")[1]

            # if file_type is image then resize quality to 70%
            if file_type in ["jpeg", "png"]:
                from PIL import Image
                from io import BytesIO

                img = Image.open(BytesIO(contents))
                img.save(f"uploads/{hoscode}_{an}.{file_type}", quality=70)
            else:
                with open(f"uploads/{hoscode}_{an}.{file_type}", "wb") as f:
                    f.write(contents)

            file_name = f"{hoscode}_{an}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            with open(f"uploads/{file_name}.{file_type}", "wb") as f:
                f.write(contents)

            return JSONResponse(status_code=200,
                                content={"message": "File uploaded successfully", "filename": f"{file_name}.{file_type}"})
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


async def create_message(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = f"""INSERT INTO t_message (hcode, hname, cid, hn, an, message, doctor_name, datetime_created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

                cursor.execute(sql, (request.hcode, request.hname, request.cid, request.hn, request.an, request.message, request.doctor_name, datetime.now()))
                connection.commit()
                
                return JSONResponse(status_code=200, content={"message": "Message created successfully"})
        
        except SQLAlchemyError as e:
            return JSONResponse(status_code=500, content={"message": "An error SQLAlchemyError", "details": str(e)})      
          
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})
        
        
        finally :
            connection.close()

            
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})
        
        
async def read_message(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = f"""SELECT * FROM t_message WHERE hcode = %s AND hn = %s AND an = %s"""
                cursor.execute(sql, (request.hcode, request.hn, request.an))
                result = cursor.fetchall()
                
                return result
        
        except SQLAlchemyError as e:
            return JSONResponse(status_code=500, content={"message": "An error SQLAlchemyError", "details": str(e)})
                
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})
        
        
        finally :
            connection.close()