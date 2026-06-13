"""Markdown 切割器：支持通用模式和父子模式"""
import re
import hashlib
from langchain_core.documents import Document
from config.settings import settings
from config.logger import logger


class MarkdownSplitter:
    """Markdown 切割器"""

    def split(self, document: Document) -> list[Document]:
        """
        根据配置选择切割模式。
        @param document: 原始文档
        @return: 切割后的 Document 列表
        """
        # 一、计算文档哈希
        doc_hash = hashlib.md5(document.page_content.encode()).hexdigest()

        # 二、根据配置选择切割模式
        if settings.rag_chunk_mode == "parent_child":
            return self.split_parent_child(document, doc_hash)
        return self.split_general(document, doc_hash)

    def split_general(self, document: Document, doc_hash: str) -> list[Document]:
        """
        通用模式：单层切割。
        @param document: 原始文档
        @param doc_hash: 文档哈希
        @return: 切割后的 Document 列表
        """
        content = document.page_content
        metadata = document.metadata.copy()

        # 一、按标题分割
        sections = self.split_by_headers(content)

        # 二、合并过小的块
        chunks = self.merge_small_chunks(sections, settings.rag_chunk_size)

        # 三、拆分过大的块
        chunks = self.split_large_chunks(chunks, settings.rag_chunk_size)

        # 四、构建 Document 列表
        documents = []
        for i, (title, chunk_content) in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["doc_hash"] = doc_hash
            chunk_metadata["section_title"] = title
            chunk_metadata["chunk_index"] = i
            chunk_metadata["chunk_type"] = "general"
            documents.append(Document(page_content=chunk_content, metadata=chunk_metadata))

        return documents

    def split_parent_child(self, document: Document, doc_hash: str) -> list[Document]:
        """
        父子模式：双层切割，子块用于检索，父块用于上下文。
        @param document: 原始文档
        @param doc_hash: 文档哈希
        @return: 子块 Document 列表（metadata 中包含 parent_content）
        """
        content = document.page_content
        metadata = document.metadata.copy()

        # 一、按标题切父块
        parent_sections = self.split_by_headers(content)

        # 二、合并过小的父块
        parent_sections = self.merge_small_chunks(parent_sections, settings.rag_parent_max_size)

        # 三、对每个父块切子块
        documents = []
        for parent_index, (title, parent_content) in enumerate(parent_sections):
            # 1、父块内容超过限制时拆分
            parent_chunks = self.split_large_chunks(
                [(title, parent_content)],
                settings.rag_parent_max_size
            )

            # 2、对每个父块切子块
            for _, pc_content in parent_chunks:
                child_sections = self._split_to_child_chunks(pc_content)

                for child_index, child_content in enumerate(child_sections):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["doc_hash"] = doc_hash
                    chunk_metadata["section_title"] = title
                    chunk_metadata["parent_index"] = parent_index
                    chunk_metadata["chunk_index"] = child_index
                    chunk_metadata["chunk_type"] = "child"
                    # 父块内容存入 metadata，检索时返回
                    chunk_metadata["parent_content"] = pc_content
                    documents.append(Document(page_content=child_content, metadata=chunk_metadata))

        logger.info(f"父子模式切割: {len(parent_sections)} 个父块, {len(documents)} 个子块")
        return documents

    def _split_to_child_chunks(self, content: str) -> list[str]:
        """
        将父块内容切为子块。
        @param content: 父块内容
        @return: 子块内容列表
        """
        # 一、按分隔符切
        delimiter = settings.rag_child_delimiter
        parts = content.split(delimiter)

        # 二、合并过小的子块
        chunks = []
        current = ""
        for part in parts:
            if not part.strip():
                continue
            if len(current) + len(part) + len(delimiter) <= settings.rag_child_max_size:
                current += (delimiter if current else "") + part
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)

        return chunks if chunks else [content]

    def split_by_headers(self, content: str) -> list[tuple[str, str]]:
        """
        按标题分割内容。
        @param content: 原始内容
        @return: (标题, 内容) 列表
        """
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        sections = []
        last_pos = 0
        current_title = "文档开头"

        for match in header_pattern.finditer(content):
            if match.start() > last_pos:
                section_content = content[last_pos:match.start()].strip()
                if section_content:
                    sections.append((current_title, section_content))
            current_title = match.group(2).strip()
            last_pos = match.end()

        if last_pos < len(content):
            section_content = content[last_pos:].strip()
            if section_content:
                sections.append((current_title, section_content))

        return sections

    def merge_small_chunks(self, sections: list[tuple[str, str]], min_size: int) -> list[tuple[str, str]]:
        """
        合并过小的块。
        @param sections: (标题, 内容) 列表
        @param min_size: 最小块大小
        @return: 合并后的列表
        """
        if not sections:
            return []

        merged = []
        current_title, current_content = sections[0]

        for title, content in sections[1:]:
            if len(current_content) < min_size:
                current_content += "\n\n" + content
            else:
                merged.append((current_title, current_content))
                current_title, current_content = title, content

        if current_content:
            merged.append((current_title, current_content))

        return merged

    def split_large_chunks(self, chunks: list[tuple[str, str]], max_size: int) -> list[tuple[str, str]]:
        """
        拆分过大的块。
        @param chunks: (标题, 内容) 列表
        @param max_size: 最大块大小
        @return: 拆分后的列表
        """
        result = []

        for title, content in chunks:
            if len(content) <= max_size:
                result.append((title, content))
            else:
                paragraphs = content.split("\n\n")
                current_chunk = ""

                for para in paragraphs:
                    if len(current_chunk) + len(para) + 2 <= max_size:
                        current_chunk += ("\n\n" if current_chunk else "") + para
                    else:
                        if current_chunk:
                            result.append((title, current_chunk))
                        current_chunk = para

                if current_chunk:
                    result.append((title, current_chunk))

        return result


# 模块级单例
markdown_splitter = MarkdownSplitter()
