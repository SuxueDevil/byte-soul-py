"""Agent 控制器：OpenAI 格式 SSE 流式聊天"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from langgraph.graph.state import CompiledStateGraph
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
    Args:
        request: ChatRequest，OpenAI chat.completions 格式
        agent_service: Agent 服务（依赖注入）
    """
    return OpenAIStreamResponse(agent_service.chat(request))


@agent_router.post("/react")
async def react(request: ChatRequest):
    """
    ReAct 模式 SSE 流式接口，输出推理过程。
    Args:
        request: ChatRequest
    """
    from agent.builder import agent
    from agent.nodes.react_node import react_node_stream
    from agent.schemas.state import AgentState
    from langchain_core.messages import HumanMessage

    # 一、构建初始状态
    state = AgentState()
    state.messages = [HumanMessage(content=request.messages[-1].content)]

    # 二、SSE 流式输出
    async def event_generator():
        async for event in react_node_stream(state):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
