import time
import uuid

from langchain_core.messages import HumanMessage
from api.schemas.chat import ChatChunk, ChatRequest
from agent.graph import agent


class AgentService:
    """Agent 服务层：接收用户消息，返回 OpenAI 格式的流式 ChatChunk"""

    @staticmethod
    async def chat(request: ChatRequest):
        """
        流式对话接口。
        @param request: ChatRequest，包含 user_id 区分会话、message 用户输入
        @yield: ChatChunk 实例
        """
        # 一、构建运行配置
        # 1、thread_id 映射到 user_id，同一用户共享一条 Thread，持久化记忆链
        config = {"configurable": {"thread_id": request.user_id}}

        # 二、OpenAI 事件公共字段
        # 1、chat_id 为本次对话唯一标识，格式 chatcmpl-{29位hex}
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        # 2、created 为请求创建时的 Unix 时间戳（秒），同一请求所有帧共享
        created = int(time.time())
        model = "YanXiaoYu"
        # 3、first_chunk 标记是否为首帧，首帧需在 delta 中附带 role: "assistant"
        first_chunk = True

        # 三、流式执行
        # 1、v2 事件格式，监听 on_chat_model_stream 获取增量 token
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                # 2、提取增量 token 文本
                chunk = event["data"]["chunk"]
                if chunk.content:
                    # 3、首帧 delta 带 role: "assistant"，后续帧仅 content
                    if first_chunk:
                        delta = ChatChunk.Delta(role="assistant", content=chunk.content)
                        first_chunk = False
                    else:
                        delta = ChatChunk.Delta(content=chunk.content)
                    # 4、构造 OpenAI chat.completion.chunk 响应块
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
