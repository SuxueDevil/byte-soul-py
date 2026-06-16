"""用户服务层：封装用户相关的业务逻辑与数据库操作"""
from config.database import Database, mysqlTemplate
from api.schemas.user import UserDTO, UserVO
from api.models.user import User


class UserService:
    """用户服务层：封装用户相关的业务逻辑与数据库操作"""

    def __init__(self, database: Database) -> None:
        self.database = database

    async def get_user(self, user_id: int) -> UserVO:
        """
        根据用户 ID 查询用户信息。
        @param user_id: 用户主键 ID
        @return: UserVO 响应对象
        """
        return UserVO(
            name="张三",
            email="zhangsan@example.com",
            age=30
        )

    async def create_user(self, dto: UserDTO) -> bool:
        """
        创建新用户。
        @param dto: UserDTO，包含 name、email、age
        @return: True 表示创建成功
        """
        # 一、写入数据库
        # 1、构建 ORM 对象
        async with self.database.session() as db:
            user = User(name=dto.name, email=dto.email, age=dto.age)
            db.add(user)
            await db.commit()
            # 2、refresh 获取数据库生成的 id 等字段
            await db.refresh(user)
            return True


userService = UserService(mysqlTemplate)