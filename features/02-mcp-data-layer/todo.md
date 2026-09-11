# MCP mock data layer tasks

## Contract

- [x] Draft MCP/provider boundary and tool contracts.
- [x] Approve supported mock tickers and in-memory MVP transport.

## Implementation

- [x] Define provider protocols and tool response schemas.
- [x] Add distinct compact fixtures for AAPL, TSLA, and MSFT.
- [x] Implement mock market, company, news, macro, and sector providers.
- [x] Replace demo FastMCP tools with six finance tools.
- [x] Implement async MCP client adapter and error translation.
- [x] Add configurable transport factory and observability hooks.
- [x] Remove obsolete MCP demo client and duplicated command notes.

## Verification

- [x] Test every provider and MCP tool through the client boundary.
- [x] Test unknown ticker, invalid timeframe, provider failure, and malformed response.
- [x] Verify ticker outputs are distinct and deterministic.
- [x] Record evidence in `reports/02-mcp-data-layer-progress.md`.
