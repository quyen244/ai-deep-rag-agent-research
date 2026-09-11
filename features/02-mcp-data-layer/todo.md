# MCP mock data layer tasks

## Contract

- [x] Draft MCP/provider boundary and tool contracts.
- [ ] Approve supported mock tickers and in-memory MVP transport.

## Implementation

- [ ] Define provider protocols and tool response schemas.
- [ ] Add distinct compact fixtures for AAPL, TSLA, and MSFT.
- [ ] Implement mock market, company, news, macro, and sector providers.
- [ ] Replace demo FastMCP tools with six finance tools.
- [ ] Implement async MCP client adapter and error translation.
- [ ] Add configurable transport factory and observability hooks.
- [ ] Remove obsolete MCP demo client and duplicated command notes.

## Verification

- [ ] Test every provider and MCP tool through the client boundary.
- [ ] Test unknown ticker, invalid timeframe, provider failure, and malformed response.
- [ ] Verify ticker outputs are distinct and deterministic.
- [ ] Record evidence in `reports/02-mcp-data-layer-progress.md`.
