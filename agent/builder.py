"""LangGraph 状态图构建器"""
from langgraph.graph import END, StateGraph

from .memory.checkpointer import checkpointer
from .nodes.intent_node import intent_node
from .nodes.react_node import react_node
from .nodes.refuse_node import refuse_node
from .schemas.state import AgentState


class AgentGraphBuilder:
    """LangGraph 状态图构建器，编译后导出模块级单例"""

    def route_decision(self, state: AgentState) -> str:
        """根据意图分类结果路由到对应节点

        Args:
            state: 当前 Agent 状态

        Returns:
            目标节点名（react 或 refuse）
        """
        return state.intent

    def build(self):
        """构建并编译带条件路由的 StateGraph

        Returns:
            编译后的 CompiledStateGraph 实例
        """
        # 一、构建状态图
        state_graph = StateGraph(AgentState)

        # 二、添加节点：意图分类 → ReAct 循环 → 终审拦截
        state_graph.add_node("intent", intent_node)
        state_graph.add_node("react", react_node)
        state_graph.add_node("refuse", refuse_node)

        # 三、配置路由
        state_graph.set_entry_point("intent")
        state_graph.add_conditional_edges(
            "intent", self.route_decision,
            {"chat": "react", "refuse": "refuse"},
        )
        state_graph.add_edge("react", END)
        state_graph.add_edge("refuse", END)

        return state_graph.compile(checkpointer=checkpointer, store=None)


# 模块级单例
agent = AgentGraphBuilder().build()
