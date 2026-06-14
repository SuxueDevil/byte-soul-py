"""Agent 服务：接收 OpenAI 请求，返回 OpenAI 格式的流式 ChatChunk"""
import time
import uuid
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage
from api.schemas.chat import ChatChunk, ChatRequest

# OpenAI role → LangChain 消息类型映射
_ROLE_MAP = {
    "user": HumanMessage,
    "assistant": AIMessage,
}


@dataclass
class AgentServiceDependencies:
    """Agent 服务依赖"""
    agent: object  # LangGraph CompiledStateGraph


class AgentService:
    """Agent 服务层：接收 OpenAI 请求，返回 OpenAI 格式的流式 ChatChunk"""

    def __init__(self, deps: AgentServiceDependencies):
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
        # 1、user 映射到 thread_id，同一用户共享一条 Thread
        user_id = request.user or f"anon-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": user_id}}

        # 二、OpenAI 事件公共字段
        # 1、id 回传 user 或自动生成的标识
        chat_id = user_id
        # 2、created 为请求创建时的 Unix 时间戳（秒）
        created = int(time.time())
        # 3、客户端可指定模型，未指定则用默认值
        model = request.model or "YanXiaoYu"
        # 4、first_chunk 标记是否为首帧
        first_chunk = True

        # 三、流式执行
        # 1、将 OpenAI 消息转为 LangChain 消息，注入图执行
        # 2、v2 事件格式，监听 on_chat_model_stream 获取增量 token
        async for event in self.deps.agent.astream_events(
            {"messages": self._to_lc_messages(request.messages)},
            config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                # 3、提取增量 token 文本
                chunk = event["data"]["chunk"]
                if chunk.content:
                    # 4、首帧 delta 带 role: "assistant"，后续帧仅 content
                    if first_chunk:
                        delta = ChatChunk.Delta(role="assistant", content=chunk.content)
                        first_chunk = False
                    else:
                        delta = ChatChunk.Delta(content=chunk.content)
                    # 5、构造 OpenAI chat.completion.chunk 响应块
                    yield ChatChunk(
                        id=chat_id,
                        created=created,
                        model=model,
                        choices=[ChatChunk.Choice(delta=delta)],
                    )

        # 四、发送结束帧
        # 1、finish_reason 为 stop，通知客户端流结束
        delta = ChatChunk.Delta(role="assistant") if first_chunk else ChatChunk.Delta()
        yield ChatChunk(
            id=chat_id,
            created=created,
            model=model,
            choices=[ChatChunk.Choice(delta=delta, finish_reason="stop")],
        )


def create_agent_service() -> AgentService:
    """创建 Agent 服务实例（依赖注入入口）"""
    from agent.builder import agent
    deps = AgentServiceDependencies(agent=agent)
    return AgentService(deps)


def get_agent_service() -> AgentService:
    """FastAPI Depends 注入点"""
    return create_agent_service()
