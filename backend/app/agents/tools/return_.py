"""
Return Tool
退换货处理工具
"""

from typing import Any


async def submit_return(params: dict[str, Any]) -> str:
    """
    提交退货申请
    """
    return_id = f"RET{params.get('order_id', '000')}{'A'}"
    reason = params.get("reason", "用户申请")

    result = {
        "return_id": return_id,
        "order_id": params.get("order_id", "未知"),
        "reason": reason,
        "status": "待退货",
        "instructions": [
            "请将商品包装好",
            "携带退货单到指定快递点寄回",
            "寄回地址：广东省深圳市龙华区xxx",
        ],
        "shipping_address": "广东省深圳市龙华区xxx",
        "contact": "客服热线：400-xxx-xxxx",
    }

    instructions_text = "\n".join(
        [f"{i+1}. {inst}" for i, inst in enumerate(result["instructions"])]
    )

    return (
        f"退货申请已提交成功！\n"
        f"退货单号：{result['return_id']}\n"
        f"订单号：{result['order_id']}\n"
        f"退货原因：{result['reason']}\n"
        f"退货状态：{result['status']}\n\n"
        f"退货须知：\n{instructions_text}\n\n"
        f"退货地址：{result['shipping_address']}\n"
        f"如有疑问请联系：{result['contact']}"
    )
