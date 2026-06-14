"""ReAct 节点：自主推理 + 工具调用循环"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from config.llm import llm_no_stream
from config.logger import logger
from agent.prompts import REACT_PROMPT
from agent.react import build_tools_description, parse_action, parse_final_answer, execute_tool

# ReAct 最大循环次数
MAX_ITERATIONS = 3


def parse_content(content: str | list) -> str:
    """解析 LLM 返回内容，兼容字符串和结构化输出"""
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


async def react_node(state):
    """
    ReAct 节点：自主推理 + 工具调用循环。
    @param state: AgentState
    @return: 更新后的 AgentState
    """
    # 一、获取用户消息
    user_message = None
    for msg in reversed(state.messages):
        if hasattr(msg, "content") and msg.type == "human":
            user_message = msg.content
            break

    if not user_message:
        logger.warning("[react_node] 未找到用户消息")
        state.current_node = "react"
        return state

    # 二、构建 ReAct Prompt
    tools_desc = build_tools_description()
    system_prompt = REACT_PROMPT.format(tools=tools_desc)

    # 三、ReAct 循环
    conversation: list[BaseMessage] = []
    final_answer = None
    llm_output = ""

    for iteration in range(MAX_ITERATIONS):
        logger.info(f"[react_node] 循环 {iteration + 1}/{MAX_ITERATIONS}")

        # 1、构建消息列表
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        messages.append(HumanMessage(content=user_message))
        messages.extend(conversation)

        # 2、调用 LLM
        response = await llm_no_stream.ainvoke(messages)
        llm_output = parse_content(response.content)
        logger.info(f"[react_node] LLM 输出:\n{llm_output}")

        # 3、解析输出
        conversation.append(response)

        # 4、检查是否有 Final Answer
        final = parse_final_answer(llm_output)
        if final:
            final_answer = final
            logger.info("[react_node] 获得最终答案")
            break

        # 5、解析 Action
        action_result = parse_action(llm_output)
        if not action_result:
            logger.warning("[react_node] 无法解析 Action，使用 LLM 输出作为答案")
            final_answer = llm_output
            break

        action, action_input = action_result
        logger.info(f"[react_node] 调用工具: {action}, 参数: {action_input}")

        # 6、执行工具
        observation = execute_tool(action, action_input)
        logger.info(f"[react_node] 工具结果: {observation[:200]}...")

        # 7、将结果加入对话
        conversation.append(HumanMessage(content=f"Observation: {observation}"))

    # 四、如果没有获得最终答案，使用最后一次 LLM 输出
    if not final_answer:
        logger.warning("[react_node] 达到最大循环次数，使用最后一次输出")
        final_answer = llm_output

    # 五、更新状态
    state.messages.append(AIMessage(content=final_answer))
    state.current_node = "react"

    return state
