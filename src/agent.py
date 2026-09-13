from langchain_openrouter import ChatOpenRouter
from langgraph.prebuilt import create_react_agent
from src.tools import (
     TECHNICAL_TOOLS , SENTIMENT_TOOLS , FUNDAMENTAL_TOOLS
)
from src.config import Config


def create_technical_agent(model : ChatOpenRouter):
    
    return create_react_agent(
        model=model,
        tools=TECHNICAL_TOOLS,
        name="technical_analyst",
        prompt="""
        Bạn là chuyên gia phân tích kỹ thuật tài chính với 15 năm kinh nghiệm.
        Nhiệm vụ của bạn:
        1. Sử dụng get_ohlcv_data để lấy dữ liệu giá
        2. Sử dụng calculate_technical_indicators để tính chỉ báo
        3. Đưa ra nhận xét về xu hướng và điểm vào/ra tiềm năng
        
        Trả về phân tích có cấu trúc bao gồm:
        - Xu hướng chính (tăng/giảm/sideways)
        - Các mức hỗ trợ/kháng cự
        - Tín hiệu từ các chỉ báo (RSI, MACD, MA)
        - Khối lượng giao dịch
        """
    )


def create_fundamental_agent(model: ChatOpenRouter):
    """Agent phân tích cơ bản"""
    
    return create_react_agent(
        model=model,
        tools=FUNDAMENTAL_TOOLS,
        name="fundamental_analyst",
        prompt="""
        Bạn là chuyên gia phân tích cơ bản từng làm tại các quỹ đầu tư hàng đầu.
        Nhiệm vụ của bạn:
        1. Sử dụng get_financial_statements để lấy báo cáo tài chính
        2. Sử dụng calculate_fundamental_metrics để tính chỉ số định giá
        3. So sánh với trung bình ngành
        
        Trả về phân tích bao gồm:
        - Sức khỏe tài chính (thanh khoản, nợ)
        - Khả năng sinh lời (biên lợi nhuận, ROE)
        - Định giá (P/E, P/B so với trung bình ngành)
        - Tăng trưởng doanh thu và lợi nhuận
        """
    )

def create_sentiment_agent(model: ChatOpenRouter):
    """Agent phân tích cảm xúc thị trường"""
    
    return create_react_agent(
        model=model,
        tools=SENTIMENT_TOOLS,
        name="sentiment_analyst",
        prompt="""
        Bạn là chuyên gia phân tích tâm lý thị trường và tin tức.
        Nhiệm vụ của bạn:
        1. Sử dụng get_news_sentiment để lấy và phân tích tin tức
        2. Đánh giá cảm xúc tổng thể của thị trường
        
        Trả về phân tích bao gồm:
        - Sentiment score (-1 đến 1)
        - Số lượng tin positive/negative/neutral
        - Các chủ đề chính trong tin tức
        - Tác động tiềm năng đến giá cổ phiếu
        """
    )



