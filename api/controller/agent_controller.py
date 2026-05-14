from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.schemas.chat import ChatRequest
from api.service.agent_service import AgentService

agent_router = APIRouter(prefix="/agent", tags=["医疗Agent"])


@agent_router.post("/chat")
async def chat(request: ChatRequest):
    """
    流式聊天接口，SSE 协议推送 LLM 生成的 token。
    @param request: 用户消息体
    @return: StreamingResponse，media_type 为 text/event-stream
    """
    async def event_stream():
        # 一、逐块拉取 AgentService 流式输出
        # 1、每块包装为 data: ...\n\n 格式
        async for chunk in AgentService.chat(request):
            yield f"data: {chunk}\n\n"
        # 2、[DONE] 标记流结束，前端据此关闭连接
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
