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

    # # Executing an MYSQL function using the execute() method
    # cursor.execute("select version()")

    # # Fetch a single row using fetchone() method.
    # data = cursor.fetchone()
    # print("Connection established to: ", data)
    return conn, cursor


def insert_user(conn, cursor, first_name, last_name, email, password):
    query = 'INSERT INTO public.\"Users\" ("firstName", "lastName", "email", "password") VALUES (%s, %s, %s, %s) RETURNING id;'
    try:
        cursor.execute(query, (first_name, last_name,
                       email, encrypt_password(password)))
        id = cursor.fetchone()[0]
        conn.commit()
        return id
    except Exception as e:
        print("Failed to insert into table")
        print(e)


def validate_user_login(conn, cursor, email, password):
    query = 'SELECT "id", "firstName", "lastName", "password" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        print(result)
        id, first_name, last_name, hashed_password = result
        print(hashed_password)
        return validate_user_password(bytes(hashed_password), password), {"first_name": first_name, "last_name": last_name, "id": id}
    except Exception as e:
        print("Failed to login user")
        print(e)


def validate_user_change_password(conn, cursor, email, old_password, new_password):
    print("VALIDATE USER CHANGE PASSWORD")
    query = 'SELECT "email", "password" FROM public.\"Users\" WHERE email = %s;'
    query_change_password = 'UPDATE public.\"Users\" SET password = %s WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        ret_email, hashed_password = result
        print(ret_email, bytes(hashed_password))
        if validate_user_password(bytes(hashed_password), old_password) and user_password_is_valid(new_password) and not old_password == new_password:
            cursor.execute(query_change_password,
                           (encrypt_password(new_password), email))
            conn.commit()
            return True
        return False
    except Exception as e:
        print("Failed to change password")
        print(e)


# def close_db(conn):
#     conn.close()
