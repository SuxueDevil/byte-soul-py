"""RAG 管道：串联全部核心步骤"""
from pathlib import Path
from dataclasses import dataclass
from langchain_core.documents import Document
from config.logger import logger
from .models import FileType
from .ingestion.markdown_loader import markdown_loader
from .ingestion.markdown_splitter import markdown_splitter
from .ingestion.doc_store import doc_store
from .pre_retrieval.query_rewriter import QueryRewriter
from .pre_retrieval.query_expansion import QueryExpander
from .mid_retrieval import vector_retriever, bm25_retriever, context_compressor
from .post_retrieval import rrf_fuser, reranker


@dataclass
class RAGDependencies:
    """RAG 管道依赖"""
    query_rewriter: QueryRewriter
    query_expander: QueryExpander


class RAGPipeline:
    """RAG 管道：离线入库 + 在线检索"""

    def __init__(self, deps: RAGDependencies):
        self.deps = deps

    def get_loader(self, file_name: str):
        """
        根据文件名扩展名匹配加载器。
        @param file_name: 文件名
        @return: 对应的加载器
        """
        suffix = Path(file_name).suffix.lower()
        try:
            file_type = FileType(suffix)
        except ValueError:
            raise ValueError(f"不支持的文件格式: {suffix}")

        # 一、Markdown 加载器
        if file_type == FileType.MD:
            return markdown_loader

        raise ValueError(f"未配置加载器: {file_type.value}")

    def ingest(self, content: str, file_name: str) -> int:
        """
        离线入库流程：直接接收文件内容。
        @param content: 文件内容
        @param file_name: 文件名
        @return: 入库的 chunk 数量
        """
        logger.info(f"开始入库: {file_name}")

        # 一、根据文件类型匹配加载器
        loader = self.get_loader(file_name)

        # 二、加载文档
        documents = loader.load(content, file_name)
        if not documents:
            logger.warning(f"加载失败: {file_name}")
            return 0
        logger.info(f"加载完成: {len(documents)} 个文档")

        # 三、切割文档
        chunks = []
        for doc in documents:
            chunks.extend(markdown_splitter.split(doc))
        logger.info(f"切割完成: {len(chunks)} 个 chunk")

        # 四、入库（原文 + 向量 + 关键词索引）
        count = doc_store.ingest(chunks)
        logger.info(f"入库完成: {count} 个 chunk")
        return count

    def query(self, question: str) -> str:
        """
        在线检索流程。
        @param question: 用户问题
        @return: 回答文本
        """
        logger.info(f"开始检索: {question}")

        # 一、检索前：查询优化
        # 1、查询改写：口语化 → 正式表述
        rewritten = self.deps.query_rewriter.rewrite(question)
        # 2、查询扩展：生成多个相关查询
        queries = self.deps.query_expander.expand(rewritten)
        logger.info(f"检索前完成: {len(queries)} 个查询")

        # 二、检索中：多路检索
        # 1、向量检索：Milvus 语义相似度（子块匹配）
        vector_docs = vector_retriever.search(queries)
        # 2、BM25 检索：Elasticsearch 关键词匹配（子块匹配）
        bm25_docs = bm25_retriever.search(queries)
        # 3、上下文压缩：提取相关片段
        vector_docs = context_compressor.compress(question, vector_docs)
        bm25_docs = context_compressor.compress(question, bm25_docs)
        logger.info(f"检索中完成: 向量 {len(vector_docs)} 条, BM25 {len(bm25_docs)} 条")

        # 三、检索后：融合与重排序
        # 1、RRF 融合：多路结果加权合并
        fused = rrf_fuser.fuse(vector_docs, bm25_docs)
        # 2、父子模式：用父块内容替换子块内容
        fused = self.replace_with_parent_context(fused)
        # 3、重排序：Cross-Encoder 精排
        results = reranker.rerank(question, fused)
        logger.info(f"检索后完成: {len(results)} 条结果")

        # 四、生成回答
        answer = self.generate(question, results)
        logger.info("回答生成完成")
        return answer

    def replace_with_parent_context(self, docs: list[dict]) -> list[dict]:
        """
        父子模式：用父块内容替换子块内容。
        @param docs: 子块检索结果
        @return: 父块内容列表
        """
        # 一、按 parent_index 去重
        seen = set()
        unique_docs = []
        for doc in docs:
            parent_index = doc.get("metadata", {}).get("parent_index")
            if parent_index is not None and parent_index not in seen:
                seen.add(parent_index)
                # 二、用父块内容替换
                parent_content = doc.get("metadata", {}).get("parent_content", "")
                if parent_content:
                    doc["content"] = parent_content
                unique_docs.append(doc)

        return unique_docs

    def generate(self, question: str, context: list[dict]) -> str:
        """
        生成回答。
        @param question: 用户问题
        @param context: 检索到的上下文
        @return: 回答文本
        """
        # TODO: 接入 LLM 生成
        return "暂未实现"


def create_rag_pipeline() -> RAGPipeline:
    """创建 RAG 管道实例（依赖注入入口）"""
    deps = RAGDependencies(
        query_rewriter=QueryRewriter(),
        query_expander=QueryExpander(),
    )
    return RAGPipeline(deps)


# 模块级单例（默认实例）
rag_pipeline = create_rag_pipeline()
