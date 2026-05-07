import inspect
from functools import wraps
from typing import Annotated, get_args, get_origin, get_type_hints

from fastmcp import FastMCP
from injector import Injector


class _Dependency:
    pass


class Injected:
    """Type annotation for injected dependencies. Usage: param: Injected[MyService]"""

    def __class_getitem__(cls, item):
        return Annotated[item, _Dependency()]


def attach_injector(mcp: FastMCP, injector: Injector):
    """Patches mcp.tool() to auto-resolve Injected[T] parameters from the injector."""
    original_tool = mcp.tool

    def patched_tool(*args, **kwargs):
        original_decorator = original_tool(*args, **kwargs)

        def decorator(func):
            hints = get_type_hints(func, include_extras=True)
            sig = inspect.signature(func)

            injected_params = {}
            tool_params = []

            for name, param in sig.parameters.items():
                hint = hints.get(name)
                if hint and get_origin(hint) is Annotated:
                    metadata = get_args(hint)
                    if any(isinstance(m, _Dependency) for m in metadata):
                        injected_params[name] = metadata[0]
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
            wrapper.__annotations__ = {
                p.name: hints[p.name] for p in tool_params if p.name in hints
            }
            if "return" in hints:
                wrapper.__annotations__["return"] = hints["return"]

            return original_decorator(wrapper)

        return decorator

    mcp.tool = patched_tool
