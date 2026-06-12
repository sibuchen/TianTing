"""
Order Status Tool
订单状态查询工具
"""

from typing import Any


async def query_order_status(params: dict[str, Any]) -> str:
    """
    查询订单状态
    """
    order_id = params.get("order_id", "未知")

    result = {
        "order_id": order_id,
        "status": "已发货",
        "amount": 299.00,
        "payment_method": "支付宝",
        "shipping_time": "2026-05-02 10:30:00",
        "estimated_delivery": "2026-05-05",
    }

    return (
        f"订单号：{result['order_id']}\n"
        f"订单状态：{result['status']}\n"
        f"订单金额：¥{result['amount']}\n"
        f"支付方式：{result['payment_method']}\n"
        f"发货时间：{result['shipping_time']}\n"
        f"预计送达：{result['estimated_delivery']}"
    )
