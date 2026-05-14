from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天接口请求体"""
    user_id: str = Field()
    message: str
