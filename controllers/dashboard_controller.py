import jwt
import logging
import json

import pymysql
from dotenv import dotenv_values
from datetime import datetime

from models.pregs.pregs_model import DbConsult

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

config_env = dotenv_values(".env")


def token_decode(token):
    secret_key = config_env["SECRET_KEY"]
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=[config_env["ALGORITHM"]])
        return {"token_data": decoded_token, "is_valid": True}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


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


def read_province():
    connection = pymysql.connect(host=config_env["DB_HOST"],
                                 user=config_env["DB_USER"],
                                 password=config_env["DB_PASSWORD"],
                                 db=config_env["DB_NAME"],
                                 charset=config_env["CHARSET"],
                                 port=int(config_env["DB_PORT"]),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )

    with connection.cursor() as cursor:
        sql = """
            SELECT code, name_th FROM provinces
            WHERE code in ("50","51","52","54","55","56","57","58")
        """
        cursor.execute(sql)
        result = cursor.fetchall()
        connection.close()

        return result


def read_province_by_hcode(hcode):
    try:
        connection = pymysql.connect(host=config_env["DB_HOST"],
                                     user=config_env["DB_USER"],
                                     password=config_env["DB_PASSWORD"],
                                     db=config_env["DB_NAME"],
                                     charset=config_env["CHARSET"],
                                     port=int(config_env["DB_PORT"]),
                                     cursorclass=pymysql.cursors.DictCursor
                                     )

        with connection.cursor() as cursor:
            sql = """SELECT p.code,p.name_th FROM chospital h
                LEFT JOIN provinces p ON h.provcode = p.code
                WHERE hoscode = %s"""

            cursor.execute(sql, hcode)
            result = cursor.fetchone()
            connection.close()

            return {"province_code": result["code"], "province_name": result["name_th"]}

    except pymysql.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {e}")






def read_hostpitals():
    connection = pymysql.connect(host=config_env["DB_HOST"],
                                 user=config_env["DB_USER"],
                                 password=config_env["DB_PASSWORD"],
                                 db=config_env["DB_NAME"],
                                 charset=config_env["CHARSET"],
                                 port=int(config_env["DB_PORT"]),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )

    with connection.cursor() as cursor:
        sql = """
              SELECT provcode as provinceCode,hoscode,hosname FROM chospital 
              WHERE provcode in ("50","51","52","54","55","56","57","58") 
              AND hostype in (5,6,7)
              """
        cursor.execute(sql)
        result = cursor.fetchall()
        connection.close()

        return result


def read_dashboard_all():
    # connection = get_connection()
    connection = pymysql.connect(host=config_env["DB_HOST"],
                                 user=config_env["DB_USER"],
                                 password=config_env["DB_PASSWORD"],
                                 db=config_env["DB_NAME"],
                                 charset=config_env["CHARSET"],
                                 port=int(config_env["DB_PORT"]),
                                 cursorclass=pymysql.cursors.DictCursor
                                 )
    with connection.cursor() as cursor:
        sql = "SELECT hcode,chospital.hosname as hosname, " \
              "count(if(cpd_risk_score < 5,hn,NULL)) as green, " \
              "count(if(cpd_risk_score >= 5 AND cpd_risk_score <= 9.5,hn,NULL)) as yellow, " \
              "count(if(cpd_risk_score >=10,hn,NULL)) as red, " \
              "SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) as subdate, " \
              "CURRENT_DATE as currentdate " \
              "FROM t_pregancy " \
              "INNER JOIN chospital on chospital.hoscode = t_pregancy.hcode " \
              "WHERE left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) AND CURRENT_DATE " \
              "GROUP BY t_pregancy.hcode"
        cursor.execute(sql)
        result = cursor.fetchall()
        connection.close()

        return result


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def read_hospital_by_hcode(hcode):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = "SELECT chospital.hosname, t_pregancy.*,hos_main_group.hosname hosname_consult FROM t_pregancy " \
                  "INNER JOIN chospital ON t_pregancy.hcode = chospital.hoscode " \
                  "LEFT JOIN t_consult ON t_pregancy.hcode = t_consult.hoscode_main AND t_pregancy.cid = t_consult.cid AND t_pregancy.an = t_consult.an " \
                  "LEFT JOIN hos_main_group ON t_consult.hoscode_consult = hos_main_group.hoscode_main " \
                  "WHERE hcode = %s " \
                  "AND left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) AND CURRENT_DATE"

            cursor.execute(sql, hcode)
            result = cursor.fetchall()
        connection.close()

        return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {e}")


