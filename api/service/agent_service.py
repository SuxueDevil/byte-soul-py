from langchain_core.messages import HumanMessage
from api.schemas.chat import ChatRequest
from agent.graph import agent


class AgentService:
    """Agent 服务层：接收用户消息，返回 LLM 流式回复"""

    @staticmethod
    async def chat(request: ChatRequest):
        """
        流式对话接口。
        @param request: ChatRequest，包含 user_id 区分会话、message 用户输入
        @yield: LLM 生成的文本片段（SSE 流式输出）
        """
        # 一、构建运行配置
        # 1、thread_id 映射到 user_id，同一用户共享一条 Thread，持久化记忆链
        config = {"configurable": {"thread_id": request.user_id}}

        # 二、流式执行
        # 1、v2 事件格式，监听 on_chat_model_stream 获取增量 token
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield chunk.content
