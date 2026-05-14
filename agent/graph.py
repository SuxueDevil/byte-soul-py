from langgraph.graph import END, StateGraph

from memory.checkpointer import checkpointer
from nodes.chat_node import chat_node
from nodes.intent_node import intent_node
from nodes.refuse_node import refuse_node
from state.agent_state import AgentState


class AgentGraphBuilder:
    """LangGraph 状态图构建器，编译后导出模块级单例"""

    def route_decision(self, state: AgentState) -> str:
        """
        根据意图分类结果路由到对应节点。
        @param state: 当前 Agent 状态
        @return: 目标节点名（chat 或 refuse）
        """
        return state.intent

    def build(self):
        """
        构建并编译带条件路由的 StateGraph。
        @return: 编译后的 CompiledStateGraph 实例
        """
        # 一、构建状态图
        # 1、创建 StateGraph
        state_graph = StateGraph(AgentState)
        # 2、添加节点：意图分类 → 对话生成 → 终审拦截
        state_graph.add_node("intent", intent_node)
        state_graph.add_node("chat", chat_node)
        state_graph.add_node("refuse", refuse_node)

        # 二、配置路由
        # 1、入口节点
        state_graph.set_entry_point("intent")
        # 2、条件边：根据 intent 结果路由到 chat 或 refuse
        state_graph.add_conditional_edges(
            "intent", self.route_decision,
            {"chat": "chat", "refuse": "refuse"},
        )
        # 3、无条件边：chat → refuse → END
        state_graph.add_edge("chat", "refuse")
        state_graph.add_edge("refuse", END)

        return state_graph.compile(checkpointer=checkpointer, store=None)


agent = AgentGraphBuilder().build()
