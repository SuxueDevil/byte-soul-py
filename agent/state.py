from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Agent 全局状态，在各节点间流转，由 checkpointer 持久化。
    messages 使用 add_messages reducer，保证新旧消息合并而非覆盖。
    """
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    intent: str = ""          # 意图分类结果：chat 放行 / refuse 拦截
    current_node: str = ""    # 当前所在节点名，用于追踪执行路径
    rag_context: str = ""     # RAG 检索到的上下文
