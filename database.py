from utils import encrypt_password, user_password_is_valid, validate_user_password
import os
import psycopg2
from dotenv import load_dotenv


def connect_db_local():
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


def insert_user(conn, cursor, first_name: str, last_name: str, email: str, password: str) -> str:
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


def validate_user_login(conn, cursor, email: str, password: str) -> bool:
    query = 'SELECT "id", "firstName", "lastName", "password" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        id, first_name, last_name, hashed_password = result
        return validate_user_password(bytes(hashed_password), password), {"first_name": first_name, "last_name": last_name, "id": id}
    except Exception as e:
        print("Failed to login user")
        print(e)


def validate_user_change_password(conn, cursor, email: str, old_password: str, new_password: str) -> bool:
    query = 'SELECT "email", "password" FROM public.\"Users\" WHERE email = %s;'
    query_change_password = 'UPDATE public.\"Users\" SET password = %s WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        _, hashed_password = result
        if validate_user_password(bytes(hashed_password), old_password) and user_password_is_valid(new_password) and not old_password == new_password:
            cursor.execute(query_change_password,
                           (encrypt_password(new_password), email))
            conn.commit()
            return True
        return False
    except Exception as e:
        print("Failed to change password")
        print(e)


def fetch_user_data_from_email(conn, cursor, email: str):
    query = 'SELECT "id", "firstName", "lastName" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        id, first_name, last_name = result
        return f"{first_name} {last_name}", id
    except Exception as e:
        print("Failed to fetch user")
        print(e)


def user_reset_password(conn, cursor, email: str, new_password: str) -> bool:
    query_change_password = 'UPDATE public.\"Users\" SET password = %s WHERE email = %s;'
    try:
        cursor.execute(query_change_password,
                       (encrypt_password(new_password), email,))
        conn.commit()
        return True
    except Exception as e:
        print("Failed to reset password")
        print(e)


def user_delete_account(conn, cursor, email: str) -> bool:
    query = 'DELETE FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        conn.commit()
        return True
    except Exception as e:
        print("Failed to delete account")
        print(e)


def user_follow_account(conn, cursor, user_id: str, following_id: str) -> bool:
    print(f"user {user_id} wants to follow user {following_id}")
    query = 'INSERT INTO public.\"Followers\" ("user_id", "following_id") VALUES (%s, %s);'
    try:
        cursor.execute(query, (user_id, following_id))
        conn.commit()
        return True
    except Exception as e:
        print("Failed to insert into table")
        print(e)


def user_get_followed_accounts(conn, cursor, user_id: str):
    print(f"get followed accounts for user {user_id}")
    query = 'SELECT "firstName", "lastName", public."Users".id FROM public."Users" INNER JOIN public."Followers" ON public."Users".id = public."Followers".following_id WHERE public."Followers".user_id = %s;'
    try:
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        print(result)
        dict_result = [{'id': r[2], 'firstName': r[0],
                        'lastName': r[1]} for r in result]
        return dict_result
    except Exception as e:
        print("Failed to fetch accounts")
        print(e)


def user_get_account_followers(conn, cursor, user_id: str):
    print(f"get account followers for user {user_id}")
    query = 'SELECT "firstName", "lastName", public."Users".id FROM public."Users" INNER JOIN public."Followers" ON public."Users".id = public."Followers".user_id WHERE public."Followers".following_id = %s;'
    try:
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        print(result)
        dict_result = [{'id': r[2], 'firstName': r[0],
                        'lastName': r[1]} for r in result]
        return dict_result
    except Exception as e:
        print("Failed to fetch accounts")
        print(e)


def user_create_question(conn, cursor, user_id, title, description):
    query = 'INSERT INTO public."Questions" ("user_id", "title", "description") VALUES (%s, %s, %s);'
    try:
        cursor.execute(query, (user_id, title, description))
        conn.commit()
        return True
    except Exception as e:
        print("Failed to insert into table")
        print(e)


def get_questions_for_user(conn, cursor, user_id):
    query = 'SELECT "title", "description", "id" FROM public."Questions" WHERE user_id = %s;'
    try:
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        print(result)
        dict_result = [{'id': r[2], 'title': r[0],
                        'description': r[1]} for r in result]
        return dict_result
    except Exception as e:
        print("Failed to fetch questions")
        print(e)


def close_db(conn):
    conn.close()
