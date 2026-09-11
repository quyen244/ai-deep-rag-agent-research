"""Select a FastMCP client transport without changing executor-facing code."""

from pathlib import Path
import sys
from typing import TypeAlias

from fastmcp import FastMCP
from fastmcp.client.transports import StdioTransport

from src.core.config import Settings
from src.core.errors import ConfigurationError
from src.mcp.server import get_finance_server

ClientTransportTarget: TypeAlias = FastMCP | str | StdioTransport


def create_client_transport(
    settings: Settings,
    *,
    in_memory_server: FastMCP | None = None,
) -> ClientTransportTarget:
    if settings.mcp_transport == "memory":
        return in_memory_server or get_finance_server()
    if settings.mcp_transport == "http":
        if settings.mcp_url is None:
            raise ConfigurationError(
                "MCP URL is required for HTTP transport.",
                operation="mcp_transport_selection",
            )
        return str(settings.mcp_url)
    if settings.mcp_transport == "stdio":
        project_root = Path(__file__).resolve().parents[2]
        return StdioTransport(
            command=sys.executable,
            args=["-m", "src.mcp.main"],
            cwd=str(project_root),
        )
    raise ConfigurationError(
        "Unsupported MCP transport.",
        operation="mcp_transport_selection",
        context={"transport": settings.mcp_transport},
    )
