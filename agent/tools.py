"""工具定义、注册与执行"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────── 数据结构 ───────────────────────────

@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    params: List[Dict[str, str]]
    func: Callable[[Dict[str, Any]], str]


@dataclass
class CallResult:
    """工具调用结果"""
    success: bool
    content: str
    error: Optional[str] = None
    tool_name: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────── RAG 工具 ───────────────────────────

def rag_search(args: Dict[str, Any]) -> str:
    """RAG 知识库检索"""
    from agent.rag.pipeline import rag_pipeline
    query = args.get("query", "")
    if not query:
        return "请提供检索关键词"
    try:
        result = rag_pipeline.query(query)
        return result if result else "未找到相关信息"
    except Exception as e:
        return f"检索失败: {str(e)}"


# ─────────────────────────── 默认工具集 ───────────────────────────

def default_tools() -> List[Tool]:
    """返回默认工具集合"""
    return [
        Tool(
            name="rag_search",
            description="在知识库中检索相关信息",
            params=[{"name": "query", "type": "string", "description": "检索关键词"}],
            func=rag_search,
        ),
    ]


# ─────────────────────────── 工具执行器 ───────────────────────────

class ToolExecutor:
    """工具执行器"""

    def __init__(self, tools: Optional[List[Tool]] = None):
        self.tools = tools if tools else default_tools()
        self.tool_map = {t.name: t for t in self.tools}

    def call(self, tool_name: str, args: Dict[str, Any]) -> CallResult:
        """
        调用工具。
        @param tool_name: 工具名称
        @param args: 工具参数
        @return: 调用结果
        """
        if tool_name not in self.tool_map:
            return CallResult(
                success=False, content="", error=f"工具 {tool_name} 不存在",
                tool_name=tool_name, params=args or {},
            )

        tool = self.tool_map[tool_name]
        try:
            result = tool.func(args or {})
            return CallResult(
                success=True, content=str(result),
                tool_name=tool_name, params=args or {},
            )
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            return CallResult(
                success=False, content="", error=str(e),
                tool_name=tool_name, params=args or {},
            )

    def get_tool_descriptions(self) -> str:
        """
        获取工具描述文本，用于 Prompt。
        @return: 工具描述字符串
        """
        lines = []
        for tool in self.tools:
            params_desc = ", ".join(
                f"{p['name']}({p.get('type', 'string')}): {p.get('description', '')}"
                for p in tool.params
            )
            lines.append(f"- {tool.name}: {tool.description} | 参数: {params_desc}")
        return "\n".join(lines)

    def add_tool(self, tool: Tool) -> None:
        """添加工具"""
        self.tools.append(tool)
        self.tool_map[tool.name] = tool


# 模块级单例
tool_executor = ToolExecutor()
