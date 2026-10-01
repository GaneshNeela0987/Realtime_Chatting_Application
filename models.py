from pydantic import BaseModel

class ChatModel(BaseModel):
    to: str
    message: str


class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str