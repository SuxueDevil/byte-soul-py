"""文档原文存储：支持增量更新和文档管理"""
import json
import hashlib
from pathlib import Path
from langchain_core.documents import Document


class DocumentStore:
    """文档存储：管理文档原文，支持增量更新"""

    def __init__(self, store_path: str = "data/docstore.json"):
        """
        初始化文档存储。
        @param store_path: 存储文件路径
        """
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._docs: dict[str, dict] = {}
        self._load()

    def _load(self):
        """从文件加载文档"""
        if self.store_path.exists():
            with open(self.store_path, "r", encoding="utf-8") as f:
                self._docs = json.load(f)

    def _save(self):
        """保存文档到文件"""
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self._docs, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_doc_id(content: str, source: str = "") -> str:
        """
        生成文档唯一 ID。
        @param content: 文档内容
        @param source: 文档来源
        @return: 文档 ID
        """
        text = f"{source}:{content[:500]}"
        return hashlib.md5(text.encode()).hexdigest()

    def add(self, doc: Document) -> str:
        """
        添加文档。
        @param doc: Document 对象
        @return: 文档 ID
        """
        doc_id = self._get_doc_id(doc.page_content, doc.metadata.get("source", ""))
        self._docs[doc_id] = {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        self._save()
        return doc_id

    def add_many(self, docs: list[Document]) -> list[str]:
        """
        批量添加文档。
        @param docs: Document 列表
        @return: 文档 ID 列表
        """
        ids = []
        for doc in docs:
            doc_id = self._get_doc_id(doc.page_content, doc.metadata.get("source", ""))
            self._docs[doc_id] = {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            ids.append(doc_id)
        self._save()
        return ids

    def get(self, doc_id: str) -> Document | None:
        """
        获取文档。
        @param doc_id: 文档 ID
        @return: Document 对象或 None
        """
        if doc_id not in self._docs:
            return None
        doc_data = self._docs[doc_id]
        return Document(
            page_content=doc_data["content"],
            metadata=doc_data["metadata"],
        )

    def delete(self, doc_id: str) -> bool:
        """
        删除文档。
        @param doc_id: 文档 ID
        @return: 是否删除成功
        """
        if doc_id in self._docs:
            del self._docs[doc_id]
            self._save()
            return True
        return False

    def list_all(self) -> list[str]:
        """
        列出所有文档 ID。
        @return: 文档 ID 列表
        """
        return list(self._docs.keys())

    def count(self) -> int:
        """
        获取文档数量。
        @return: 文档数量
        """
        return len(self._docs)


# 模块级单例
docstore = DocumentStore()
