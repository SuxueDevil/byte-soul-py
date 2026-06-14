"""意图识别节点"""
from langchain_core.messages import SystemMessage

from config.llm import llm_no_stream
from config.logger import logger
from config.prompts import INTENT_PROMPT


async def intent_node(state):
    """识别用户消息是否属于医疗健康领域

    Args:
        state: AgentState，使用最后一条消息进行意图分类

    Returns:
        更新后的 AgentState，intent 字段为 chat 或 refuse
    """
    # 一、意图分类
    user_message = state.messages[-1]
    response = await llm_no_stream.ainvoke([
        SystemMessage(content=INTENT_PROMPT),
        user_message,
    ])

    # 二、解析结果
    content = response.content.strip().upper()
    state.intent = "chat" if "CHAT" in content else "refuse"
    state.current_node = "intent"

    # 三、记录用户问题(超长截断,避免日志刷屏)
    user_text = str(user_message.content)
    if len(user_text) > 80:
        user_text = user_text[:80] + "…"
    logger.info("[IntentNode] intent={} user={!r} raw={}",
                state.intent, user_text, response.content)
    return state
