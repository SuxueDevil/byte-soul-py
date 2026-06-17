"""文档切割器：按文件类型选用合适的切割策略（父子模式）"""
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from config.settings import settings


class Spilter:
    """文档切割器：按文件类型选用不同的切割策略"""

    @staticmethod
    def markdown(documents: list[Document]) -> list[Document]:
        """切割 Markdown - 父块按 markdown 结构切，再切子块

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、用 MarkdownTextSplitter 按父块大小切分
        # 1、保留标题层级（# ## ###）作为父块边界
        parent_splitter = MarkdownTextSplitter(
            chunk_size=settings.rag_parent_max_size,
            chunk_overlap=0,
        )
        parents = parent_splitter.split_documents(documents)
        # 二、用 RecursiveCharacterTextSplitter 把父块细切成子块
        return Spilter._build_children(parents)

    @staticmethod
    def pdf(documents: list[Document]) -> list[Document]:
        """切割 PDF - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、PDF 无结构，用 RecursiveCharacterTextSplitter 按段落边界切
        return Spilter._recursive_parent_child(documents)

    @staticmethod
    def word(documents: list[Document]) -> list[Document]:
        """切割 Word - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、Word 段落结构简单，用 RecursiveCharacterTextSplitter 按段落边界切
        return Spilter._recursive_parent_child(documents)

    @staticmethod
    def _recursive_parent_child(documents: list[Document]) -> list[Document]:
        """通用递归切割：先切父块再切子块（PDF/Word 共用）

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、用 RecursiveCharacterTextSplitter 按 parent_max_size 切父块
        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_parent_max_size,
            chunk_overlap=0,
        )
        parents = parent_splitter.split_documents(documents)
        # 二、用 RecursiveCharacterTextSplitter 把父块细切成子块
        return Spilter._build_children(parents)

    @staticmethod
    def _build_children(parents: list[Document]) -> list[Document]:
        """子块构建：把父块细切成子块，注入父块元数据

        Args:
            parents: 父块 Document 列表

        Returns:
            子块 Document 列表
        """
        # 一、用 RecursiveCharacterTextSplitter 按 child_max_size 细切子块
        # 1、相邻子块保留 overlap 维持上下文
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_child_max_size,
            chunk_overlap=settings.rag_child_overlap,
        )
        children: list[Document] = []
        for parent_index, parent in enumerate(parents):
            # 二、构造父块元数据，注入到子块供检索时回溯
            parent_meta = parent.metadata.copy()
            parent_meta["parent_index"] = parent_index
            parent_meta["parent_content"] = parent.page_content
            for child in child_splitter.split_documents([parent]):
                # 三、把父块元数据合并到子块
                child.metadata = {**parent_meta, **child.metadata}
                children.append(child)
        return children
