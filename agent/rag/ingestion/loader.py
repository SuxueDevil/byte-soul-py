"""文档加载器：按文件类型加载为 LangChain Document 列表

Document 是 LangChain 的数据容器，每个 Document 包含：
- page_content: 文本内容（str）
- metadata: 附加信息（dict），如 {"source": "文件名", "page": 页码}
"""
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)


class Loader:
    """文档加载器：按文件类型加载为 LangChain Document 列表"""

    @staticmethod
    def markdown(file_path: str) -> list[Document]:
        """加载 Markdown 文件

        Args:
            file_path: Markdown 文件路径

        Returns:
            Document 列表
        """
        # 一、用 UnstructuredMarkdownLoader 解析 Markdown
        return UnstructuredMarkdownLoader(file_path).load()

    @staticmethod
    def pdf(file_path: str) -> list[Document]:
        """加载 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            Document 列表（按页拆分）
        """
        # 一、用 PyPDFLoader 按页解析 PDF
        return PyPDFLoader(file_path).load()

    @staticmethod
    def word(file_path: str) -> list[Document]:
        """加载 Word 文件

        Args:
            file_path: Word 文件路径

        Returns:
            Document 列表（按段落拆分）
        """
        # 一、用 Docx2txtLoader 提取 Word 文段落结构
        return Docx2txtLoader(file_path).load()
