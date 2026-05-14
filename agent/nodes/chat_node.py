from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.llm import llm
from config.logger import logger
from config.prompt import CHAT_PROMPT

prompt = ChatPromptTemplate.from_messages([
    ("system", CHAT_PROMPT),
    MessagesPlaceholder(variable_name="history"),
])


async def chat_node(state):
    """
    调用 LLM 流式生成回复，追加到消息历史。
    @param state: AgentState，包含 messages 列表
    @return: 更新后的 AgentState
    """
    # 一、注入对话上下文
    # 1、将历史消息填充到提示词模板
    messages = prompt.invoke({"history": state.messages})

    # 二、流式调用 LLM
    # 1、astream 逐 token 获取回复
    full = ""
    async for chunk in llm.astream(messages):
        full += chunk.content

    # 三、更新状态
    # 1、完整回复写入消息历史，供后续节点和记忆链使用
    state.messages.append(AIMessage(content=full))
    state.current_node = "chat"
    logger.info("[chat_node] state: {}", state)
    return state
