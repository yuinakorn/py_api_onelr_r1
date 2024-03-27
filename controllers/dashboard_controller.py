import jwt
import logging
import json

import pymysql
from dotenv import dotenv_values
from datetime import datetime

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
        sql = "SELECT hoscode,hosname FROM chospital " \
              "WHERE provcode = '51' " \
              "AND hostype in (5,6,7)"
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
              "SUBDATE(CURRENT_DATE,INTERVAL 5 DAY) as subdate, " \
              "CURRENT_DATE as currentdate " \
              "FROM t_pregancy " \
              "INNER JOIN chospital on chospital.hoscode = t_pregancy.hcode " \
              "WHERE left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 5 DAY) AND CURRENT_DATE " \
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
            sql = "SELECT chospital.hosname, t_pregancy.* FROM t_pregancy " \
                  "INNER JOIN chospital ON t_pregancy.hcode = chospital.hoscode " \
                  "WHERE hcode = %s " \
                  "AND left(admit_date,10) BETWEEN SUBDATE(CURRENT_DATE,INTERVAL 5 DAY) AND CURRENT_DATE"

            cursor.execute(sql, hcode)
            result = cursor.fetchall()
        connection.close()

        return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {e}")


def read_patient_by_an(hcode, an):
    connection = get_connection()
    with connection.cursor() as cursor:
        # execute with bind param
        sql = "SELECT * FROM t_pregancy WHERE hcode = %s AND an = %s"
        value = (hcode, an)
        cursor.execute(sql, value)
        result = cursor.fetchone()
        connection.close()

        return result


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
