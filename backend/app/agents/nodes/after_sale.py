"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
After Sale Node
售后节点：工具调用
"""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.order import query_order_status
from app.agents.tools.logistics import query_logistics
from app.agents.tools.refund import submit_refund
from app.agents.tools.return_ import submit_return


async def after_sale_node(state: AgentState) -> AgentState:
    """
    售后节点
    处理退换货、订单查询等售后问题
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}
    user_content = last_message.get("content", "")

    tool_calls: list[dict[str, Any]] = []
    response = ""

    if "退款" in user_content or "取消订单" in user_content:
        result = await submit_refund({})
        tool_calls.append({
            "toolName": "submit_refund",
            "arguments": {},
            "result": result,
        })
        response = f"已为您提交退款申请：{result}"

    elif "退货" in user_content or "换货" in user_content:
        result = await submit_return({})
        tool_calls.append({
            "toolName": "submit_return",
            "arguments": {},
            "result": result,
        })
        response = f"已为您提交退货申请：{result}"

    elif "订单" in user_content:
        result = await query_order_status({"order_id": "ORD001"})
        tool_calls.append({
            "toolName": "query_order_status",
            "arguments": {"order_id": "ORD001"},
            "result": result,
        })
        response = f"您的订单状态：{result}"

    elif "物流" in user_content or "快递" in user_content:
        result = await query_logistics({"tracking_number": "SF123456789"})
        tool_calls.append({
            "toolName": "query_logistics",
            "arguments": {"tracking_number": "SF123456789"},
            "result": result,
        })
        response = f"您的物流信息：{result}"

    else:
        response = "您好，我是售后客服助手。请告诉我您的订单号或具体问题，我来帮您处理。"

    return {
        "current_node": "after_sale",
        "agent_response": response,
        "tool_calls": tool_calls,
    }
