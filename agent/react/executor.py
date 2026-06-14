"""工具执行器"""
import json
from agent.tools import tool_executor


def execute_tool(action: str, action_input: str) -> str:
    """
    执行工具调用。
    @param action: 工具名称
    @param action_input: 工具参数（JSON 字符串）
    @return: 工具执行结果
    """
    try:
        params = json.loads(action_input)
    except json.JSONDecodeError:
        # 尝试将整个输入作为 query 参数
        params = {"query": action_input}

    result = tool_executor.call(action, params)
    return result.content if result.success else f"错误: {result.error}"
