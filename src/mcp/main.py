"""CLI entry point for an optional standalone stdio finance MCP server."""

from src.mcp.server import get_finance_server


def main() -> None:
    get_finance_server().run(transport="stdio")


if __name__ == "__main__":
    main()
    




