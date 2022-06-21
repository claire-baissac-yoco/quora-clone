import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
import os
import re
import redis
import yagmail
import random


def encrypt_password(password: str) -> bytes:
    byte_password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(byte_password, salt)
    return hash


def generate_token(id: str, first_name: str, last_name: str, email: str) -> str:
    payload_data = {
        "id": id,
        "name": f"{first_name} {last_name}",
        "email": email
    }
    private_key = os.environ.get("PRIVATE_KEY")
    password = os.environ.get("KEY_PASSWORD")
    key = serialization.load_ssh_private_key(
        private_key.encode(), password=password.encode('utf-8'))
    token = jwt.encode(payload=payload_data, key=key, algorithm='RS256')
    return token


def decode_token(token: str):
    public_key = os.environ.get("PUBLIC_KEY")
    key = serialization.load_ssh_public_key(public_key.encode())
    payload = jwt.decode(jwt=token, key=key, algorithms=['RS256'])
    return payload


def user_password_is_valid(password: str) -> bool:
    return len(password) >= 8


def user_email_is_valid(email: str) -> bool:
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return re.search(regex, email)


def validate_user_info(email: str, password: str) -> bool:
    return user_email_is_valid(email) and user_password_is_valid(password)


def validate_user_password(actual_password_hashed, provided_password: str):
    return bcrypt.checkpw(provided_password.encode('utf-8'), actual_password_hashed)


def gen_redis_code(user_id):
    redis_host = os.environ.get("REDIS_HOST")
    redis_port = os.environ.get("REDIS_PORT")
    redis_password = os.environ.get("REDIS_PASSWORD")
    r = redis.Redis(
        host=redis_host, port=redis_port, password=redis_password)
    nums = random.sample(range(0, 10), 5)
    code = "".join([str(num) for num in nums])
    key_name = f"password-reset-token-{user_id}"
    r.set(name=key_name, value=code)
    r.expire(key_name, 10*60)
    return code


def send_reset_password_email(user_email, user_name, user_id):
    code = gen_redis_code(user_id)
    password = os.environ.get("EMAIL_PASSWORD")
    sender_email = os.environ.get("EMAIL_ADDRESS")
    yag = yagmail.SMTP(sender_email, password)
    contents = [f'Hi there, {user_name}! Here is the 5-digit code to reset your password: {code} :)',
                'If you have not requested to reset your password :( oh no']
    yag.send(to=user_email, subject='Reset your password', contents=contents)
