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


async def test_injected_param_not_in_schema(mcp):
    @mcp.tool()
    def my_tool(question: str, svc: FakeService = Injected(FakeService)) -> str:
        return svc.greet(question)

    tool = await mcp.get_tool("my_tool")
    assert "question" in tool.parameters["properties"]
    assert "svc" not in tool.parameters["properties"]


async def test_tool_resolves_dependency(mcp):
    @mcp.tool()
    def my_tool(name: str, svc: FakeService = Injected(FakeService)) -> str:
        return svc.greet(name)

    result = await mcp.call_tool("my_tool", {"name": "World"})
    assert result.content[0].text == "Hello, World!"


async def test_tool_resolves_nested_dependency(mcp):
    @mcp.tool()
    def my_tool(value: str, svc: ServiceWithDep = Injected(ServiceWithDep)) -> str:
        return svc.process(value)

    result = await mcp.call_tool("my_tool", {"value": "Alice"})
    assert result.content[0].text == "Hello, Alice!"


async def test_async_tool(mcp):
    @mcp.tool()
    async def my_async_tool(name: str, svc: FakeService = Injected(FakeService)) -> str:
        return svc.greet(name)

    result = await mcp.call_tool("my_async_tool", {"name": "Async"})
    assert result.content[0].text == "Hello, Async!"


async def test_tool_without_injected_params(mcp):
    @mcp.tool()
    def plain_tool(x: int, y: int) -> int:
        return x + y

    tool = await mcp.get_tool("plain_tool")
    assert "x" in tool.parameters["properties"]
    assert "y" in tool.parameters["properties"]
    result = await mcp.call_tool("plain_tool", {"x": 2, "y": 3})
    assert result.content[0].text == "5"
