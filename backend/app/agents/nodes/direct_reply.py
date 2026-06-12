"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
Direct Reply Node
直接回复节点：闲聊/问候
"""

from app.agents.state import AgentState


async def direct_reply_node(state: AgentState) -> AgentState:
    """
    直接回复节点
    处理问候、闲聊等简单场景
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}
    user_content = last_message.get("content", "")

    response = _generate_direct_reply(user_content)

    return {
        "current_node": "direct_reply",
        "agent_response": response,
        "tool_calls": None,
    }


def _generate_direct_reply(content: str) -> str:
    """生成直接回复"""
    content_lower = content.lower()

    greeting_keywords = ["你好", "在吗", "嗨", "hi", "hello", "您好"]
    for keyword in greeting_keywords:
        if keyword in content_lower:
            return "您好！很高兴为您服务。我是天听智能客服，请问有什么可以帮您的？"

    thanks_keywords = ["谢谢", "感谢", "多谢", "thanks"]
    for keyword in thanks_keywords:
        if keyword in content_lower:
            return "不客气！请问还有其他问题需要帮助吗？"

    goodbye_keywords = ["再见", "拜拜", "bye", "好的"]
    for keyword in goodbye_keywords:
        if keyword in content_lower:
            return "再见！祝您生活愉快。如有需要，随时联系我们。"

    return "我理解您的问题。请问您是想咨询产品信息、订单问题还是其他内容呢？请详细描述您的问题，我会尽力帮您解答。"
