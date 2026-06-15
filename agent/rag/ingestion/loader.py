"""文档加载器：按文件类型加载为 LangChain Document 列表"""
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)

from config.logger import logger


class Loader:
    """文档加载器：按文件类型加载为 LangChain Document 列表"""

    @staticmethod
    def markdown(file_path: str) -> list[Document]:
        """加载 Markdown 文件

        Args:
            file_path: Markdown 文件路径

        Returns:
            Document 列表；加载失败返回空列表
        """
        # 一、用 UnstructuredMarkdownLoader 解析 Markdown
        # 1、自动识别标题、段落、列表结构
        # 2、保留元素层级作为元数据
        try:
            return UnstructuredMarkdownLoader(file_path).load()
        except Exception as e:
            logger.error(f"Markdown 加载失败 [{file_path}]: {e}")
            return []

    @staticmethod
    def pdf(file_path: str) -> list[Document]:
        """加载 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            Document 列表（按页拆分）；加载失败返回空列表
        """
        # 一、用 PyPDFLoader 按页解析 PDF
        # 1、每页返回一个 Document，page 元数据自动注入
        try:
            return PyPDFLoader(file_path).load()
        except Exception as e:
            logger.error(f"PDF 加载失败 [{file_path}]: {e}")
            return []

    @staticmethod
    def word(file_path: str) -> list[Document]:
        """加载 Word 文件

        Args:
            file_path: Word 文件路径

        Returns:
            Document 列表（按段落拆分）；加载失败返回空列表
        """
        # 一、用 Docx2txtLoader 提取 Word 文本
        # 1、保留段落结构作为 Document
        try:
            return Docx2txtLoader(file_path).load()
        except Exception as e:
            logger.error(f"Word 加载失败 [{file_path}]: {e}")
            return []
