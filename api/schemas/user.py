from typing import Optional
from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    """创建/更新用户的请求体"""
    id: Optional[int] = Field(None)
    name: str = Field()
    email: str = Field()
    age: int = Field()


class UserVO(BaseModel):
    """用户信息响应体"""
    name: Optional[str] = Field(None, description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    age: Optional[int] = Field(None, description="年龄")
