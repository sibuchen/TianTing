"""
User Info Tool
用户信息查询工具
"""

from typing import Any


async def query_user_info(params: dict[str, Any]) -> str:
    """
    查询用户信息
    """
    user_id = params.get("user_id", "未知")

    result = {
        "user_id": user_id,
        "username": "张三",
        "level": "VIP会员",
        "points": 5800,
        "total_orders": 25,
        "total_amount": 15680.00,
        "member_since": "2024-01-15",
    }

    return (
        f"用户信息：\n"
        f"用户ID：{result['user_id']}\n"
        f"用户名：{result['username']}\n"
        f"会员等级：{result['level']}\n"
        f"积分：{result['points']}\n"
        f"历史订单数：{result['total_orders']}\n"
        f"累计消费：¥{result['total_amount']}\n"
        f"注册时间：{result['member_since']}"
    )
