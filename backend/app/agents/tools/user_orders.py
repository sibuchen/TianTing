"""
User Orders Tool
用户订单列表工具
"""

from typing import Any


async def query_user_orders(params: dict[str, Any]) -> str:
    """
    查询用户历史订单
    """
    user_id = params.get("user_id", "未知")

    orders = [
        {
            "order_id": "ORD20260501001",
            "product": "智能手表 Pro",
            "amount": 2999.00,
            "status": "已完成",
            "order_time": "2026-05-01 10:30:00",
        },
        {
            "order_id": "ORD20260425002",
            "product": "无线蓝牙耳机",
            "amount": 599.00,
            "status": "已完成",
            "order_time": "2026-04-25 15:20:00",
        },
        {
            "order_id": "ORD202604180003",
            "product": "移动电源 20000mAh",
            "amount": 129.00,
            "status": "已完成",
            "order_time": "2026-04-18 09:45:00",
        },
    ]

    orders_text = "\n".join(
        [
            f"[{o['order_time']}] {o['order_id']} - {o['product']} - ¥{o['amount']} - {o['status']}"
            for o in orders
        ]
    )

    return (
        f"用户 {user_id} 的历史订单：\n\n"
        f"{orders_text}\n\n"
        f"共 {len(orders)} 条订单记录"
    )
