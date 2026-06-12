"""文档加载器：支持 PDF、Markdown、TXT 格式"""
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)


class DocumentLoader:
    """统一文档加载器：根据文件扩展名自动选择加载方式"""

    # 支持的文件格式及对应加载器
    LOADER_MAP = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".md": UnstructuredMarkdownLoader,
    }

    @classmethod
    def load(cls, file_path: str) -> list[Document]:
        """
        加载单个文档。
        @param file_path: 文件路径
        @return: Document 列表
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        loader_cls = cls.LOADER_MAP.get(suffix)
        if not loader_cls:
            raise ValueError(f"不支持的文件格式: {suffix}")

        loader = loader_cls(str(path))
        return loader.load()

    @classmethod
    def load_directory(cls, dir_path: str, glob_pattern: str = "**/*.*") -> list[Document]:
        """
        加载目录下所有文档。
        @param dir_path: 目录路径
        @param glob_pattern: 文件匹配模式
        @return: Document 列表
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")

        documents = []
        for file_path in path.glob(glob_pattern):
            if file_path.suffix.lower() in cls.LOADER_MAP:
                try:
                    documents.extend(cls.load(str(file_path)))
                except Exception as e:
                    print(f"加载失败 {file_path}: {e}")

        return documents
