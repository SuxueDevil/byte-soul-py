"""Markdown 切割器：按标题层级切割"""
import re
from langchain_core.documents import Document


class MarkdownSplitter:
    """按 Markdown 标题层级切割文档"""

    def __init__(self, min_chunk_size: int = 50, max_chunk_size: int = 2000):
        """
        初始化切割器。
        @param min_chunk_size: 最小块大小（字符数）
        @param max_chunk_size: 最大块大小（字符数）
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def split(self, document: Document) -> list[Document]:
        """
        按标题层级切割 Markdown 文档。
        @param document: 原始文档
        @return: 切割后的 Document 列表
        """
        content = document.page_content
        metadata = document.metadata.copy()

        # 按标题分割
        sections = self._split_by_headers(content)

        # 合并过小的块
        chunks = self._merge_small_chunks(sections)

        # 拆分过大的块
        chunks = self._split_large_chunks(chunks)

        # 构建 Document 列表
        documents = []
        for i, (title, chunk_content) in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["section_title"] = title
            chunk_metadata["chunk_index"] = i
            documents.append(Document(page_content=chunk_content, metadata=chunk_metadata))

        return documents

    def _split_by_headers(self, content: str) -> list[tuple[str, str]]:
        """
        按标题分割内容。
        @param content: 原始内容
        @return: (标题, 内容) 列表
        """
        # 匹配 Markdown 标题（# ## ### 等）
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        sections = []
        last_pos = 0
        current_title = "文档开头"

        for match in header_pattern.finditer(content):
            # 保存上一个标题的内容
            if match.start() > last_pos:
                section_content = content[last_pos:match.start()].strip()
                if section_content:
                    sections.append((current_title, section_content))

            # 更新当前标题
            current_title = match.group(2).strip()
            last_pos = match.end()

        # 保存最后一个标题的内容
        if last_pos < len(content):
            section_content = content[last_pos:].strip()
            if section_content:
                sections.append((current_title, section_content))

        return sections

    def _merge_small_chunks(self, sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """
        合并过小的块。
        @param sections: (标题, 内容) 列表
        @return: 合并后的列表
        """
        if not sections:
            return []

        merged = []
        current_title, current_content = sections[0]

        for title, content in sections[1:]:
            # 如果当前块太小，合并到下一个块
            if len(current_content) < self.min_chunk_size:
                current_content += "\n\n" + content
                current_title = current_title  # 保留第一个标题
            else:
                merged.append((current_title, current_content))
                current_title, current_content = title, content

        # 保存最后一个块
        if current_content:
            merged.append((current_title, current_content))

        return merged

    def _split_large_chunks(self, chunks: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """
        拆分过大的块。
        @param chunks: (标题, 内容) 列表
        @return: 拆分后的列表
        """
        result = []

        for title, content in chunks:
            if len(content) <= self.max_chunk_size:
                result.append((title, content))
            else:
                # 按段落拆分
                paragraphs = content.split("\n\n")
                current_chunk = ""

                for para in paragraphs:
                    if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
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
