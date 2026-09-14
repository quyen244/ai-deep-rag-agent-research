"""Compact deterministic fixtures. Values are illustrative, not live market data."""

from types import MappingProxyType

AS_OF = "2026-09-01T00:00:00Z"

COMPANIES = MappingProxyType(
    {
        "AAPL": {
            "financials": {
                "fiscal_year": 2025,
                "revenue": 416_200.0,
                "gross_profit": 195_800.0,
                "operating_income": 130_400.0,
                "net_income": 101_900.0,
                "total_assets": 365_700.0,
                "total_liabilities": 294_100.0,
                "shareholders_equity": 71_600.0,
                "operating_cash_flow": 121_500.0,
                "free_cash_flow": 99_300.0,
            },
            "metrics": {
                "price_to_earnings": {"value": 31.8, "unit": "ratio"},
                "return_on_equity": {"value": 142.3, "unit": "percent"},
                "net_margin": {"value": 24.5, "unit": "percent"},
                "debt_to_equity": {"value": 1.87, "unit": "ratio"},
            },
            "sector": {
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "metrics": {
                    "median_price_to_earnings": {"value": 27.4, "unit": "ratio"},
                    "annual_growth": {"value": 7.6, "unit": "percent"},
                },
                "competitors": [
                    {"ticker": "MSFT", "name": "Microsoft", "market_cap_usd_billions": 3_850.0, "revenue_growth_percent": 15.2},
                    {"ticker": "GOOGL", "name": "Alphabet", "market_cap_usd_billions": 2_450.0, "revenue_growth_percent": 12.8},
                ],
            },
            "bars": [
                ["2026-04-01T00:00:00Z", 188.4, 202.1, 186.0, 198.2, 1_210_000_000],
                ["2026-05-01T00:00:00Z", 198.3, 205.4, 191.8, 203.9, 1_095_000_000],
                ["2026-06-01T00:00:00Z", 204.0, 216.7, 201.2, 214.1, 1_180_000_000],
                ["2026-07-01T00:00:00Z", 214.0, 226.9, 210.6, 224.6, 1_260_000_000],
                ["2026-08-01T00:00:00Z", 224.8, 232.5, 218.9, 229.7, 1_140_000_000],
                ["2026-09-01T00:00:00Z", 229.8, 236.4, 225.2, 233.1, 485_000_000],
            ],
            "news": [
                ["Services revenue reaches a new mock-data high", "2026-08-28T12:00:00Z", 0.64, ["services", "earnings"]],
                ["Device demand remains resilient in key markets", "2026-08-21T12:00:00Z", 0.31, ["demand", "hardware"]],
                ["Regulatory scrutiny creates App Store uncertainty", "2026-08-12T12:00:00Z", -0.42, ["regulation", "services"]],
            ],
        },
        "TSLA": {
            "financials": {
                "fiscal_year": 2025,
                "revenue": 112_600.0,
                "gross_profit": 20_900.0,
                "operating_income": 8_100.0,
                "net_income": 7_400.0,
                "total_assets": 136_800.0,
                "total_liabilities": 55_300.0,
                "shareholders_equity": 81_500.0,
                "operating_cash_flow": 16_200.0,
                "free_cash_flow": 6_800.0,
            },
            "metrics": {
                "price_to_earnings": {"value": 68.4, "unit": "ratio"},
                "return_on_equity": {"value": 9.5, "unit": "percent"},
                "net_margin": {"value": 6.6, "unit": "percent"},
                "debt_to_equity": {"value": 0.18, "unit": "ratio"},
            },
            "sector": {
                "sector": "Consumer Discretionary",
                "industry": "Automobile Manufacturers",
                "metrics": {
                    "median_price_to_earnings": {"value": 19.2, "unit": "ratio"},
                    "annual_growth": {"value": 5.1, "unit": "percent"},
                },
                "competitors": [
                    {"ticker": "TM", "name": "Toyota", "market_cap_usd_billions": 315.0, "revenue_growth_percent": 4.3},
                    {"ticker": "BYDDY", "name": "BYD", "market_cap_usd_billions": 180.0, "revenue_growth_percent": 22.4},
                ],
            },
            "bars": [
                ["2026-04-01T00:00:00Z", 271.0, 294.6, 238.2, 245.8, 2_640_000_000],
                ["2026-05-01T00:00:00Z", 245.5, 278.9, 232.6, 270.4, 2_330_000_000],
                ["2026-06-01T00:00:00Z", 270.8, 301.2, 259.7, 287.3, 2_510_000_000],
                ["2026-07-01T00:00:00Z", 287.0, 296.1, 248.4, 257.9, 2_820_000_000],
                ["2026-08-01T00:00:00Z", 258.1, 281.4, 241.3, 276.2, 2_290_000_000],
                ["2026-09-01T00:00:00Z", 276.4, 289.7, 266.8, 283.5, 910_000_000],
            ],
            "news": [
                ["Energy storage deployments expand in mock quarter", "2026-08-29T12:00:00Z", 0.58, ["energy", "growth"]],
                ["Vehicle pricing pressure persists across regions", "2026-08-20T12:00:00Z", -0.47, ["pricing", "competition"]],
                ["New manufacturing line begins pilot production", "2026-08-09T12:00:00Z", 0.22, ["manufacturing", "capacity"]],
            ],
        },
        "MSFT": {
            "financials": {
                "fiscal_year": 2025,
                "revenue": 281_700.0,
                "gross_profit": 193_400.0,
                "operating_income": 128_500.0,
                "net_income": 105_600.0,
                "total_assets": 556_300.0,
                "total_liabilities": 243_700.0,
                "shareholders_equity": 312_600.0,
                "operating_cash_flow": 136_900.0,
                "free_cash_flow": 91_200.0,
            },
            "metrics": {
                "price_to_earnings": {"value": 36.1, "unit": "ratio"},
                "return_on_equity": {"value": 38.7, "unit": "percent"},
                "net_margin": {"value": 37.5, "unit": "percent"},
                "debt_to_equity": {"value": 0.31, "unit": "ratio"},
            },
            "sector": {
                "sector": "Technology",
                "industry": "Systems Software",
                "metrics": {
                    "median_price_to_earnings": {"value": 32.7, "unit": "ratio"},
                    "annual_growth": {"value": 13.8, "unit": "percent"},
                },
                "competitors": [
                    {"ticker": "GOOGL", "name": "Alphabet", "market_cap_usd_billions": 2_450.0, "revenue_growth_percent": 12.8},
                    {"ticker": "ORCL", "name": "Oracle", "market_cap_usd_billions": 510.0, "revenue_growth_percent": 10.6},
                ],
            },
            "bars": [
                ["2026-04-01T00:00:00Z", 438.2, 461.9, 432.5, 458.7, 512_000_000],
                ["2026-05-01T00:00:00Z", 458.5, 476.3, 451.8, 472.6, 486_000_000],
                ["2026-06-01T00:00:00Z", 472.8, 493.4, 466.1, 489.2, 521_000_000],
                ["2026-07-01T00:00:00Z", 489.0, 511.8, 481.3, 506.4, 548_000_000],
                ["2026-08-01T00:00:00Z", 506.7, 528.1, 498.9, 521.7, 503_000_000],
                ["2026-09-01T00:00:00Z", 521.5, 532.6, 512.4, 527.3, 205_000_000],
            ],
            "news": [
                ["Cloud backlog expands on enterprise AI demand", "2026-08-27T12:00:00Z", 0.71, ["cloud", "AI"]],
                ["Security portfolio gains large public-sector contract", "2026-08-18T12:00:00Z", 0.49, ["security", "contracts"]],
                ["Capital spending outlook rises with data-center buildout", "2026-08-08T12:00:00Z", -0.18, ["capital expenditure", "cloud"]],
            ],
        },
    }
)

MACRO = MappingProxyType(
    {
        "US": {
            "policy_rate": {"value": 3.75, "unit": "percent"},
            "inflation_year_over_year": {"value": 2.6, "unit": "percent"},
            "unemployment_rate": {"value": 4.2, "unit": "percent"},
            "gdp_growth_annualized": {"value": 2.1, "unit": "percent"},
            "ten_year_treasury_yield": {"value": 4.05, "unit": "percent"},
        }
    }
)
