"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
Agent Graph
StateGraph图定义与构建
"""

import os
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes.orchestrator import orchestrator_node
from app.agents.nodes.faq import faq_node
from app.agents.nodes.after_sale import after_sale_node
from app.agents.nodes.direct_reply import direct_reply_node
from app.agents.nodes.human_transfer import human_transfer_node


def create_agent_graph() -> StateGraph:
    """创建Agent图"""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("faq", faq_node)
    graph.add_node("after_sale", after_sale_node)
    graph.add_node("direct_reply", direct_reply_node)
    graph.add_node("human_transfer", human_transfer_node)

    graph.set_entry_point("orchestrator")

    def route_next(
        state: AgentState,
    ) -> Literal["faq", "after_sale", "direct_reply", "human_transfer", END]:
        """路由决策"""
        if state.get("should_transfer_to_human"):
            return "human_transfer"

        agent_type = state.get("agent_type")

        if agent_type == "faq":
            return "faq"
        elif agent_type == "after-sale":
            return "after_sale"
        elif agent_type == "direct":
            return "direct_reply"
        else:
            return "direct_reply"

    graph.add_conditional_edges(
        "orchestrator",
        route_next,
        {
            "faq": "faq",
            "after_sale": "after_sale",
            "direct_reply": "direct_reply",
            "human_transfer": "human_transfer",
            END: END,
        },
    )

    graph.add_edge("faq", END)
    graph.add_edge("after_sale", END)
    graph.add_edge("direct_reply", END)
    graph.add_edge("human_transfer", END)

    return graph


def compile_graph() -> StateGraph:
    """编译图"""
    graph = create_agent_graph()
    return graph.compile()


agent_graph = compile_graph()
