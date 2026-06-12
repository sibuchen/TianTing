from typing import Any, Callable, Awaitable

_tool_handlers: dict[str, Callable[..., Awaitable[str]]] = {}


def register_tool(name: str):
    def decorator(func: Callable[..., Awaitable[str]]):
        _tool_handlers[name] = func
        return func
    return decorator


def get_tool_handler(name: str) -> Callable[..., Awaitable[str]] | None:
    return _tool_handlers.get(name)


async def execute_builtin_tool(tool_config_id: str, tool_name: str, args: dict[str, Any]) -> str:
    handler = get_tool_handler(tool_name)
    if handler:
        return await handler(args)
    return f"工具 {tool_name} 暂未实现"
