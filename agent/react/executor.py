"""工具执行器"""
import json

from config.logger import logger
from .registry import get_tool, get_available_tools


def execute_tool(action: str, action_input: str) -> str:
    """
    执行工具调用。
    @param action: 工具名称
    @param action_input: 工具参数（JSON 字符串）
    @return: 工具执行结果
    """
    # 一、查找工具
    tool = get_tool(action)
    if not tool:
        available = get_available_tools()
        return f"错误：未知工具 '{action}'，可用工具: {available}"

    # 二、解析参数并执行
    try:
        params = json.loads(action_input)
        return tool.execute(**params)
    except json.JSONDecodeError:
        # 1、尝试将整个输入作为 query 参数
        return tool.execute(query=action_input)
    except Exception as e:
        return f"工具执行失败: {str(e)}"
