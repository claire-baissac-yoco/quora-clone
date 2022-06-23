import psycopg2
import urllib.parse as urlparse
import os
import redis


def connect_db():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    con = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cursor = con.cursor()
    return con, cursor


def connect_redis():
    redis_host = os.environ.get("REDIS_HOST")
    redis_port = os.environ.get("REDIS_PORT")
    redis_password = os.environ.get("REDIS_PASSWORD")
    r = redis.Redis(
        host=redis_host, port=redis_port, password=redis_password)
