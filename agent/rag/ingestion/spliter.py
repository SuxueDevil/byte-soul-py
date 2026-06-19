"""文档切割器：按文件类型选用合适的切割策略（父子模式）"""
import re

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from config.settings import settings


class Spilter:
    """文档切割器：按文件类型选用不同的切割策略"""

    # ─────────────────────────── Markdown ───────────────────────────
    @staticmethod
    def markdown(documents: list[Document]) -> list[Document]:
        """切割 Markdown - 父块按结构切，再切子块

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        # 一、父块切割：三级判断
        parents = Spilter.split_markdown_parents(documents)
        # 二、子块切割：分隔符优先，字数兜底
        return Spilter.build_children(parents)

    # ─────────────────────────── PDF ───────────────────────────
    @staticmethod
    def pdf(documents: list[Document]) -> list[Document]:
        """切割 PDF - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        return Spilter.recursive_parent_child(documents)

    # ─────────────────────────── Word ───────────────────────────
    @staticmethod
    def word(documents: list[Document]) -> list[Document]:
        """切割 Word - 按段落递归切分

        Args:
            documents: 待切割的 Document 列表

        Returns:
            子块 chunk 列表
        """
        return Spilter.recursive_parent_child(documents)

    # ─────────────────────────── 父块切割 ───────────────────────────
    @staticmethod
    def split_markdown_parents(documents: list[Document]) -> list[Document]:
        """Markdown 父块切割：三级判断

        1. 有标题 → MarkdownTextSplitter 按标题切
        2. 没标题 → 按分隔符切（\n\n > \n）
        3. 没切开 → 按字数强制切

        Args:
            documents: 待切割的 Document 列表

        Returns:
            父块 Document 列表（已去重）
        """
        # 一、检测有没有标题结构
        if Spilter.has_headers(documents):
            # 二、有标题：按标题切
            parents = MarkdownTextSplitter(
                chunk_size=settings.rag_parent_max_size,
                chunk_overlap=0,
            ).split_documents(documents)
        else:
            # 三、没标题：按分隔符切
            parents = Spilter.split_by_delimiter(documents, settings.rag_parent_max_size)

        # 四、检测有没有切开
        if len(parents) <= 1:
            # 五、没切开：按字数强制切
            parents = RecursiveCharacterTextSplitter(
                chunk_size=settings.rag_parent_max_size,
                chunk_overlap=0,
            ).split_documents(documents)

        # 六、去重
        seen = set()
        unique_parents = []
        for parent in parents:
            content_key = parent.page_content.strip()
            if content_key not in seen:
                seen.add(content_key)
                unique_parents.append(parent)
        return unique_parents

    @staticmethod
    def has_headers(documents: list[Document]) -> bool:
        """检测文档是否包含 Markdown 标题（# ## ###）

        Args:
            documents: Document 列表

        Returns:
            是否包含标题
        """
        for doc in documents:
            if re.search(r'^#{1,6}\s', doc.page_content, re.MULTILINE):
                return True
        return False

    @staticmethod
    def split_by_delimiter(documents: list[Document], max_size: int) -> list[Document]:
        """按分隔符切分（\n\n > \n），超长块按字数兜底

        Args:
            documents: 待切割的 Document 列表
            max_size: 最大块大小

        Returns:
            切割后的 Document 列表
        """
        # 一、按分隔符切段落
        segments = []
        for doc in documents:
            parts = doc.page_content.split("\n\n")
            if len(parts) == 1:
                parts = doc.page_content.split("\n")
            for part in parts:
                part = part.strip()
                if part:
                    segments.append(part)

        # 二、合并短块
        merged = []
        current = ""
        for seg in segments:
            if len(current) + len(seg) + 2 <= max_size:
                current = current + "\n\n" + seg if current else seg
            else:
                if current:
                    merged.append(current)
                current = seg
        if current:
            merged.append(current)

        # 三、超长块按字数兜底
        result = []
        for text in merged:
            if len(text) <= max_size:
                result.append(Document(page_content=text, metadata=documents[0].metadata.copy() if documents else {}))
            else:
                splitter = RecursiveCharacterTextSplitter(chunk_size=max_size, chunk_overlap=0)
                result.extend(splitter.split_documents([Document(page_content=text, metadata=documents[0].metadata.copy() if documents else {})]))

        return result

    @staticmethod
    def recursive_parent_child(documents: list[Document]) -> list[Document]:
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
        return Spilter.build_children(parents)

    # ─────────────────────────── 子块切割 ───────────────────────────
    @staticmethod
    def build_children(parents: list[Document]) -> list[Document]:
        """子块构建：把父块细切成子块，注入父块元数据

        Args:
            parents: 父块 Document 列表（已去重）

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
