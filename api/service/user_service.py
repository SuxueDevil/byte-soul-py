"""用户服务层：封装用户相关的业务逻辑与数据库操作"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from config.database import Database, database
from api.schemas.user import UserDTO, UserVO
from api.models.user import User


@dataclass(frozen=True)
class UserServiceDependencies:
    """用户服务依赖"""
    database: Database


class UserService:
    """用户服务层：封装用户相关的业务逻辑与数据库操作"""

    def __init__(self, deps: UserServiceDependencies) -> None:
        self.deps = deps

    async def get_user(self, user_id: int) -> UserVO:
        """
        根据用户 ID 查询用户信息。
        @param user_id: 用户主键 ID
        @return: UserVO 响应对象
        """
        pass

    async def create_user(self, dto: UserDTO) -> bool:
        """
        创建新用户。
        @param dto: UserDTO，包含 name、email、age
        @return: True 表示创建成功
        """
        # 一、写入数据库
        # 1、构建 ORM 对象
        async with self.deps.database.session() as db:
            user = User(name=dto.name, email=dto.email, age=dto.age)
            db.add(user)
            await db.commit()
            # 2、refresh 获取数据库生成的 id 等字段
            await db.refresh(user)
            return True


@lru_cache(maxsize=1)
def _build_user_service() -> UserService:
    """构建用户服务单例"""
    deps = UserServiceDependencies(database=database)
    return UserService(deps)


UserServiceDep = Annotated[UserService, Depends(_build_user_service)]
