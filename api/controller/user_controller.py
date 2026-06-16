"""用户控制器：用户管理接口"""
from fastapi import APIRouter

from api.schemas.response import Response
from api.schemas.user import UserDTO, UserVO
from api.service.user_service import userService

user_router = APIRouter(prefix="/users", tags=["用户管理"])


@user_router.get("/{user_id}")
async def get_user(user_id: int):
    """
    根据用户 ID 查询。
    @param user_id: 用户主键 ID
    @return: 统一响应包装的 UserVO
    """
    return Response.success(await userService.get_user(user_id))


@user_router.post("")
async def create_user(user_dto: UserDTO):
    """
    创建新用户。
    @param user_dto: UserDTO，需包含 name、email、age
    @return: 统一响应包装
    """
    return Response.success(await userService.create_user(user_dto))