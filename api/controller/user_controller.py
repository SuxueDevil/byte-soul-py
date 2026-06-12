from fastapi import APIRouter

from api.schemas.response import Response
from api.schemas.user import UserDTO,UserVO
from api.service.user_service import UserService

user_router = APIRouter(prefix="/users", tags=["用户管理"])


@user_router.get("/{user_id}")
async def get_user(user_id: int):
    """
    根据用户 ID 查询。
    @param user_id: 用户主键 ID
    @return: 统一响应包装的 UserVO
    """
    user_vo = await UserService.get_user(user_id)
    return Response.success(user_vo)


@user_router.post("")
async def create_user(user_dto: UserDTO):
    """
    创建新用户。
    @param user_dto: UserDTO，需包含 name、email、age
    @return: 统一响应包装
    """
    res = await UserService.create_user(user_dto)
    return Response.success(res)
