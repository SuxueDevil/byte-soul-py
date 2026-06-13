"""用户控制器：用户管理接口"""
from fastapi import APIRouter, Depends

from api.schemas.response import Response
from api.schemas.user import UserDTO, UserVO
from api.service.user_service import UserService, get_user_service

user_router = APIRouter(prefix="/users", tags=["用户管理"])


@user_router.get("/{user_id}")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    根据用户 ID 查询。
    @param user_id: 用户主键 ID
    @param user_service: 用户服务（依赖注入）
    @return: 统一响应包装的 UserVO
    """
    user_vo: UserVO = await user_service.get_user(user_id)
    return Response.success(user_vo)


@user_router.post("")
async def create_user(
    user_dto: UserDTO,
    user_service: UserService = Depends(get_user_service),
):
    """
    创建新用户。
    @param user_dto: UserDTO，需包含 name、email、age
    @param user_service: 用户服务（依赖注入）
    @return: 统一响应包装
    """
    res = await user_service.create_user(user_dto)
    return Response.success(res)
