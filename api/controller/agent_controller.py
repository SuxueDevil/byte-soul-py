"""Agent 控制器：OpenAI 格式 SSE 流式聊天"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from langgraph.graph.state import CompiledStateGraph
from api.schemas.chat import ChatRequest
from api.service.agent_service import AgentServiceDep
from api.handler.openai_sse_response import OpenAIStreamResponse

agent_router = APIRouter(prefix="/agent", tags=["ReACT-Agent"])


@agent_router.post("/chat")
async def chat(
    request: ChatRequest,
    agent_service: AgentServiceDep,
):
    """
    OpenAI 格式 SSE 流式聊天接口。
    Args:
        request: ChatRequest，OpenAI chat.completions 格式
        agent_service: Agent 服务（依赖注入）
    """
    return OpenAIStreamResponse(agent_service.chat(request))
