"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
Orchestrator Node
编排节点：意图识别 + 路由
"""

from typing import Literal

from app.agents.state import AgentState


async def orchestrator_node(state: AgentState) -> AgentState:
    """
    编排器节点
    负责意图识别和路由分发
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}

    user_content = last_message.get("content", "")

    intent = _classify_intent(user_content)
    agent_type = _determine_agent_type(intent)

    return {
        "current_node": "orchestrator",
        "intent": intent,
        "agent_type": agent_type,
        "should_transfer_to_human": False,
    }


def _classify_intent(content: str) -> str:
    """
    意图分类
    这里使用规则匹配，MVP阶段可扩展为LLM调用
    """
    content_lower = content.lower()

    refund_keywords = ["退款", "退货", "换货", "退换", "不想要", "取消订单"]
    for keyword in refund_keywords:
        if keyword in content_lower:
            return "after_sale"

    faq_keywords = ["怎么", "如何", "是什么", "哪里", "什么", "请问", "有没有"]
    for keyword in faq_keywords:
        if keyword in content_lower:
            return "faq"

    greeting_keywords = ["你好", "在吗", "嗨", "hi", "hello", "您好"]
    for keyword in greeting_keywords:
        if keyword in content_lower:
            return "greeting"

    order_keywords = ["订单", "物流", "快递", "发货", "签收"]
    for keyword in order_keywords:
        if keyword in content_lower:
            return "after_sale"

    return "general"


def _determine_agent_type(intent: str) -> str:
    """确定Agent类型"""
    if intent == "after_sale":
        return "after-sale"
    elif intent == "faq":
        return "faq"
    elif intent == "greeting":
        return "direct"
    else:
        return "direct"
