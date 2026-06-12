"""RAG 管道编排：整合检索前-中-后全流程"""
from langchain_core.documents import Document
from config.settings import settings
from config.logger import logger

# 检索前
from .pre_retrieval.query_rewriter import query_rewriter
from .pre_retrieval.query_expansion import query_expander

# 检索中
from .mid_retrieval.vector_retriever import vector_retriever
from .mid_retrieval.bm25_retriever import bm25_retriever
from .mid_retrieval.compressor import compressor

# 检索后
from .post_retrieval.fusion import rrf_fuser
from .post_retrieval.reranker import reranker

# 工具
from .ingestion.loader import DocumentLoader
from .ingestion.splitter import splitter
from .ingestion.docstore import docstore
from .utils import format_docs


class RAGPipeline:
    """RAG 管道：编排完整的检索增强生成流程"""

    def __init__(self):
        """初始化 RAG 管道"""
        self._bm25_fitted = False

    def index_documents(self, file_paths: list[str] | None = None, dir_path: str | None = None):
        """
        索引文档到向量库。
        @param file_paths: 文件路径列表
        @param dir_path: 目录路径（加载目录下所有文档）
        """
        # 加载文档
        documents = []
        if file_paths:
            for path in file_paths:
                documents.extend(DocumentLoader.load(path))
        if dir_path:
            documents.extend(DocumentLoader.load_directory(dir_path))

        if not documents:
            logger.warning("[RAG] 没有文档可索引")
            return

        logger.info("[RAG] 加载了 {} 个文档", len(documents))

        # 分块
        chunks = splitter.split(documents)
        logger.info("[RAG] 分块后 {} 个片段", len(chunks))

        # 存储原文
        docstore.add_many(chunks)

        # 构建 BM25 索引
        bm25_retriever.fit(chunks)
        self._bm25_fitted = True
        logger.info("[RAG] BM25 索引构建完成")

        # 向量库会自动索引（Chroma 特性）
        logger.info("[RAG] 文档索引完成")

    async def retrieve(self, query: str) -> str:
        """
        执行完整的 RAG 检索流程。
        @param query: 用户查询
        @return: 检索到的上下文文本
        """
        logger.info("[RAG] 开始检索: {}", query)

        # ====== 检索前：查询优化 ======
        processed_query = query
        if settings.rag_enable_rewrite:
            processed_query = await query_rewriter.arewrite(query)
            logger.info("[RAG] 查询改写: {} -> {}", query, processed_query)

        queries = [processed_query]
        if settings.rag_enable_expansion:
            queries = await query_expander.aexpand(processed_query)
            logger.info("[RAG] 查询扩展: {} 个查询", len(queries))

        # ====== 检索中：多路检索 ======
        vector_docs = []
        bm25_docs = []

        # 向量检索（使用所有扩展查询）
        for q in queries:
            docs = await vector_retriever.aretrieve(q)
            vector_docs.extend(docs)
        logger.info("[RAG] 向量检索: {} 个文档", len(vector_docs))

        # BM25 检索
        if settings.rag_enable_bm25 and self._bm25_fitted:
            for q in queries:
                docs = await bm25_retriever.aretrieve(q)
                bm25_docs.extend(docs)
            logger.info("[RAG] BM25 检索: {} 个文档", len(bm25_docs))

        # 上下文压缩
        if settings.rag_enable_compression:
            if vector_docs:
                vector_docs = await compressor.acompress(query, vector_docs)
            if bm25_docs:
                bm25_docs = await compressor.acompress(query, bm25_docs)
            logger.info("[RAG] 上下文压缩完成")

        # ====== 检索后：融合与重排序 ======
        # RRF 融合
        all_docs = rrf_fuser.fuse(vector_docs, bm25_docs)
        logger.info("[RAG] RRF 融合: {} 个文档", len(all_docs))

        # 重排序
        if settings.rag_enable_reranker and all_docs:
            all_docs = await reranker.arerank(query, all_docs)
            logger.info("[RAG] 重排序完成")

        # 格式化输出
        context = format_docs(all_docs[:settings.retrieval_top_k])
        logger.info("[RAG] 检索完成，上下文长度: {} 字符", len(context))

        return context


# 模块级单例
rag_pipeline = RAGPipeline()
