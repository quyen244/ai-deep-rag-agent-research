import os
import json
from langsmith import Client
from src.supervisor import build_financial_agent
from src.config import Config

def get_user_input():
    """
    Lấy input từ user (hiện đang dùng mock data)
    """
    # TODO: Uncomment khi muốn dùng interactive
    # print('[Step 1] : Ticker selection ')
    # for idx , ticker in enumerate(get_args(tickers)):
    #     print(f"     [{idx}]. {ticker}")
    # input_idx = int(input('Please choose the ticker by inputing the index: '))
    # input_ticker = get_args(tickers)[input_idx]
    # 
    # print('[Step 2] : Timeframe selection ')
    # for idx , timeframe in enumerate(get_args(timeframes)):
    #     print(f"     [{idx}]. {timeframe}")
    # input_idx = int(input('Please choose the timeframe by inputing the index: '))
    # input_timeframe = get_args(timeframes)[input_idx]
    # 
    # print('[Step 3] : Focus area selection ')
    # for idx , area in enumerate(get_args(focus_area)):
    #     print(f"     [{idx}]. {area}")
    # input_idx = int(input('Please choose the focus area by inputing the index: '))
    # input_focus_area = get_args(focus_area)[input_idx]
    # 
    # print('[Step 4] : Enter your question ')
    # input_questions = input('Enter the question: ')
    
    # Mock data cho test
    return {
        'tickers': ['AAPL'],
        'timeframes': ['1y'],  # ⭐ Đổi từ '1D' thành '1y' để có dữ liệu
        'analysis_types': ['technical', 'fundamental', 'sentiment'],
        'focus_area': ['profitability'],
        'questions': ['Phân tích kỹ thuật và cơ bản của cổ phiếu AAPL trong 1 năm qua']  # ⭐ Sửa thành string
    }

def run_financial_analysis(user_input):
    """
    Chạy phân tích tài chính với input từ user.
    """
    print(f"\n{'='*60}")
    print(f"📝 Câu hỏi: {user_input.get('questions', 'N/A')}")
    print(f"📊 Ticker: {user_input.get('tickers', [])}")
    print(f"📅 Timeframe: {user_input.get('timeframes', [])}")
    print(f"{'='*60}\n")
    
    # ⭐ QUAN TRỌNG: Tạo câu hỏi hoàn chỉnh từ input
    
    query = user_input.get('questions', '')
    tickers = user_input.get('tickers', [])
    timeframes = user_input.get('timeframes', [])
    analysis_types = user_input.get('analysis_types', [])

    if isinstance(query, list):
            query_text = query[0] if query else ""
    else:
            query_text = query
    # Tạo câu hỏi đầy đủ nếu chưa có
    if not query:
        query = f"Phân tích {', '.join(analysis_types)} của cổ phiếu {', '.join(tickers)} trong {', '.join(timeframes)}"
    
    # Khởi tạo state ban đầu
    initial_state = {
        "query": user_input,  # Giữ lại để tham khảo
        "messages": [
            {
                "role": "user",
                "content": query_text  # ⭐ Câu hỏi dạng string
            }
        ],
        "research_plan": None,
        "technical_analysis": None,
        "fundamental_analysis": None,
        "sentiment_analysis": None,
        "macro_analysis": None,
        "validation_errors": [],
        "missing_data": [],
        "final_report": None,
        "current_step": "initial",
        "errors": []
    }
    
    print("🔄 Đang xây dựng agent...\n")

    app = build_financial_agent()

    
        # ⭐ Chạy workflow - mọi thứ tự động được trace
    result = app.invoke(initial_state)
    
    # ⭐ Lấy run ID và in link LangSmith
    if Config.LANGCHAIN_TRACING_V2:
        try:
            # Get latest run from LangSmith
            client = Client()
            # Lấy runs gần nhất của project
            runs = client.list_runs(
                project_name=Config.LANGCHAIN_PROJECT,
                limit=1
            )
            for run in runs:
                run_id = run.id
                url = f"https://smith.langchain.com/projects/{Config.LANGCHAIN_PROJECT}/runs/{run_id}"
                print(f"\n🔗 Xem chi tiết trace: {url}")
        except Exception as e:
            print(f"⚠️ Could not get LangSmith link: {e}")
    
    # Extract outputs
    result = extract_agent_outputs(result)
    
    return result

def extract_agent_outputs(result: dict):
    """Extract outputs từ messages"""
    outputs = {
        "technical": None,
        "fundamental": None,
        "sentiment": None
    }
    
    supervisor_msgs = []
    
    if result.get("messages"):
        for msg in result["messages"]:
            if isinstance(msg, dict):
                name = msg.get("name", "")
                content = msg.get("content", "")
                
                if "technical" in name.lower() and content:
                    outputs["technical"] = content
                elif "fundamental" in name.lower() and content:
                    outputs["fundamental"] = content
                elif "sentiment" in name.lower() and content:
                    outputs["sentiment"] = content
                elif "supervisor" in name.lower() and content:
                    supervisor_msgs.append(content)
    
    result["technical_analysis"] = outputs["technical"]
    result["fundamental_analysis"] = outputs["fundamental"]
    result["sentiment_analysis"] = outputs["sentiment"]
    result["final_report"] = supervisor_msgs[-1] if supervisor_msgs else None
    
    return result

if __name__ == "__main__":
    user_input = get_user_input()
    result = run_financial_analysis(user_input)
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ")
    print("=" * 60)
    print(f"\nTechnical: {'✅' if result['technical_analysis'] else '❌'}")
    print(f"Fundamental: {'✅' if result['fundamental_analysis'] else '❌'}")
    print(f"Sentiment: {'✅' if result['sentiment_analysis'] else '❌'}")
