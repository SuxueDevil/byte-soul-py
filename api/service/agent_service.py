import time

from langchain_core.messages import HumanMessage, AIMessage
from api.schemas.chat import ChatChunk, ChatRequest
from agent.graph import agent

# OpenAI role → LangChain 消息类型映射（system 由服务端 prompt 管理，不接收客户端传入）
_ROLE_MAP = {
    "user": HumanMessage,
    "assistant": AIMessage,
}


class AgentService:
    """Agent 服务层：接收 OpenAI 请求，返回 OpenAI 格式的流式 ChatChunk"""

    @staticmethod
    def _to_lc_messages(messages: list[ChatRequest.Message]):
        # 将 OpenAI 消息列表转为 LangChain 消息，过滤客户端 system 消息
        return [_ROLE_MAP[m.role](content=m.content) for m in messages if m.role != "system"]

    @staticmethod
    async def chat(request: ChatRequest):
        """
        流式对话接口。
        @param request: ChatRequest，OpenAI chat.completions 格式
        @yield: ChatChunk 实例
        """
        # 一、构建运行配置
        # 1、user 映射到 thread_id，同一用户共享一条 Thread，持久化记忆链
        config = {"configurable": {"thread_id": request.user}}

        # 二、OpenAI 事件公共字段
        # 1、chat_id 使用前端传入的 user 标识，同一用户多次请求共享此 ID
        chat_id = request.user
        # 2、created 为请求创建时的 Unix 时间戳（秒），同一请求所有帧共享
        created = int(time.time())
        # 3、客户端可指定模型，未指定则用默认值
        model = request.model or "YanXiaoYu"
        # 4、first_chunk 标记是否为首帧，首帧需在 delta 中附带 role: "assistant"
        first_chunk = True

        # 三、流式执行
        # 1、将 OpenAI 消息转为 LangChain 消息，注入图执行
        # 2、v2 事件格式，监听 on_chat_model_stream 获取增量 token
        async for event in agent.astream_events(
            {"messages": AgentService._to_lc_messages(request.messages)},
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
        # 1、finish_reason 为 stop，通知客户端流结束；未产生任何流式内容时仍需补 role
        delta = ChatChunk.Delta(role="assistant") if first_chunk else ChatChunk.Delta()
        yield ChatChunk(
            id=chat_id,
            created=created,
            model=model,
            choices=[ChatChunk.Choice(delta=delta, finish_reason="stop")],
        )
