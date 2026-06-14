"""ReAct 节点：自主推理 + 工具调用循环（SSE 流式输出）"""
import json
import re

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from config.llm import llm_no_stream
from config.logger import logger
from agent.prompts import REACT_PROMPT
from agent.tools import tools

# ReAct 最大循环次数
MAX_ITERATIONS = 3

# 工具名称列表
TOOL_NAMES = [t.name for t in tools]


def parse_content(content: str | list) -> str:
    """解析 LLM 返回内容，兼容字符串和结构化输出

    Args:
        content: LLM 返回的内容，可能是字符串或列表
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


def parse_action(text: str) -> tuple[str, str] | None:
    """从 LLM 输出中解析 Action 和 Action Input

    Args:
        text: LLM 输出文本

    Returns:
        (action, action_input) 或 None
    """
    action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text)

    if action_match and input_match:
        action = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        return action, action_input
    return None


def parse_final_answer(text: str) -> str | None:
    """从 LLM 输出中解析 Final Answer

    Args:
        text: LLM 输出文本

    Returns:
        最终答案或 None
    """
    match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def execute_tool(action: str, action_input: str) -> str:
    """执行工具调用

    Args:
        action: 工具名称
        action_input: 工具参数（JSON 字符串）

    Returns:
        工具执行结果
    """
    tool_map = {t.name: t for t in tools}
    tool = tool_map.get(action)
    if not tool:
        return f"错误：未知工具 '{action}'，可用工具: {TOOL_NAMES}"

    try:
        params = json.loads(action_input)
        return tool.invoke(params)
    except json.JSONDecodeError:
        return tool.invoke({"query": action_input})
    except Exception as e:
        return f"工具执行失败: {str(e)}"


def build_tools_description() -> str:
    """构建工具描述文本，用于 Prompt

    Returns:
        工具描述字符串
    """
    lines = []
    for tool in tools:
        lines.append(f"- {tool.name}: {tool.description}")
    return "\n".join(lines)


async def react_node_stream(state):
    """ReAct 节点：自主推理 + 工具调用循环，SSE 流式输出

    Args:
        state: AgentState

    Yields:
        SSE 事件：Thought / Action / Observation / Final Answer
    """
    # 一、获取用户消息
    user_message = None
    for msg in reversed(state.messages):
        if hasattr(msg, "content") and msg.type == "human":
            user_message = msg.content
            break

    if not user_message:
        yield {"type": "error", "content": "未找到用户消息"}
        state.current_node = "react"
        return

    # 二、构建 ReAct Prompt
    tools_desc = build_tools_description()
    system_prompt = REACT_PROMPT.format(tools=tools_desc)

    # 三、ReAct 循环
    conversation: list[BaseMessage] = []
    final_answer = None
    llm_output = ""

    for iteration in range(MAX_ITERATIONS):
        # 1、构建消息列表
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        messages.append(HumanMessage(content=user_message))
        messages.extend(conversation)

        # 2、调用 LLM（流式）
        full_content = ""
        async for chunk in llm_no_stream.astream(messages):
            if chunk.content:
                token = parse_content(chunk.content)
                full_content += token
                yield {"type": "token", "content": token}

        llm_output = full_content
        yield {"type": "thought", "content": llm_output}

        # 3、解析输出
        conversation.append(AIMessage(content=llm_output))

        # 4、检查是否有 Final Answer
        final = parse_final_answer(llm_output)
        if final:
            final_answer = final
            yield {"type": "answer", "content": final_answer}
            break

        # 5、解析 Action
        action_result = parse_action(llm_output)
        if not action_result:
            final_answer = llm_output
            yield {"type": "answer", "content": final_answer}
            break

        action, action_input = action_result
        yield {"type": "action", "content": f"{action}({action_input})"}

        # 6、执行工具
        observation = execute_tool(action, action_input)
        yield {"type": "observation", "content": observation}

        # 7、将结果加入对话
        conversation.append(HumanMessage(content=f"Observation: {observation}"))

    # 四、如果没有获得最终答案
    if not final_answer:
        final_answer = llm_output
        yield {"type": "answer", "content": final_answer}

    # 五、更新状态
    state.messages.append(AIMessage(content=final_answer))
    state.current_node = "react"


async def react_node(state):
    """ReAct 节点：非流式版本，兼容 LangGraph

    Args:
        state: AgentState

    Returns:
        更新后的 AgentState
    """
    async for event in react_node_stream(state):
        if event["type"] == "answer":
            logger.info(f"[react_node] 最终答案: {event['content'][:100]}...")
    return state
