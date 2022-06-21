import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import uvicorn
from models import CreateUser, User
from database import insert_user, validate_user_change_password, validate_user_login
from db_script import connect_db
import utils

PORT = int(os.environ.get('PORT'))
conn, cursor = connect_db()


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


app = FastAPI()


def verify_jwt_token(req: Request):
    token = req.headers['Authorization'].split(" ")[1]
    try:
        decoded_token = utils.decode_token(token)
        return True, decoded_token['email'], decoded_token['id'], decoded_token["name"]
    except:
        return False


@app.get('/')
def get_root():
    return {'success': True, 'message': 'success'}


@app.post('/', status_code=201)
def post_root():
    return {'success': True, 'message': 'success'}


@app.post('/auth/register', status_code=201)
def create_user(user: CreateUser):
    if not utils.validate_user_info(user.email, user.password):
        return JSONResponse(status_code=400, content={
            "success": False, "error": "Invalid user input"})
    try:
        user_id = insert_user(conn, cursor, user.first_name,
                              user.last_name, user.email, user.password)
        token = utils.generate_token(
            user_id, user.first_name, user.last_name, user.email)
        return {'success': True, 'message': 'success', 'data': token}
    except:
        return JSONResponse(status_code=404, content={
            "success": False, "error": "Failed to create user"})


@app.post('/auth/login')
def login_user(user: User):
    try:
        is_validated, user_info = validate_user_login(
            conn, cursor, user.email, user.password)
        if is_validated:
            token = utils.generate_token(
                user_info["id"], user_info["first_name"], user_info["last_name"], user.email)
            return {'success': True, 'message': 'success', 'data': token}
        else:
            return JSONResponse(status_code=400, content={
                "success": False, "error": "Incorrect email or password"})
    except:
        return JSONResponse(status_code=400, content={
            "success": False, "error": "Incorrect email or password"})


@app.post('/auth/password')
async def change_password_user(req: Request):
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    verify_token = verify_jwt_token(req)
    if verify_token:
        authorized, email, _, _ = verify_token
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})
    if authorized:
        request_body = await req.body()
        body_json = json.loads(request_body.decode('utf-8'))
        old_password = body_json['old_password']
        new_password = body_json['new_password']
        if validate_user_change_password(conn, cursor, email, old_password, new_password):
            return {'success': True, 'message': 'success'}
        else:
            return JSONResponse(status_code=400, content={"success": False, "error": "Failed to change password"})
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})


@app.post('/auth/password-reset')
def forgot_password_user(req: Request):
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    authorized, email, user_id, user_name = verify_jwt_token(req)
    if authorized:
        utils.send_reset_password_email(email, user_name, user_id)
        return {'success': True, 'message': 'A 5-digit code will be sent to your email inbox to reset your password.'}
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})


@app.exception_handler(404)
async def custom_http_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
