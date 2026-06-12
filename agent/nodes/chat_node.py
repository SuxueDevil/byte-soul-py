from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.llm import llm
from config.logger import logger
from agent.prompts import CHAT_PROMPT


def _parse_content(content: str | list) -> str:
    """解析 LLM 返回内容，兼容字符串和结构化输出"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


# RAG 增强提示词
RAG_CHAT_PROMPT = """{base_prompt}

请基于以下检索到的上下文回答用户问题。如果上下文不相关，请忽略它直接回答。

<context>
{context}
</context>
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_CHAT_PROMPT),
    MessagesPlaceholder(variable_name="history"),
])


async def chat_node(state):
    """
    调用 LLM 流式生成回复，追加到消息历史。
    @param state: AgentState，包含 messages 列表和 rag_context
    @return: 更新后的 AgentState
    """
    # 一、注入对话上下文
    # 1、获取 RAG 上下文
    rag_context = getattr(state, "rag_context", "")
    # 2、构建增强提示词
    system_prompt = RAG_CHAT_PROMPT.format(
        base_prompt=CHAT_PROMPT,
        context=rag_context or "无检索上下文",
    )
    # 3、构建消息列表
    enhanced_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
    ])
    messages = enhanced_prompt.invoke({"history": state.messages})

    # 二、流式调用 LLM
    # 1、astream 逐 token 获取回复
    full = ""
    async for chunk in llm.astream(messages):
        full += _parse_content(chunk.content)

    # 三、更新状态
    # 1、完整回复写入消息历史，供后续节点和记忆链使用
    state.messages.append(AIMessage(content=full))
    state.current_node = "chat"
    logger.info("[chat_node] state: {}", state)
    return state
