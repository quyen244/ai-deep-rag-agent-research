# tools.py - Phiên bản đã sửa với @tool
from langchain_core.tools import tool
from typing import Dict, Any, List
import json
from datetime import datetime

# ============================================
# TOOL 1: Lấy dữ liệu OHLCV
# ============================================
@tool
def get_ohlcv_data(ticker: str, timeframe: str = "1y") -> Dict[str, Any]:
    """
    Lấy dữ liệu giá OHLCV (Open, High, Low, Close, Volume) của một cổ phiếu.
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'AAPL', 'TSLA', 'MSFT')
        timeframe: Khung thời gian - '1d' (1 ngày), '1w' (1 tuần), '1m' (1 tháng), '3m' (3 tháng), '1y' (1 năm)
    
    Returns:
        Dict chứa dữ liệu giá và metadata
    """
    print(f"🔧 [TOOL] get_ohlcv_data called with ticker={ticker}, timeframe={timeframe}")
    
    # Mock data (sẽ thay bằng MCP call sau)
    mock_data = {
        "ticker": ticker,
        "timeframe": timeframe,
        "data": [
            {"date": "2024-01-01", "open": 180.0, "high": 185.0, "low": 178.0, "close": 184.0, "volume": 1000000},
            {"date": "2024-01-02", "open": 184.5, "high": 190.0, "low": 183.0, "close": 188.5, "volume": 1200000},
            {"date": "2024-01-03", "open": 188.0, "high": 192.0, "low": 186.0, "close": 190.5, "volume": 1100000},
        ],
        "source": "yahoo_finance (mock)",
        "fetched_at": datetime.now().isoformat()
    }
    
    return mock_data

# ============================================
# TOOL 2: Tính toán chỉ báo kỹ thuật
# ============================================
@tool
def calculate_technical_indicators(ohlcv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính toán các chỉ báo kỹ thuật từ dữ liệu OHLCV.
    
    Args:
        ohlcv_data: Dữ liệu OHLCV từ get_ohlcv_data
    
    Returns:
        Dict chứa các chỉ báo: RSI, MACD, Moving Averages, Trend
    """
    print(f"🔧 [TOOL] calculate_technical_indicators called")
    
    # Mock calculation
    closes = [d["close"] for d in ohlcv_data.get("data", [])]
    
    return {
        "rsi": 65.5,
        "macd": {
            "macd_line": 2.3,
            "signal_line": 1.8,
            "histogram": 0.5
        },
        "moving_averages": {
            "ma_20": 182.5,
            "ma_50": 178.2,
            "ma_200": 170.0
        },
        "trend": "uptrend" if closes and closes[-1] > closes[0] else "downtrend",
        "support_levels": [178.0, 170.0],
        "resistance_levels": [190.0, 200.0]
    }

# ============================================
# TOOL 3: Lấy báo cáo tài chính
# ============================================
@tool
def get_financial_statements(ticker: str) -> Dict[str, Any]:
    """
    Lấy báo cáo tài chính (Income Statement, Balance Sheet, Cash Flow) từ SEC EDGAR.
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'AAPL', 'TSLA')
    
    Returns:
        Dict chứa báo cáo tài chính
    """
    print(f"🔧 [TOOL] get_financial_statements called with ticker={ticker}")
    
    # Mock data
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
        "fiscal_year": 2024,
        "source": "sec_edgar"
    }

# ============================================
# TOOL 4: Tính toán chỉ số định giá
# ============================================
@tool
def calculate_fundamental_metrics(financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính toán các chỉ số định giá từ báo cáo tài chính.
    
    Args:
        financials: Dữ liệu báo cáo tài chính từ get_financial_statements
    
    Returns:
        Dict chứa các chỉ số: P/E, P/B, ROE, Margins
    """
    print(f"🔧 [TOOL] calculate_fundamental_metrics called")
    
    is_data = financials.get("income_statement", {})
    bs_data = financials.get("balance_sheet", {})
    
    revenue = is_data.get("revenue", 1)
    net_income = is_data.get("net_income", 1)
    equity = bs_data.get("shareholders_equity", 1)
    
    return {
        "pe_ratio": 28.5,
        "pb_ratio": 12.3,
        "roe": round((net_income / equity) * 100, 2),
        "gross_margin": round((is_data.get("gross_profit", 0) / revenue) * 100, 2),
        "operating_margin": round((is_data.get("operating_income", 0) / revenue) * 100, 2),
        "net_margin": round((net_income / revenue) * 100, 2),
        "debt_to_equity": round(bs_data.get("total_liabilities", 0) / equity, 2)
    }

# ============================================
# TOOL 5: Phân tích cảm xúc tin tức
# ============================================
@tool
def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """
    Phân tích cảm xúc thị trường từ tin tức về một cổ phiếu.
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'AAPL', 'TSLA')
    
    Returns:
        Dict chứa sentiment score và phân tích tin tức
    """
    print(f"🔧 [TOOL] get_news_sentiment called with ticker={ticker}")
    
    # Mock sentiment data
    return {
        "ticker": ticker,
        "sentiment_score": 0.65,  # -1 đến 1
        "sentiment_label": "Tích cực",
        "news_count": {
            "positive": 12,
            "negative": 3,
            "neutral": 5
        },
        "top_topics": [
            "Sản phẩm mới (iPhone 15, M4 chip)",
            "Tăng trưởng doanh thu quý mạnh",
            "Apple Intelligence - AI integration",
            "Tăng trưởng dịch vụ (Services)",
            "Cạnh tranh tại thị trường Trung Quốc"
        ],
        "summary": "Tin tức tích cực về sản phẩm mới và tăng trưởng doanh thu.",
        "source": "google_news"
    }

# ============================================
# Export tất cả tools dưới dạng list
# ============================================
# Danh sách tất cả tools để dễ dùng
ALL_TOOLS = [
    get_ohlcv_data,
    calculate_technical_indicators,
    get_financial_statements,
    calculate_fundamental_metrics,
    get_news_sentiment
]

# Danh sách theo nhóm
TECHNICAL_TOOLS = [get_ohlcv_data, calculate_technical_indicators]
FUNDAMENTAL_TOOLS = [get_financial_statements, calculate_fundamental_metrics]
SENTIMENT_TOOLS = [get_news_sentiment]