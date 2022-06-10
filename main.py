from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()
PORT = int(os.getenv('PORT'))


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


@app.exception_handler(404)
async def custom_http_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
