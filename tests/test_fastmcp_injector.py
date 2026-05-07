import pytest
from fastmcp import FastMCP
from injector import Injector, inject

from fastmcp_injector import Injected, attach_injector


class FakeService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class ServiceWithDep:
    @inject
    def __init__(self, fake: FakeService):
        self.fake = fake

    def process(self, value: str) -> str:
        return self.fake.greet(value)


@pytest.fixture
def injector():
    return Injector()


@pytest.fixture
def mcp(injector):
    server = FastMCP("test")
    attach_injector(server, injector)
    return server


def test_injected_param_not_in_schema(mcp):
    @mcp.tool()
    def my_tool(question: str, svc: Injected[FakeService]) -> str:
        return svc.greet(question)

    tools = mcp._tool_manager._tools
    tool = tools["my_tool"]
    params = tool.fn_metadata.arg_model.model_fields
    assert "question" in params
    assert "svc" not in params


def test_tool_resolves_dependency(mcp):
    @mcp.tool()
    def my_tool(name: str, svc: Injected[FakeService]) -> str:
        return svc.greet(name)

    tool = mcp._tool_manager._tools["my_tool"]
    result = tool.fn(name="World")
    assert result == "Hello, World!"


def test_tool_resolves_nested_dependency(mcp):
    @mcp.tool()
    def my_tool(value: str, svc: Injected[ServiceWithDep]) -> str:
        return svc.process(value)

    tool = mcp._tool_manager._tools["my_tool"]
    result = tool.fn(value="Alice")
    assert result == "Hello, Alice!"


@pytest.mark.asyncio
async def test_async_tool(mcp):
    @mcp.tool()
    async def my_async_tool(name: str, svc: Injected[FakeService]) -> str:
        return svc.greet(name)

    tool = mcp._tool_manager._tools["my_async_tool"]
    result = await tool.fn(name="Async")
    assert result == "Hello, Async!"


def test_tool_without_injected_params(mcp):
    @mcp.tool()
    def plain_tool(x: int, y: int) -> int:
        return x + y

    tool = mcp._tool_manager._tools["plain_tool"]
    params = tool.fn_metadata.arg_model.model_fields
    assert "x" in params
    assert "y" in params
    result = tool.fn(x=2, y=3)
    assert result == 5
