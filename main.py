import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import uvicorn
from models import ConfirmResetPassword, CreateUser, Question, ResetPassword, User
from database import fetch_user_data_from_email, get_questions_for_user, insert_user, user_create_question, user_delete_account, user_follow_account, user_get_account_followers, user_get_followed_accounts, user_reset_password, validate_user_change_password, validate_user_login
from db_script import connect_db, connect_redis
import utils

PORT = os.environ.get('PORT')
if PORT:
    PORT = int(PORT)
else:
    PORT = 8000
conn, cursor = connect_db()
r = connect_redis()


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


def verify_header(req: Request):
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    verify_token = verify_jwt_token(req)
    if verify_token:
        authorized, email, user_id, user_name = verify_token
        return authorized, email, user_id, user_name
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})


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
def reset_password_user(resetPassword: ResetPassword):
    user_name, user_id = fetch_user_data_from_email(
        conn, cursor, email=resetPassword.email)
    utils.send_reset_password_email(r, resetPassword.email, user_name, user_id)
    return {'success': True, 'message': 'A 5-digit code will be sent to your email inbox to reset your password.'}


@app.post('/auth/password-reset/confirm')
def reset_password_confirm_user(confirmResetPassword: ConfirmResetPassword):
    _, user_id = fetch_user_data_from_email(
        conn, cursor, email=confirmResetPassword.email)
    try:
        if utils.validate_redis_code(r, user_id, confirmResetPassword.code):
            if user_reset_password(
                    conn, cursor, confirmResetPassword.email, confirmResetPassword.password):
                return {'success': True, 'message': 'Password reset successfully'}
        return JSONResponse(status_code=401, content={"success": False, "error": "Failed to reset password"})
    except:
        return JSONResponse(status_code=401, content={"success": False, "error": "Failed to reset password"})


@app.post('/user/delete')
def delete_account_user(req: Request):
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    verify_token = verify_jwt_token(req)
    if verify_token:
        authorized, email, _, _ = verify_token
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})
    if authorized:
        try:
            if user_delete_account(conn, cursor, email):
                return {'success': True, 'message': 'Account deleted successfully'}
        except:
            return JSONResponse(status_code=401, content={"success": False, "error": "Failed to delete account"})


@app.get('/search/accounts')
def find_account(email: str, req: Request):
    print(f"find account: {email}")
    verif_header = verify_header(req)
    if isinstance(verif_header, JSONResponse):
        return verif_header
    try:
        user_name, user_id, _, _ = fetch_user_data_from_email(
            conn, cursor, email=email)
        print(user_name, user_id)
        return {'success': True, 'message': 'Successfully found user', 'data': {user_name, user_id}}
    except:
        return JSONResponse(status_code=401, content={"success": False, "error": "Failed to find user"})


@app.post('/accounts/follow')
def follow_account(following_id: str, req: Request):
    print(f"follow account: {id}")
    if 'Authorization' not in req.headers:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid header"})
    verify_token = verify_jwt_token(req)
    print(verify_token)
    if verify_token:
        authorized, _, user_id, _ = verify_token
    else:
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})
    if authorized:
        try:
            if not user_id == following_id and user_follow_account(conn, cursor, user_id, following_id):
                return {'success': True, 'message': 'Successfully followed user'}
        except:
            return JSONResponse(status_code=401, content={"success": False, "error": "Failed to follow user"})
    return JSONResponse(status_code=401, content={"success": False, "error": "Invalid authorization token"})


@app.post('/accounts/following')
def get_followed_accounts(req: Request):
    verif_header = verify_header(req)
    if isinstance(verif_header, JSONResponse):
        return verif_header
    authorized, _, user_id, _ = verif_header
    if authorized:
        try:
            followed_accounts = user_get_followed_accounts(
                conn, cursor, user_id)
            return {'success': True, 'message': 'Successfully retrieved followed accounts', 'data': followed_accounts}
        except:
            return JSONResponse(status_code=401, content={"success": False, "error": "Failed to fetch followed accounts"})
    return JSONResponse(status_code=401, content={"success": False, "error": "Failed to fetch followed accounts"})


@app.post('/accounts/followers')
def get_account_followers(req: Request):
    verif_header = verify_header(req)
    if isinstance(verif_header, JSONResponse):
        return verif_header
    authorized, _, user_id, _ = verif_header
    if authorized:
        try:
            account_followers = user_get_account_followers(
                conn, cursor, user_id)
            return {'success': True, 'message': 'Successfully retrieved following accounts', 'data': account_followers}
        except:
            return JSONResponse(status_code=401, content={"success": False, "error": "Failed to fetch account followers"})
    return JSONResponse(status_code=401, content={"success": False, "error": "Failed to fetch account followers"})


@app.post('/questions')
def create_question(question: Question, req: Request):
    verif_header = verify_header(req)
    if isinstance(verif_header, JSONResponse):
        return verif_header
    authorized, _, user_id, _ = verif_header
    if authorized:
        if user_create_question(conn, cursor, user_id, question.title, question.description):
            return {'success': True, 'message': 'Successfully created question'}
    return JSONResponse(status_code=401, content={"success": False, "error": "Failed to create question"})


@app.get('/questions')
def fetch_questions(user_id: str, req: Request):
    verif_header = verify_header(req)
    if isinstance(verif_header, JSONResponse):
        return verif_header
    authorized, _, user_id, _ = verif_header
    if authorized:
        user_questions = get_questions_for_user(conn, cursor, user_id)
        return {'success': True, 'message': 'Successfully created question', 'data': user_questions}
    return JSONResponse(status_code=401, content={"success": False, "error": "Failed to create question"})


@app.exception_handler(404)
async def custom_http_exception_handler():
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
