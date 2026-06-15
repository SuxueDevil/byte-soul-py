"""RAG 管道：串联全部核心步骤"""
from dataclasses import dataclass
from functools import lru_cache
from config.logger import logger

from agent.rag.pre.query_rewriter import QueryRewriter
from agent.rag.pre.query_expansion import QueryExpander
from agent.rag.ingestion.loader import Loader
from agent.rag.ingestion.spliter import Spilter
from agent.rag.ingestion.saver import Saver


@dataclass
class RAGDependencies:
    """RAG 管道依赖"""
    query_rewriter: QueryRewriter
    query_expander: QueryExpander


class RAGPipeline:
    """RAG 管道：离线入库 + 在线检索"""

    def __init__(self, deps: RAGDependencies):
        self.deps = deps

    def ingest(self, content: str, file_name: str) -> int:
        """离线入库流程

        Args:
            content: 文件路径
            file_name: 文件名

        Returns:
            入库的 chunk 数量
        """
        logger.info(f"[RagPipeline] 开始入库: {file_name}")

        # 一、根据文件类型 加载、切割、入库
        # 1、match 匹配文件类型
        match file_name:
            # 2、对应 Loader / Spilter / Saver 串联执行
            case "markdown" | "md":
                count = Saver.markdown(Spilter.markdown(Loader.markdown(content)))
            case "pdf":
                count = Saver.pdf(Spilter.pdf(Loader.pdf(content)))
            case "word" | "docx":
                count = Saver.word(Spilter.word(Loader.word(content)))
            case _:
                logger.warning(f"[RagPipeline] 不支持的文件类型: {file_name}")
                return 0

        logger.info(f"[RagPipeline] 入库完成: {file_name} → {count} 个 chunk")
        return count

    def query(self, question: str) -> str:
        """在线检索流程

        Args:
            question: 用户问题

        Returns:
            回答文本
        """
        logger.info(f"[RagPipeline] 开始检索: {question}")

        # 一、检索前：查询优化
        rewritten = self.deps.query_rewriter.rewrite(question)
        queries = self.deps.query_expander.expand(rewritten)
        logger.info(f"[RagPipeline] 检索前完成")

        # 二、检索中：多路检索
        vector_docs = vector_retriever.search(queries)
        bm25_docs = bm25_retriever.search(queries)
        logger.info(
            f"[RagPipeline] 检索中完成: 向量 {len(vector_docs)} 条, BM25 {len(bm25_docs)} 条")

        # 三、检索后：融合与重排序
        fused = rrf_fuser.fuse(vector_docs, bm25_docs)
        # ？
        fused = self.replace_with_parent_context(fused)
        results = reranker.rerank(question, fused)
        logger.info(f"[RagPipeline] 检索后完成: {len(results)} 条结果")

        # 四、生成回答
        answer = self.generate(question, results)
        logger.info("[RagPipeline] 回答生成完成")
        return answer

    def replace_with_parent_context(self, docs: list[dict]) -> list[dict]:
        """父子模式：用父块内容替换子块内容

        Args:
            docs: 子块检索结果

        Returns:
            父块内容列表
        """
        seen = set()
        unique_docs = []
        for doc in docs:
            parent_index = doc.get("metadata", {}).get("parent_index")
            if parent_index is not None and parent_index not in seen:
                seen.add(parent_index)
                parent_content = doc.get(
                    "metadata", {}).get("parent_content", "")
                if parent_content:
                    doc["content"] = parent_content
                unique_docs.append(doc)
        return unique_docs


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """懒构建 RAG 管道单例（首次调用时执行,之后永久复用）"""
    deps = RAGDependencies(
        query_rewriter=QueryRewriter(),
        query_expander=QueryExpander(),
    )
    return RAGPipeline(deps)
