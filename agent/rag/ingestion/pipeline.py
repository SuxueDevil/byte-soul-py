"""入库管道：串联加载、切割、入库"""
from pathlib import Path
from langchain_core.documents import Document
from config.logger import logger
from .markdown_loader import markdown_loader
from .markdown_splitter import markdown_splitter
from .ingestion_manager import ingestion_manager


class IngestionPipeline:
    """入库管道：串联 Markdown 加载、切割、入库"""

    def run(self, file_path: str) -> int:
        """
        执行入库流程。
        @param file_path: Markdown 文件路径
        @return: 入库的 chunk 数量
        """
        logger.info(f"开始入库: {file_path}")

        # 一、加载文档
        documents = markdown_loader.load(file_path)
        if not documents:
            logger.warning(f"加载失败: {file_path}")
            return 0

        logger.info(f"加载完成: {len(documents)} 个文档")

        # 二、切割文档
        chunks = []
        for doc in documents:
            chunks.extend(markdown_splitter.split(doc))

        logger.info(f"切割完成: {len(chunks)} 个 chunk")

        # 三、向量化（TODO: 接入 Embedding 模型）
        embeddings = [[0.0] * 1024 for _ in chunks]  # 临时占位

        # 四、入库
        count = ingestion_manager.ingest(chunks, embeddings)

        logger.info(f"入库完成: {count} 个 chunk")
        return count

    def run_directory(self, dir_path: str) -> int:
        """
        批量入库目录下的所有 Markdown 文件。
        @param dir_path: 目录路径
        @return: 入库的 chunk 总数
        """
        path = Path(dir_path)
        if not path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return 0

        total = 0
        for md_file in path.glob("**/*.md"):
            total += self.run(str(md_file))

        return total


# 模块级单例
ingestion_pipeline = IngestionPipeline()
