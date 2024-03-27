from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib import parse

import pymysql.cursors

config_env = dotenv_values(".env")

engine = create_engine("mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4".format(
    user=config_env['DB_USER'],
    password=parse.quote_plus(config_env['DB_PASSWORD']),
    host=config_env['DB_HOST'],
    port=config_env['DB_PORT'],
    db_name=config_env['DB_NAME'],
    pool_size=50,
    max_overflow=100,
    # pool_recycle=240,
    # wait_time=28800,
))

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    try:
        db = session_local()
        yield db
    finally:
        db.close()



