from pydantic import BaseModel

class ChatModel(BaseModel):
    to: str
    message: str