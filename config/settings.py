"""全局配置：从 config.yaml 加载，支持 CONFIG_FILE 环境变量指定路径"""
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import SecretStr


class Settings:
    """全局配置：扁平结构，字段名与 config.yaml 一一对齐"""

    def __init__(self):
        cfg = _read_yaml(_resolve_config_path())

        # ---- Java 服务 ----
        java = cfg.get("java", {})
        self.java_url: str = java.get("url", "http://localhost:8080/api")

        # ---- MySQL ----
        mysql = cfg.get("mysql", {})
        self.mysql_user: str = mysql.get("user", "root")
        self.mysql_password: str = mysql.get("password", "")
        self.mysql_host: str = mysql.get("host", "localhost")
        self.mysql_port: int = mysql.get("port", 3306)
        self.mysql_database: str = mysql.get("database", "")
        pool = mysql.get("pool", {})
        self.mysql_pool_size: int = pool.get("size", 10)
        self.mysql_pool_recycle: int = pool.get("recycle", 3600)
        self.mysql_pool_timeout: int = pool.get("timeout", 30)
        self.mysql_max_overflow: int = pool.get("max_overflow", 20)

        # ---- LLM ----
        llm = cfg.get("llm", {})
        self.llm_model: str = llm.get("model", "qwen-plus")
        self.llm_api_key: str = llm.get("api_key", "")
        self.llm_base_url: str = llm.get("base_url", "")

        # ---- Checkpointer ----
        cp = cfg.get("checkpointer", {})
        self.checkpointer_model: str = cp.get("model", "async_sqlite")
        self.sqlite_url: str = cp.get("sqlite_url", "data/agent.db")
        self.pg_url: str = cp.get("pg_url", "")

        # ---- RAG ----
        rag = cfg.get("rag", {})
        # PG RAG 文档库
        self.rag_pg_url: str = rag.get("pg_url", "")
        # Neo4j 知识图谱
        neo4j = rag.get("neo4j", {})
        self.neo4j_uri: str = neo4j.get("uri", "bolt://localhost:7687")
        self.neo4j_user: str = neo4j.get("user", "neo4j")
        self.neo4j_password: str = neo4j.get("password", "password")

        # 嵌入模型（默认复用 LLM 配置）
        embedding = rag.get("embedding", {})
        self.embedding_model: str = embedding.get("model", "text-embedding-v3")
        self.embedding_api_key: str = embedding.get("api_key", self.llm_api_key)
        self.embedding_base_url: str = embedding.get("base_url", self.llm_base_url)
        self.embedding_dimensions: int = embedding.get("dimensions", 1024)

        # Milvus 向量存储
        vectorstore = rag.get("vectorstore", {})
        self.milvus_host: str = vectorstore.get("milvus_host", "localhost")
        self.milvus_port: int = vectorstore.get("milvus_port", 19530)
        self.milvus_collection: str = vectorstore.get("collection_name", "bs_rag")

        # Elasticsearch BM25
        bm25 = rag.get("bm25", {})
        self.es_hosts: list[str] = bm25.get("es_hosts", ["http://localhost:9200"])
        self.es_index_name: str = bm25.get("index_name", "bs_rag")
        self.es_ik_analyzer: str = bm25.get("ik_analyzer", "ik_max_word")
        self.es_ik_search_analyzer: str = bm25.get("ik_search_analyzer", "ik_smart")

        # 检索配置
        retrieval = rag.get("retrieval", {})
        self.retrieval_top_k: int = retrieval.get("top_k", 5)
        self.retrieval_score_threshold: float = retrieval.get("score_threshold", 0.7)

        # 检索前
        pre = rag.get("pre_retrieval", {})
        self.rag_enable_rewrite: bool = pre.get("enable_rewrite", True)
        self.rag_enable_expansion: bool = pre.get("enable_expansion", True)
        self.rag_expansion_count: int = pre.get("expansion_count", 3)
        self.rag_enable_hyde: bool = pre.get("enable_hyde", False)

        # 检索中
        mid = rag.get("mid_retrieval", {})
        self.rag_enable_bm25: bool = mid.get("enable_bm25", True)
        self.rag_enable_compression: bool = mid.get("enable_compression", True)

        # 检索后
        post = rag.get("post_retrieval", {})
        self.rag_enable_reranker: bool = post.get("enable_reranker", True)
        self.reranker_model: str = post.get("reranker_model", "BAAI/bge-reranker-v2-m3")


def _read_yaml(path: str) -> dict[str, Any]:
    """读取 YAML 配置文件"""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise FileNotFoundError(f"配置文件读取失败: {path}, {e}")


def _resolve_config_path() -> str:
    """按优先级找 config.yaml：环境变量 > 项目根"""
    explicit = os.environ.get("CONFIG_FILE")
    if explicit:
        return explicit
    return "config.yaml"


settings = Settings()
