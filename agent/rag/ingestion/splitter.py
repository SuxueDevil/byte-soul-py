"""文档分块：递归字符分割，支持自定义分块策略"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.settings import settings


class DocumentSplitter:
    """文档分块器：将长文档切分为适合 embedding 的小块"""

    def __init__(
        self,
        chunk_size: int = 0,
        chunk_overlap: int = 0,
        separators: list[str] | None = None,
    ):
        """
        初始化分块器。
        @param chunk_size: 分块大小（字符数）
        @param chunk_overlap: 分块重叠字符数
        @param separators: 分隔符列表
        """
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def split(self, documents: list[Document]) -> list[Document]:
        """
        将文档列表分块。
        @param documents: Document 列表
        @return: 分块后的 Document 列表
        """
        return self._splitter.split_documents(documents)

    def split_text(self, text: str) -> list[str]:
        """
        将文本分块。
        @param text: 原始文本
        @return: 分块后的文本列表
        """
        return self._splitter.split_text(text)


# 模块级单例
splitter = DocumentSplitter()
