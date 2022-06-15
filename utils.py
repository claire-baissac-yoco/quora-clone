import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
import os
import re

load_dotenv()


def encrypt_password(password: str):
    byte_password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(byte_password, salt)
    return hash


def generate_token(first_name, last_name, email):
    payload_data = {
        "name": f"{first_name} {last_name}",
        "email": email
    }
    private_key = open('.ssh/id_rsa', 'r').read()
    password = os.getenv("KEY_PASSWORD")
    key = serialization.load_ssh_private_key(
        private_key.encode(), password=password.encode('utf-8'))
    token = jwt.encode(payload=payload_data, key=key, algorithm='RS256')
    print(token)
    return token


def decode_token(token):
    public_key = open('.ssh/id_rsa.pub', 'r').read()
    key = serialization.load_ssh_public_key(public_key.encode())
    payload = jwt.decode(jwt=token, key=key, algorithms=['RS256'])
    print(payload)
    return payload


def user_password_is_valid(password):
    return len(password) >= 8


def user_email_is_valid(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return re.search(regex, email)


def validate_user_info(email, password):
    return user_email_is_valid(email) and user_password_is_valid(password)


def validate_user_password(actual_password_hashed, provided_password: str):
    print("actual password hashed vs provided password")
    print(actual_password_hashed, provided_password)
    return bcrypt.checkpw(provided_password.encode('utf-8'), actual_password_hashed)
