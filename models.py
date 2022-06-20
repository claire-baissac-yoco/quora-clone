from fastapi import Query
from pydantic import BaseModel


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class User(BaseModel):
    email: str
    password: str

# class ChangePassword(BaseModel):
#     password: str
