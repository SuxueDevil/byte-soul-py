"""Agent 控制器：OpenAI 格式 SSE 流式聊天"""
from fastapi import APIRouter

from api.schemas.chat import ChatRequest
from api.service.agent_service import agentService
from api.handler.openai_sse_response import OpenAIStreamResponse

agent_router = APIRouter(prefix="/agent", tags=["ReACT-Agent"])


@agent_router.post("/chat")
async def chat(request: ChatRequest):
    """
    OpenAI 格式 SSE 流式聊天接口。
    Args:
        request: ChatRequest，OpenAI chat.completions 格式
    """
    return OpenAIStreamResponse(agentService.chat(request))