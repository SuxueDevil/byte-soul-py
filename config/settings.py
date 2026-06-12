import os
from pathlib import Path
import yaml


class Settings:
    """全局配置：从 config.yaml 加载，支持 CONFIG_FILE 环境变量指定路径"""

    def __init__(self):
        config_file = os.environ.get("CONFIG_FILE", "config.yaml")
        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path.resolve()}，请复制 config.yaml.example 为 config.yaml")
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        # 一、Java 服务
        self.java_url: str = cfg["java"]["url"]

        # 二、MySQL
        mysql = cfg["mysql"]
        self.mysql_user: str = mysql["user"]
        self.mysql_password: str = mysql["password"]
        self.mysql_host: str = mysql["host"]
        self.mysql_port: int = mysql["port"]
        self.mysql_database: str = mysql["database"]
        pool = mysql.get("pool", {})
        self.mysql_pool_size: int = pool.get("size", 10)
        self.mysql_pool_recycle: int = pool.get("recycle", 3600)
        self.mysql_pool_timeout: int = pool.get("timeout", 30)
        self.mysql_max_overflow: int = pool.get("max_overflow", 20)

        # 三、LLM
        llm = cfg["llm"]
        self.llm_model: str = llm["model"]
        self.llm_api_key: str = llm["api_key"]
        self.llm_base_url: str = llm["base_url"]

        # 四、Checkpointer
        cp = cfg["checkpointer"]
        self.checkpointer_model: str = cp["model"]
        self.sqlite_url: str = cp.get("sqlite_url", "data/agent.db")
        self.pg_url: str = cp.get("pg_url", "")


settings = Settings()
