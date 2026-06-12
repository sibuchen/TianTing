"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
Agent State
图状态定义
"""

from typing import TypedDict, Literal


class AgentState(TypedDict, total=False):
    """Agent状态"""

    conversation_id: str
    session_id: str
    user_id: str | None
    user_name: str | None
    messages: list[dict]
    current_node: str
    intent: str | None
    agent_type: str | None
    should_transfer_to_human: bool
    agent_response: str | None
    tool_calls: list[dict] | None
    rag_results: list[dict] | None
    error: str | None
