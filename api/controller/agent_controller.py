from fastapi import APIRouter
from api.schemas.chat import ChatRequest
from api.service.agent_service import AgentService
from api.handler.openai_sse_response import OpenAIStreamResponse

agent_router = APIRouter(prefix="/agent", tags=["医疗Agent"])


@agent_router.post("/chat")
async def chat(request: ChatRequest):
    """OpenAI 格式 SSE 流式聊天接口"""
    return OpenAIStreamResponse(AgentService.chat(request))
