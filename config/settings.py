from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置：自动从 .env 文件加载，大小写兼容"""

    # env_ignore_empty=True 防止空值覆盖默认值
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    # Java 服务地址
    java_url: str
    # 数据库连接
    mysql_user: str
    mysql_password: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_pool_size: int = 10
    mysql_pool_recycle: int = 3600
    mysql_pool_timeout: int = 30
    mysql_max_overflow: int = 20
    # LLM 配置
    llm_model: str
    llm_api_key: str
    llm_base_url: str
    # 短期记忆存储方式：sqlite / postgres / async_sqlite
    checkpointer_model: str
    sqlite_url: str
    pg_url: str


settings = Settings()
