import psycopg2
import os
from dotenv import load_dotenv

from utils import encrypt_password


def connect_db():
    load_dotenv()
    DATABASE = os.getenv('DATABASE')
    USER = os.getenv('USER')
    PASSWORD = os.getenv('PASSWORD')
    HOST = os.getenv('HOST')
    DB_PORT = os.getenv('DB_PORT')

    conn = psycopg2.connect(database=DATABASE, user=USER,
                            password=PASSWORD, host=HOST, port=DB_PORT)

    cursor = conn.cursor()

    # Executing an MYSQL function using the execute() method
    cursor.execute("select version()")

    # Fetch a single row using fetchone() method.
    data = cursor.fetchone()
    print("Connection established to: ", data)
    return conn, cursor


def insert_user(conn, cursor, first_name, last_name, email, password):
    query = 'INSERT INTO public.\"Users\" ("firstName", "lastName", "email", "password") VALUES (%s, %s, %s, %s);'
    try:
        cursor.execute(query, (first_name, last_name,
                       email, encrypt_password(password)))
        conn.commit()
    except Exception as e:
        print("Failed to insert into table")
        print(e)


def close_db(conn):
    conn.close()
