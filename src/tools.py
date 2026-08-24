from typing import Dict , Any , List 
import json 

# technical 
def get_ohlcv_data(ticker , timeframe : str = '1D') -> Dict[str , Any]:
    """
    Mô phỏng: Lấy dữ liệu OHLCV.
    Thực tế sẽ gọi MCP Server (Yahoo Finance, Infoway...)
    """
    # Giả lập dữ liệu
    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "data": [
            {"date": "2024-01-01", "open": 180.0, "high": 185.0, "low": 178.0, "close": 184.0, "volume": 1000000},
            {"date": "2024-01-02", "open": 184.5, "high": 190.0, "low": 183.0, "close": 188.5, "volume": 1200000}
        ],
        "source": "yahoo_finance"
    }


def calculate_technical_indicators(ohlcv: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mô phỏng: Tính các chỉ báo kỹ thuật.
    """
    closes = [d["close"] for d in ohlcv["data"]]
    return {
        "rsi": 65.5,
        "macd": {
            "macd": 2.3,
            "signal": 1.8,
            "histogram": 0.5
        },
        "moving_averages": {
            "ma_20": 182.5,
            "ma_50": 178.2,
            "ma_200": 170.0
        },
        "trend": "uptrend" if closes[-1] > closes[0] else "downtrend"
    }

# fundamental
def get_financial_statements(ticker: str) -> Dict[str, Any]:
    """
    Mô phỏng: Lấy báo cáo tài chính.
    """
    return {
        "ticker": ticker,
        "income_statement": {
            "revenue": 383285,  # triệu USD
            "gross_profit": 169148,
            "operating_income": 114301,
            "net_income": 96995
        },
        "balance_sheet": {
            "total_assets": 352755,
            "total_liabilities": 290400,
            "shareholders_equity": 62355
        },
        "cash_flow": {
            "operating_cash_flow": 110543,
            "free_cash_flow": 98584
        },
        "source": "sec_edgar"
    }

def calculate_fundamental_metrics(financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính các chỉ số định giá.
    """
    is_data = financials["income_statement"]
    bs_data = financials["balance_sheet"]
    
    return {
        "pe_ratio": 28.5,  # Giả định
        "pb_ratio": 12.3,
        "roe": round((is_data["net_income"] / bs_data["shareholders_equity"]) * 100, 2),
        "gross_margin": round((is_data["gross_profit"] / is_data["revenue"]) * 100, 2),
        "operating_margin": round((is_data["operating_income"] / is_data["revenue"]) * 100, 2),
        "net_margin": round((is_data["net_income"] / is_data["revenue"]) * 100, 2)
    }

# sentiment

def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """
    Mô phỏng: Phân tích cảm xúc từ tin tức.
    """
    return {
        "ticker": ticker,
        "sentiment_score": 0.65,  # -1 đến 1, positive > 0
        "positive_news": 12,
        "negative_news": 3,
        "neutral_news": 5,
        "summary": "Tin tức tích cực về sản phẩm mới và tăng trưởng doanh thu.",
        "source": "google_news"
    }

# Tools list để đăng ký với LangGraph
tools = [
    get_ohlcv_data,
    calculate_technical_indicators,
    get_financial_statements,
    calculate_fundamental_metrics,
    get_news_sentiment
]