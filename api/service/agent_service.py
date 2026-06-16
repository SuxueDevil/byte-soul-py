"""Agent 服务：接收 OpenAI 请求，返回 OpenAI 格式的流式 ChatChunk"""
import time
import uuid
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from agent.builder import agent
from api.schemas.chat import ChatChunk, ChatRequest

# OpenAI role → LangChain 消息类型映射
_ROLE_MAP = {
    "user": HumanMessage,
    "assistant": AIMessage,
}


@dataclass(frozen=True)
class AgentServiceDependencies:
    """Agent 服务依赖"""
    agent: CompiledStateGraph


class AgentService:
    """Agent 服务层：接收 OpenAI 请求，返回 OpenAI 格式的流式 ChatChunk"""

    def __init__(self, deps: AgentServiceDependencies) -> None:
        self.deps = deps

    def _to_lc_messages(self, messages: list[ChatRequest.Message]):
        """将 OpenAI 消息列表转为 LangChain 消息

        Args:
            messages: OpenAI 格式消息列表
        """
        return [_ROLE_MAP[m.role](content=m.content) for m in messages if m.role != "system"]

    async def chat(self, request: ChatRequest):
        """流式对话接口

        Args:
            request: ChatRequest，OpenAI chat.completions 格式

        Yields:
            ChatChunk 实例
        """
        # 一、构建运行配置
        user_id = request.user or f"anon-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": user_id}}

        # 二、OpenAI 事件公共字段
        chat_id = user_id
        created = int(time.time())
        model = request.model or "YanXiaoYu"
        first_chunk = True

        # 三、流式执行
        async for event in self.deps.agent.astream_events(
            {"messages": self._to_lc_messages(request.messages)},
            config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    if first_chunk:
                        delta = ChatChunk.Delta(role="assistant", content=chunk.content)
                        first_chunk = False
                    else:
                        delta = ChatChunk.Delta(content=chunk.content)
                    yield ChatChunk(
                        id=chat_id,
                        created=created,
                        model=model,
                        choices=[ChatChunk.Choice(delta=delta)],
                    )

        # 四、发送结束帧
        delta = ChatChunk.Delta(role="assistant") if first_chunk else ChatChunk.Delta()
        yield ChatChunk(
            id=chat_id,
            created=created,
            model=model,
            choices=[ChatChunk.Choice(delta=delta, finish_reason="stop")],
        )


# 一、模块级单例
# 1、import 时即建，LangGraph 图已在 agent.builder 编译好
agentService = AgentService(
    AgentServiceDependencies(agent=agent)
)
