"""工具注册表"""
from agent.tools import rag_tool

# 工具注册表
TOOLS = {
    rag_tool.name: rag_tool,
}


def build_tools_description() -> str:
    """
    构建工具描述文本，用于 Prompt。
    @return: 工具描述字符串
    """
    return "\n".join(tool.to_prompt() for tool in TOOLS.values())


def get_tool(name: str):
    """
    根据名称获取工具。
    @param name: 工具名称
    @return: 工具实例或 None
    """
    return TOOLS.get(name)


def get_available_tools() -> list[str]:
    """
    获取可用工具名称列表。
    @return: 工具名称列表
    """
    return list(TOOLS.keys())
