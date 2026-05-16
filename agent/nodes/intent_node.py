from langchain_core.messages import SystemMessage

from config.llm import llm_no_stream
from config.logger import logger
from config.prompt import INTENT_PROMPT


async def intent_node(state):
    """
    识别用户消息是否属于医疗健康领域。
    @param state: AgentState，使用最后一条消息进行意图分类
    @return: 更新后的 AgentState，intent 字段为 chat 或 refuse
    """
    # 一、意图分类
    # 1、调用 LLM，prompt 要求仅回复 CHAT 或 REFUSE
    response = await llm_no_stream.ainvoke([
        SystemMessage(content=INTENT_PROMPT),
        state.messages[-1],
    ])

    # 二、解析结果
    # 1、提取意图标签，兼容模型多输出其他内容的情况
    content = response.content.strip().upper()
    state.intent = "chat" if "CHAT" in content else "refuse"
    state.current_node = "intent"
    logger.info("[intent_node] intent={} raw={}", state.intent, response.content)
    return state
