"""Markdown 加载器：读取 .md 文件"""
from pathlib import Path
from langchain_core.documents import Document


class MarkdownLoader:
    """Markdown 文件加载器"""

    def load(self, file_path: str) -> list[Document]:
        """
        加载单个 Markdown 文件。
        @param file_path: 文件路径
        @return: Document 列表
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = path.read_text(encoding="utf-8")
        metadata = {
            "file_name": path.name,
            "file_type": "md",
            "source": str(path),
        }
        return [Document(page_content=content, metadata=metadata)]

    def load_directory(self, dir_path: str) -> list[Document]:
        """
        加载目录下所有 Markdown 文件。
        @param dir_path: 目录路径
        @return: Document 列表
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")

        documents = []
        for md_file in path.glob("**/*.md"):
            try:
                documents.extend(self.load(str(md_file)))
            except Exception as e:
                print(f"加载失败 {md_file}: {e}")
        return documents


# 模块级单例
markdown_loader = MarkdownLoader()
