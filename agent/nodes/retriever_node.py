"""RAG 检索节点：在 LLM 生成前执行检索，注入上下文"""
from agent.rag.pipeline import rag_pipeline
from config.logger import logger


def retriever_node(state):
    """
    RAG 检索节点：根据用户问题检索相关文档，注入上下文。
    @param state: AgentState，包含 messages 列表
    @return: 更新后的 AgentState
    """
    # 获取用户最后一条消息
    user_message = None
    for msg in reversed(state.messages):
        if hasattr(msg, "content") and msg.type == "human":
            user_message = msg.content
            break

    if not user_message:
        logger.warning("[retriever_node] 未找到用户消息")
        state.current_node = "retriever"
        return state

    # 执行 RAG 检索
    try:
        context = rag_pipeline.query(user_message)
        # 将检索到的上下文注入状态
        state.rag_context = context
        logger.info("[retriever_node] 检索完成，上下文长度: {} 字符", len(context))
    except Exception as e:
        logger.error("[retriever_node] 检索失败: {}", str(e))
        state.rag_context = ""

    state.current_node = "retriever"
    return state
