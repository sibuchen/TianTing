"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
Human Transfer Node
人工转接节点
"""

from app.agents.state import AgentState


async def human_transfer_node(state: AgentState) -> AgentState:
    """
    人工转接节点
    将对话转接给人工客服
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}
    user_content = last_message.get("content", "")

    response = (
        "您好，看起来您的问题需要人工客服来处理。\n"
        "我已经将您的问题记录，稍后会有专业的客服人员为您服务。\n"
        "请您稍等，感谢您的耐心！"
    )

    return {
        "current_node": "human_transfer",
        "agent_response": response,
        "should_transfer_to_human": True,
    }
