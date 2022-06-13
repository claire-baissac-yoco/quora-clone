from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn
from models import User
from database import connect_db, insert_user
import utils

load_dotenv()
PORT = int(os.getenv('PORT'))

conn, cursor = connect_db()


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


app = FastAPI()


@app.get('/')
def get_root():
    return {'success': True, 'message': 'success'}


@app.post('/', status_code=201)
def post_root():
    return {'success': True, 'message': 'success'}


@app.post('/auth/register', status_code=201)
def create_user(user: User):
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


@app.exception_handler(404)
async def custom_http_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
