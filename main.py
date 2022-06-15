import json
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn
from models import CreateUser, User
from database import connect_db, insert_user, validate_user_change_password, validate_user_login
import utils

load_dotenv()
PORT = int(os.getenv('PORT'))

conn, cursor = connect_db()


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


app = FastAPI()


def verify_jwt_token(req: Request):
    token = req.headers['Authorization'].split(" ")[1]
    print(token)
    decoded_token = utils.decode_token(token)
    return True, decoded_token['email']


@app.get('/')
def get_root():
    return {'success': True, 'message': 'success'}


@app.post('/', status_code=201)
def post_root():
    return {'success': True, 'message': 'success'}


@app.post('/auth/register', status_code=201)
def create_user(user: CreateUser):
    print(user)
    print(user.first_name, user.last_name, user.email, user.password)
    if not utils.validate_user_info(user.email, user.password):
        return JSONResponse(status_code=400, content={
            "success": False, "error": "Invalid user input"})
    try:
        token = utils.generate_token(
            user.first_name, user.last_name, user.email)
        # payload = utils.decode_token(token)
        insert_user(conn, cursor, user.first_name,
                    user.last_name, user.email, user.password)
        return {'success': True, 'message': 'success', 'data': token}
    except:
        return JSONResponse(status_code=404, content={
            "success": False, "error": "Failed to create user"})


@app.post('/auth/login')
def login_user(user: User):
    print(user)
    is_validated, user_info = validate_user_login(
        conn, cursor, user.email, user.password)
    if is_validated:
        token = utils.generate_token(
            user_info["first_name"], user_info["last_name"], user.email)
        return {'success': True, 'message': 'success', 'data': token}
    else:
        return JSONResponse(status_code=400, content={
            "success": False, "error": "Incorrect email or password"})


@app.post('/auth/password')
async def change_password_user(req: Request):
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    authorized, email = verify_jwt_token(req)
    if authorized:
        request_body = await req.body()
        body_json = json.loads(request_body.decode('utf-8'))
        old_password = body_json['old_password']
        new_password = body_json['new_password']
        print(old_password, new_password)
        if validate_user_change_password(conn, cursor, email, old_password, new_password):
            return {'success': True, 'message': 'success'}
        else:
            return JSONResponse(status_code=400, content={"success": False, "error": "Failed to change password"})
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})


@app.exception_handler(404)
async def custom_http_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
