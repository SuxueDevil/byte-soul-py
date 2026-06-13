"""Markdown 加载器：接收文件内容"""
from langchain_core.documents import Document
from config.logger import logger


class MarkdownLoader:
    """Markdown 文件加载器"""

    def load(self, content: str, file_name: str = "") -> list[Document]:
        """
        加载 Markdown 内容。
        @param content: 文件内容
        @param file_name: 文件名
        @return: Document 列表
        """
        if not content.strip():
            logger.warning(f"文件内容为空: {file_name}")
            return []

        metadata = {
            "file_name": file_name,
            "file_type": "md",
        }
        return [Document(page_content=content, metadata=metadata)]

    def load_local(self, file_path: str) -> list[Document]:
        """
        从本地文件加载。
        @param file_path: 文件路径
        @return: Document 列表
        """
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return self.load(content, file_path)


# 模块级单例
markdown_loader = MarkdownLoader()
