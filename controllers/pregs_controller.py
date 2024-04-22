import jwt
import logging
import httpx

import pymysql
import requests
from dotenv import dotenv_values
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from models.pregs.pregs_model import DbPreg, DbChospital, DbConsult
from controllers.dashboard_controller import read_hostpitals

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


def line_notify(token, new_preg):
    global cpd_icon
    url = config_env["LINE_NOTIFY_URL"]
    # line_token = config_env["LINE_NOTIFY_TOKEN"]
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
          f"อายุ: {new_preg.age_y} ปี \n " \
          f"{cpd_icon}CPD Risk: {new_preg.cpd_risk_score} \n " \
          f"Hematocrit: {new_preg.hematocrit} % \n " \
          f"ยอดมดลูก: {new_preg.fundal_height} ซม. \n " \
          f"น้ำหนักเด็ก(U/S): {new_preg.ultrasound} กรัม \n " \
          f"วันที่แอดมิท {admit_date} น. \n \n " \
          f"กรุณาเปิดลิงค์ในคอมฯ: {config_env['FRONTEND_URL']}/#/patient/{hoscode_to_find}/{new_preg.an}/{new_preg.cid}"
    payload = {"message": msg}
    headers = {"Authorization": "Bearer " + line_token}
    httpx.post(url, data=payload, headers=headers)


def line_notify_consult(hoscode_main, cid, an):
    url = config_env["LINE_NOTIFY_URL"]

    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = f"""
                SELECT p.*,c.*,h2.hosname hosname_main,h.hosname hosname_consult,h.line_token
                 FROM t_pregancy p
                LEFT JOIN t_consult c ON p.hcode = c.hoscode_main AND p.cid = c.cid AND p.an = c.an
                LEFT JOIN hos_main_group h ON c.hoscode_consult = h.hoscode_main
                LEFT JOIN hos_main_group h2 ON c.hoscode_main = h2.hoscode_main
                WHERE c.hoscode_main = %s AND c.cid = %s AND c.an = %s
                LIMIT 1
            """
            cursor.execute(sql, (hoscode_main, cid, an))
            result = cursor.fetchone()
            line_token = result["line_token"]

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
              f"{cpd_icon} CPD Risk: {result['cpd_risk_score']} \n" \
              f"อายุ: {result['age_y']} ปี \n" \
              f"ครรภ์ที่: {result['gravida']} \n" \
              f"อายุครรภ์: {result['ga']} w \n" \
              f"จำนวนการตรวจ ANC: {result['no_of_anc']} \n" \
              f"น้ำหนักเพิ่มขึ้น: {result['weight_gain']} กก. \n" \
              f"ส่วนสูง: {result['height']} ซม. \n" \
              f"ยอดมดลูก: {result['fundal_height']} ซม. \n" \
              f"Hematocrit: {result['hematocrit']} % \n" \
              f"น้ำหนักเด็ก(U/S): {result['ultrasound']} กรัม \n" \
              f"วันที่แอดมิท: {result['admit_date']} \n \n" \
              f"กรุณาเปิดลิงค์ในคอมฯ: {config_env['FRONTEND_URL']}/#/patient/{hoscode_main}/{an}/{cid}"

        payload = {"message": msg}
        headers = {"Authorization": "Bearer " + line_token}
        httpx.post(url, data=payload, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error", "message": str(e)})


def token_decode(token):
    try:
        decoded_token = jwt.decode(token, config_env["SECRET_KEY"], algorithms=[config_env["ALGORITHM"]])
        return {"token_data": decoded_token, "is_valid": True}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


def read_preg(request, db: Session):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        return db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode']).all()

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "You are not allowed!!"})


# for main hospital (Pregs)
def read_preg_all(request):
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
                sql = f"""
                  SELECT t_pregancy.*,hos_main_group.hosname hosname_consult,chospital.hosname FROM t_pregancy 
                  INNER JOIN chospital ON chospital.hoscode = t_pregancy.hcode AND left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) AND CURRENT_DATE 
                  LEFT JOIN t_consult ON t_pregancy.hcode = t_consult.hoscode_main AND t_pregancy.cid = t_consult.cid AND t_pregancy.an = t_consult.an 
                  LEFT JOIN hos_main_group ON t_consult.hoscode_consult = hos_main_group.hoscode_main
                  {stmt}
                  ORDER BY admit_date DESC"""
                cursor.execute(sql)
                result = cursor.fetchall()
            return result
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={"status": "error", "message": "You are not allowed!"})

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


def search(db: Session, request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        result = db.query(DbPreg).filter(DbPreg.hcode == token_decode(token)['token_data']['hosCode'],
                                         DbPreg.cid == request.get("cid"), DbPreg.an == request.get("an")).first()
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


def his_search(request):
    token = request.get("token")

    if token_decode(token)['is_valid']:
        auth = {}
        api_url = f"{config_env['HIS_URL']}/person_anc/{request.get('hcode')}?cid={request.get('cid')}"
        response = requests.get(api_url, auth=auth)
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


def create(db: Session, request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        current_date = datetime.now()
        image = str(request.image).replace("\n", "")
        new_preg = DbPreg(
            hcode=token_decode(token)['token_data']['hosCode'],
            cid=request.cid,
            hn=request.hn,
            an=request.an,
            admit_date=request.admit_date,
            title=request.title,
            pname=request.pname,
            lname=request.lname,
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
        )
        try:
            db.add(new_preg)
            db.commit()
            db.refresh(new_preg)
            if new_preg:
                line_notify(token, new_preg)
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


def consult(db: Session, request):
    global new_consult
    token = request.get("token")
    if not token_decode(token)['is_valid']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    cid = token_decode(token)['token_data']['cid']

    # Check if the consult record already exists
    existing_consult = db.query(DbConsult).filter_by(
        hoscode_main=request.hoscode_main,
        cid=request.cid,
        an=request.an
    ).first()

    if existing_consult:
        # If exists, update the existing record
        existing_consult.by_user_cid = cid
        existing_consult.hoscode_consult = request.hoscode_consult
        existing_consult.datetime_created = datetime.now()
    else:
        # Otherwise, create a new consult record
        new_consult = DbConsult(
            hoscode_main=request.hoscode_main,
            cid=request.cid,
            an=request.an,
            hoscode_consult=request.hoscode_consult,
            by_user_cid=cid,
            datetime_created=datetime.now()
        )
        db.add(new_consult)

    try:
        db.commit()
        db.refresh(existing_consult if existing_consult else new_consult)

        line_notify_consult(request.hoscode_main, request.cid, request.an)

        return {"message": "ok", "detail": existing_consult if existing_consult else new_consult}
    except SQLAlchemyError as e:
        db.rollback()
        error_message = f"Error in consult operation: {str(e)}"
        logging.error(error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error", "message": error_message})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"status": "error", "message": str(e)})


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
                            AND is_node = 'Y'
                        """
                print(sql2 % hoscode)
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
