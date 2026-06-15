"""文档切割器：按文件类型选用合适的切割策略"""
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from config.settings import settings
from agent.schemas.rag import ChunkMode


class Spilter:
    """文档切割器：按文件类型选用不同的切割策略"""

    @staticmethod
    def markdown(documents: list[Document]) -> list[Document]:
        """切割 Markdown - 按 Markdown 结构切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            切割后的 chunk 列表
        """
        # 一、Markdown 有明确结构，按 markdown 分隔符切分
        match ChunkMode(settings.rag_chunk_mode):
            # 1、通用模式：单层切分
            case ChunkMode.GENERAL:
                return Spilter._markdown_general_split(documents)
            # 2、父子模式：父块按 markdown 结构切，再切子块
            case ChunkMode.PARENT_CHILD:
                return Spilter._markdown_parent_child_split(documents)

    @staticmethod
    def pdf(documents: list[Document]) -> list[Document]:
        """切割 PDF - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            切割后的 chunk 列表
        """
        # 一、PDF 是无结构纯文本，用 RecursiveCharacterTextSplitter 按自然分隔符切分
        return Spilter._recursive_split(documents)

    @staticmethod
    def word(documents: list[Document]) -> list[Document]:
        """切割 Word - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            切割后的 chunk 列表
        """
        # 一、Word 段落结构简单，用 RecursiveCharacterTextSplitter 即可
        return Spilter._recursive_split(documents)

    @staticmethod
    def _markdown_general_split(documents: list[Document]) -> list[Document]:
        """Markdown 通用模式：按 Markdown 结构切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            切割后的 chunk 列表
        """
        # 一、用 MarkdownTextSplitter 优先按 markdown 分隔符切分
        # 1、保留标题、代码块、列表等语义结构
        # 2、相邻块保留 overlap 维持上下文
        splitter = MarkdownTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        return splitter.split_documents(documents)

    @staticmethod
    def _markdown_parent_child_split(documents: list[Document]) -> list[Document]:
        """Markdown 父子模式：父块按标题切，再切子块

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、用 MarkdownTextSplitter 按父块大小切分
        # 1、保留标题层级（# ## ###）作为父块边界
        # 2、用于检索时回溯上下文
        parent_splitter = MarkdownTextSplitter(
            chunk_size=settings.rag_parent_max_size,
            chunk_overlap=0,
        )
        parents = parent_splitter.split_documents(documents)
        # 二、再切子块
        return Spilter._build_children(parents)

    @staticmethod
    def _recursive_split(documents: list[Document]) -> list[Document]:
        """通用回溯切割（PDF/Word）：按自然分隔符递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            切割后的 chunk 列表
        """
        # 一、按配置选择切割模式
        match ChunkMode(settings.rag_chunk_mode):
            # 1、通用模式：单层切分
            case ChunkMode.GENERAL:
                # 一、用 RecursiveCharacterTextSplitter 按自然分隔符递归切分
                # 1、优先按段落、句子、字符边界切，保证语义完整
                # 2、相邻块保留 overlap 维持上下文
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.rag_chunk_size,
                    chunk_overlap=settings.rag_chunk_overlap,
                )
                return splitter.split_documents(documents)
            case ChunkMode.PARENT_CHILD:
                # 2、父子模式：先切父块再切子块
                # 一、先按 parent_max_size 切父块
                # 1、保留父块全文，用于检索时回溯上下文
                parent_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.rag_parent_max_size,
                    chunk_overlap=0,
                )
                parents = parent_splitter.split_documents(documents)
                # 二、再切子块
                return Spilter._build_children(parents)

    @staticmethod
    def _build_children(parents: list[Document]) -> list[Document]:
        """通用子块构建：把父块细切成子块，注入父块元数据

        Args:
            parents: 父块 Document 列表

        Returns:
            子块 Document 列表
        """
        # 一、用 RecursiveCharacterTextSplitter 细切
        # 1、相邻子块保留 overlap 维持上下文
        # 2、子块携带 parent_index，命中后可找回父块
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_child_max_size,
            chunk_overlap=settings.rag_child_overlap,
        )
        children: list[Document] = []
        for parent_index, parent in enumerate(parents):
            # 1、构造父块元数据，注入到子块供检索时回溯
            parent_meta = parent.metadata.copy()
            parent_meta["parent_index"] = parent_index
            parent_meta["parent_content"] = parent.page_content
            for child in child_splitter.split_documents([parent]):
                # 2、把父块元数据合并到子块
                child.metadata = {**parent_meta, **child.metadata}
                children.append(child)
        return children
