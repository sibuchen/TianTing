"""
Refund Tool
退款处理工具
"""

from typing import Any


async def submit_refund(params: dict[str, Any]) -> str:
    """
    提交退款申请
    """
    refund_id = f"REF{params.get('order_id', '000')}{'A'}"
    amount = params.get("amount", 299.00)
    reason = params.get("reason", "用户申请")

    result = {
        "refund_id": refund_id,
        "order_id": params.get("order_id", "未知"),
        "amount": amount,
        "reason": reason,
        "status": "处理中",
        "estimated_time": "3-5个工作日",
    }

    return (
        f"退款申请已提交成功！\n"
        f"退款单号：{result['refund_id']}\n"
        f"订单号：{result['order_id']}\n"
        f"退款金额：¥{result['amount']}\n"
        f"退款原因：{result['reason']}\n"
        f"退款状态：{result['status']}\n"
        f"预计到账时间：{result['estimated_time']}"
    )
