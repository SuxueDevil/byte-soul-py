"""Agent 控制器：OpenAI 格式 SSE 流式聊天"""
from fastapi import APIRouter, Depends
from api.schemas.chat import ChatRequest
from api.service.agent_service import AgentService, get_agent_service
from api.handler.openai_sse_response import OpenAIStreamResponse

agent_router = APIRouter(prefix="/agent", tags=["医疗Agent"])


@agent_router.post("/chat")
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    OpenAI 格式 SSE 流式聊天接口。
    @param request: ChatRequest，OpenAI chat.completions 格式
    @param agent_service: Agent 服务（依赖注入）
    @return: SSE 流式响应
    """
    return OpenAIStreamResponse(agent_service.chat(request))
