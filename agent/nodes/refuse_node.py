from langchain_core.messages import AIMessage

from config.logger import logger
from config.prompts import REFUSE_PROMPT


def refuse_node(state):
    """
    终审节点：非医疗意图追加拒绝消息，医疗意图透传。
    @param state: AgentState，根据 intent 决定是否拦截
    @return: 更新后的 AgentState
    """
    # 一、意图拦截
    # 1、非医疗意图追加预设拒绝回复，医疗意图保留 chat_node 生成的回答
    if state.intent != "medical":
        state.messages.append(AIMessage(content=REFUSE_PROMPT))

    state.current_node = "refuse"
    logger.info("[refuse_node] state: {}", state)
    return state
