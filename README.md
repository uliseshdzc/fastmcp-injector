# FastMCP Injector

Dependency injection integration for [FastMCP](https://github.com/jlowin/fastmcp) using [injector](https://github.com/python-injector/injector).

Inspired by [fastapi-injector](https://github.com/macieyng/fastapi-injector).

## Installation

```bash
pip install fastmcp-injector
```

## Usage

```python
from fastmcp import FastMCP
from injector import Injector, inject, singleton

from fastmcp_injector import Injected, attach_injector


# Define your services
class Database:
    @inject
    def __init__(self):
        self._data = {"answer": 42}

    def query(self, q: str) -> str:
        return str(self._data)


# Set up DI and MCP
injector = Injector()
mcp = FastMCP()
attach_injector(mcp, injector)


# Use Injected[T] to declare dependencies — they won't appear in the tool schema
@mcp.tool()
def ask_database(question: str, db: Injected[Database]) -> str:
    return db.query(question)


if __name__ == "__main__":
    mcp.run()
```

`Injected[T]` parameters are resolved automatically from the injector container at call time. Only regular parameters (like `question: str`) are exposed in the MCP tool schema.

## How it works

1. `attach_injector(mcp, injector)` patches `mcp.tool()` to intercept tool registration.
2. Parameters annotated with `Injected[T]` are stripped from the function signature before FastMCP generates the tool schema.
3. At invocation time, a wrapper resolves those dependencies via `injector.get(T)` and injects them into the original function.

## License

MIT
