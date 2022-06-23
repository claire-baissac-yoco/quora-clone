from utils import encrypt_password, user_password_is_valid, validate_user_password
# from psycopg2 import connection, cursor


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


def fetch_user_data_from_email(conn, cursor, email: str) -> dict:
    query = 'SELECT "id", "firstName", "lastName" FROM public.\"Users\" WHERE email = %s;'
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        id, first_name, last_name = result
        return {"name": f"{first_name} {last_name}", "id": id}
    except Exception as e:
        print("Failed to fetch user")
        print(e)


def user_reset_password(conn, cursor, email: str, new_password: str) -> None:
    query_change_password = 'UPDATE public.\"Users\" SET password = %s WHERE email = %s;'
    try:
        cursor.execute(query_change_password, (email,))
        conn.commit()
    except Exception as e:
        print("Failed to reset password")
        print(e)


def close_db(conn):
    conn.close()
