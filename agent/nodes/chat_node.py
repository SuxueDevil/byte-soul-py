"""对话生成节点：调用 LLM 流式生成回复"""
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.llm import llm
from config.logger import logger
from agent.prompts import CHAT_PROMPT


def parse_content(content: str | list) -> str:
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


prompt = ChatPromptTemplate.from_messages([
    ("system", CHAT_PROMPT),
    MessagesPlaceholder(variable_name="history"),
])


async def chat_node(state):
    """
    调用 LLM 流式生成回复。
    @param state: AgentState
    @return: 更新后的 AgentState
    """
    # 一、构建消息列表
    messages = prompt.invoke({"history": state.messages})

    # 二、流式调用 LLM
    full = ""
    async for chunk in llm.astream(messages):
        full += parse_content(chunk.content)

    # 三、更新状态
    state.messages.append(AIMessage(content=full))
    state.current_node = "chat"
    logger.info("[chat_node] 回复生成完成")
    return state
