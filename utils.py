import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
import os
import re
import redis
import yagmail
import random

load_dotenv()


def encrypt_password(password: str):
    byte_password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(byte_password, salt)
    return hash


def generate_token(id, first_name, last_name, email):
    payload_data = {
        "id": id,
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


def gen_redis_code(user_id):
    r = redis.Redis()
    nums = random.sample(range(0, 10), 5)
    code = "".join([str(num) for num in nums])
    print(code)
    key_name = f"password-reset-token-{user_id}"
    r.set(name=key_name, value=code)
    r.expire(key_name, 10*60)
    print(r.get(key_name).decode('utf-8'))
    return code


def send_reset_password_email(user_email, user_name, user_id):
    code = gen_redis_code(user_id)
    password = os.getenv("EMAIL_PASSWORD")
    sender_email = os.getenv("EMAIL_ADDRESS")
    yag = yagmail.SMTP(sender_email, password)
    contents = [f'Hi there, {user_name}! Here is the 5-digit code to reset your password: {code} :)',
                'If you have not requested to reset your password :( oh no']
    print(contents)
    yag.send(to=user_email, subject='Reset your password', contents=contents)