def read_patient_by_an(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = """
                        SELECT t_pregancy.*,t_consult.hoscode_consult,chospital.hosname FROM t_pregancy 
                        LEFT JOIN t_consult ON t_pregancy.hcode = t_consult.hoscode_main AND t_pregancy.an = t_consult.an
                        LEFT JOIN chospital ON t_consult.hoscode_consult = chospital.hoscode
                        WHERE t_pregancy.hcode = %s AND t_pregancy.an = %s
                        ORDER BY t_consult.id DESC 
                        LIMIT 1
                    """
                cursor.execute(sql, (request.get("hoscode"), request.get("an")))
                result = cursor.fetchone()
                connection.close()
                return result

        except pymysql.Error as e:
            raise HTTPException(500, f"Database error: {e}")
        except Exception as e:
            raise HTTPException(500, f"An error occurred: {e}")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})



def read_hospital_by_an(hcode, an):
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "select " \
              "JSON_ARRAYAGG(d.v) jdata " \
              "from( " \
              "SELECT " \
              "cid,an,hcode, " \
              "JSON_OBJECT(ccode.code_name, " \
              "JSON_ARRAYAGG( " \
              "JSON_OBJECT('update_time',progress_date_time, " \
              "'time',time(progress_date_time), " \
              "'value',value) " \
              ")) v " \
              "from progress " \
              "INNER JOIN ccode on progress.`code`=ccode.`code` " \
              "WHERE progress.`code` not in('C06','C07') " \
              "AND hcode=%s " \
              "and an=%s " \
              "GROUP BY cid,an,hcode,ccode.`code` " \
              "union all " \
              "SELECT " \
              "cid,an,hcode, " \
              "JSON_OBJECT('bp', " \
              "JSON_ARRAYAGG( " \
              "JSON_OBJECT('update_time',progress_date_time, " \
              "'time',time(progress_date_time), " \
              "'value1',SBP,'value2',DBP) " \
              ")) v " \
              "from (SELECT " \
              "cid,an,hcode, " \
              "progress.progress_date_time, " \
              "mid(value,1,instr(value,'/')-1) as  'SBP', " \
              "mid(value,instr(value,'/')+1,3) as  'DBP' " \
              "from progress " \
              "INNER JOIN ccode on progress.`code`=ccode.`code` " \
              "WHERE progress.`code` ='C06' " \
              "AND hcode=%s " \
              "and an=%s " \
              "GROUP BY cid,an,hcode,time(progress_date_time) " \
              ") progress " \
              ") d"
        value = (hcode, an, hcode, an)
        cursor.execute(sql, value)
        result = cursor.fetchall()
        data = result[0]['jdata']
        formatted_data = json.loads(data)

        connection.close()

        return formatted_data


def read_hos_node(request):
    global hoscode
    token = request.get("token")
    if token_decode(token)['is_valid']:
        decoded_token = jwt.decode(token, config_env["SECRET_KEY"], algorithms=[config_env["ALGORITHM"]])
        hoscode = decoded_token["hosCode"]

    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = "SELECT provcode FROM chospital WHERE hoscode = %s"
            cursor.execute(sql, hoscode)
            result = cursor.fetchone()
            provcode = result["provcode"]

            sql = f"""
                SELECT hoscode_main,hosname FROM hos_main_group 
                WHERE provcode = %s AND is_node = 'Y' OR is_node_master = 'Y' 
                ORDER BY priority_level
                """
            cursor.execute(sql, provcode)
            result = cursor.fetchall()

            connection.close()
            return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {e}")


def read_hospital_name(hcode):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = "SELECT hosname FROM chospital WHERE hoscode = %s"
            cursor.execute(sql, hcode)
            result = cursor.fetchone()
            connection.close()

            return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {e}")


def read_pregs_consult(request):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        hoscode = token_decode(token)['token_data']['hosCode']
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = f"""SELECT h.hosname,p.*,c.hoscode_consult,c.datetime_created FROM t_pregancy p
                        LEFT JOIN t_consult c ON p.hcode = c.hoscode_main AND p.cid = c.cid AND p.an = c.an
                        LEFT JOIN hos_main_group h ON p.hcode = h.hoscode_main
                        WHERE c.hoscode_consult = %s
                        AND left(p.admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 7 DAY) AND CURRENT_DATE
                        ORDER BY p.admit_date DESC"""
                cursor.execute(sql, hoscode)
                result = cursor.fetchall()
                connection.close()

                return result
        except pymysql.Error as e:
            raise HTTPException(500, f"Database error: {e}")
        except Exception as e:
            raise HTTPException(500, f"An error occurred: {e}")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})


def read_notify_count(hoscode_consult, db: Session):
    count_not_seen = db.query(DbConsult).filter_by(hoscode_consult=hoscode_consult, seen='N').count()
    return {"count": count_not_seen}


def update_consulted(request, db: Session):
    token = request.get("token")
    if token_decode(token)['is_valid']:
        hoscode = token_decode(token)['token_data']['hosCode']
        try:
            db.query(DbConsult).filter_by(hoscode_consult=hoscode, seen='N').update({"seen": "Y"})
            db.commit()
            return {"status": "success", "message": "Consulted status updated successfully"}
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(500, f"Database error: {e}")
        except Exception as e:
            raise HTTPException(500, f"An error occurred: {e}")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"status": "error", "message": "Token is invalid!!"})

