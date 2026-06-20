"""RAG 管道：串联全部核心步骤"""
from pathlib import Path

from langchain_core.documents import Document

from agent.rag.mid import retriever
from config.logger import logger

from agent.rag.pre.ik_tokenize import ikTokenizer
from agent.rag.pre.query_rewriter import queryRewriter
from agent.rag.pre.query_expansion import queryExpander
from agent.rag.ingestion.spliter import Spilter
from agent.rag.ingestion.saver import Saver


class RAGPipeline:
    """RAG 管道：离线入库 + 在线检索"""

    async def ingest(self, file_name: str , content: str, ) -> int:
        """离线入库流程

        Args:
            content: 文件内容
            file_name: 文件名

        Returns:
            入库的 chunk 数量
        """
        logger.info(f"[RagPipeline] 开始入库: {file_name}")

        # 一、直接把内容转成 Document
        doc = Document(page_content=content, metadata={"source": file_name})

        # 二、按扩展名切割
        suffix = Path(file_name).suffix.lower()
        match suffix:
            case ".md" | ".markdown" | ".txt":
                chunks = Spilter.markdown([doc])
            case ".pdf":
                chunks = Spilter.pdf([doc])
            case ".docx" | ".word":
                chunks = Spilter.word([doc])
            case _:
                logger.warning(f"[RagPipeline] 不支持的文件类型: {suffix}")
                return 0

        # 三、统一入库
        count = await Saver.save(chunks, file_name)

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
        # 1、IK 提取关键词，辅助 LLM 改写
        keywords = ikTokenizer.extract_keywords(question)
        # 2、LLM 改写（传入关键词辅助）
        rewritten = queryRewriter.rewrite(question, keywords)
        # 3、查询扩展
        queries = queryExpander.expand(rewritten)
        logger.info(f"[RagPipeline] 检索前完成: keywords={keywords}")

        # 二、检索中：多路检索
        vector_docs = retriever.vector_search(queries)
        bm25_docs = retriever.bm25_search(queries)
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


ragPipeline = RAGPipeline()
