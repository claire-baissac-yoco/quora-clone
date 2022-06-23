from pydantic import BaseModel


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class User(BaseModel):
    email: str
    password: str


class ResetPassword(BaseModel):
    email: str


class ConfirmResetPassword(BaseModel):
    email: str
    password: str
    code: str
