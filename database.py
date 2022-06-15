import psycopg2
import os
from dotenv import load_dotenv
from utils import encrypt_password, user_password_is_valid, validate_user_password


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


def validate_user_login(conn, cursor, email, password):
    query = 'SELECT "firstName", "lastName", "password" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        print(result)
        first_name, last_name, hashed_password = result
        return validate_user_password(bytes(hashed_password), password), {"first_name": first_name, "last_name": last_name}
    except Exception as e:
        print("Failed to login user")
        print(e)


def validate_user_change_password(conn, cursor, email, old_password, new_password):
    print("VALIDATE USER CHANGE PASSWORD")
    query = 'SELECT "password" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        print(result)
        hashed_password = result
        if validate_user_password(bytes(hashed_password), old_password) and user_password_is_valid(new_password):
            return not old_password == new_password
        return False
    except Exception as e:
        print("Failed to change password")
        print(e)


def close_db(conn):
    conn.close()
