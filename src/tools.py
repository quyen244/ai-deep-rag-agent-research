"""Retired direct-tool module.

Finance data now crosses the typed :class:`src.mcp.client.FinanceMCPClient`
boundary. Executors own calculations in ordinary Python and never receive
LangChain tool lists.
"""

from src.mcp.client import FinanceMCPClient

__all__ = ["FinanceMCPClient"]
