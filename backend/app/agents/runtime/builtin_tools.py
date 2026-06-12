from app.agents.runtime.tool_registry import register_tool
from app.agents.tools.order import query_order_status
from app.agents.tools.logistics import query_logistics
from app.agents.tools.refund import submit_refund
from app.agents.tools.return_ import submit_return
from app.agents.tools.user_info import query_user_info
from app.agents.tools.user_orders import query_user_orders


@register_tool("查询订单状态")
async def _query_order_status(args: dict) -> str:
    return await query_order_status(args)


@register_tool("查询物流信息")
async def _query_logistics(args: dict) -> str:
    return await query_logistics(args)


@register_tool("发起退款申请")
async def _submit_refund(args: dict) -> str:
    return await submit_refund(args)


@register_tool("发起退货申请")
async def _submit_return(args: dict) -> str:
    return await submit_return(args)


@register_tool("查询用户信息")
async def _query_user_info(args: dict) -> str:
    return await query_user_info(args)


@register_tool("查询历史订单")
async def _query_user_orders(args: dict) -> str:
    return await query_user_orders(args)
