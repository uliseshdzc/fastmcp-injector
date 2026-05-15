import inspect
from functools import wraps
from typing import Type, TypeVar

from fastmcp import FastMCP
from injector import Injector

T = TypeVar("T")


class _InjectedMarker:
    def __init__(self, interface: type):
        self.interface = interface


def Injected(interface: Type[T]) -> T:  # pylint: disable=invalid-name
    """Marks a parameter for dependency injection. Usage: param: Database = Injected(Database)"""
    return _InjectedMarker(interface)


def attach_injector(mcp: FastMCP, injector: Injector):
    """Patches mcp.tool() to auto-resolve Injected(T) parameters from the injector."""
    original_tool = mcp.tool

    def patched_tool(*args, **kwargs):
        original_decorator = original_tool(*args, **kwargs)

        def decorator(func):
            sig = inspect.signature(func)

            injected_params = {}
            tool_params = []

            for name, param in sig.parameters.items():
                if isinstance(param.default, _InjectedMarker):
                    injected_params[name] = param.default.interface
                    continue
                tool_params.append(param)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def wrapper(**kw):
                    for p_name, p_type in injected_params.items():
                        kw[p_name] = injector.get(p_type)
                    return await func(**kw)

            else:

                @wraps(func)
                def wrapper(**kw):
                    for p_name, p_type in injected_params.items():
                        kw[p_name] = injector.get(p_type)
                    return func(**kw)

            wrapper.__signature__ = sig.replace(parameters=tool_params)
            annotations = getattr(func, "__annotations__", {})
            wrapper.__annotations__ = {
                p.name: annotations[p.name]
                for p in tool_params
                if p.name in annotations
            }
            if "return" in annotations:
                wrapper.__annotations__["return"] = annotations["return"]

            return original_decorator(wrapper)

        return decorator

    mcp.tool = patched_tool
