import os
from dotenv import load_dotenv
from src.supervisor import build_finanial_agent
import json
from src.mockData import (
    tickers, 
    timeframes, 
    focus_area, 
    analysis_types
)
from typing import get_args, Dict, Any
import logging

# Load environment variables
load_dotenv()

# Cấu hình logging để debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def run_financial_analysis(user_input: Dict[str, Any]):
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
    
    # Tạo câu hỏi đầy đủ nếu chưa có
    if not query:
        query = f"Phân tích {', '.join(analysis_types)} của cổ phiếu {', '.join(tickers)} trong {', '.join(timeframes)}"
    
    # Khởi tạo state ban đầu
    initial_state = {
        "query": user_input,  # Giữ lại để tham khảo
        "messages": [
            {
                "role": "user",
                "content": query[0]  # ⭐ Câu hỏi dạng string
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
    
    # Build agent
    app = build_finanial_agent()
    
    print("🔄 Đang chạy phân tích...\n")
    
    # Chạy workflow
    result = app.invoke(initial_state)
    
    # ⭐ Extract outputs từ messages
    result = extract_agent_outputs(result)
    
    # In kết quả
    print_analysis_result(result)
    
    # ⭐ In chi tiết từng agent output
    print_agent_outputs_detail(result)
    
    # Lưu kết quả ra file
    save_result_to_json(result)
    
    return result

def extract_agent_outputs(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trích xuất output của từng agent từ messages.
    """
    print("\n🔍 Đang trích xuất output từ các agent...")
    
    agent_outputs = {
        "technical": None,
        "fundamental": None,
        "sentiment": None,
        "macro": None
    }
    
    final_report = None
    supervisor_messages = []
    
    if result.get("messages"):
        for msg in result["messages"]:
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
                name = msg.get("name", "")
                msg_type = msg.get("type", "")
                
                # Debug: in từng message
                if content and len(str(content)) > 10:
                    print(f"  📨 [{role}] {name}: {str(content)[:50]}...")
                
                # Tìm output của từng agent theo name
                if name == "technical_analyst":
                    agent_outputs["technical"] = content
                    print(f"  ✅ Found Technical Analysis ({len(str(content))} chars)")
                elif name == "fundamental_analyst":
                    agent_outputs["fundamental"] = content
                    print(f"  ✅ Found Fundamental Analysis ({len(str(content))} chars)")
                elif name == "sentiment_analyst":
                    agent_outputs["sentiment"] = content
                    print(f"  ✅ Found Sentiment Analysis ({len(str(content))} chars)")
                elif name == "macro_analyst":
                    agent_outputs["macro"] = content
                    print(f"  ✅ Found Macro Analysis ({len(str(content))} chars)")
                
                # Lưu supervisor messages
                if name == "supervisor":
                    supervisor_messages.append(content)
    
    # Lấy tin nhắn cuối cùng của supervisor làm báo cáo
    if supervisor_messages:
        final_report = supervisor_messages[-1]
        print(f"  ✅ Found Final Report ({len(str(final_report))} chars)")
    
    # Cập nhật result
    result["technical_analysis"] = agent_outputs["technical"]
    result["fundamental_analysis"] = agent_outputs["fundamental"]
    result["sentiment_analysis"] = agent_outputs["sentiment"]
    result["macro_analysis"] = agent_outputs["macro"]
    result["final_report"] = final_report
    
    print("✅ Đã trích xuất xong output từ các agent\n")
    
    return result

def print_analysis_result(result: Dict[str, Any]):
    """
    In kết quả phân tích tổng quan.
    """
    print(f"\n{'='*60}")
    print(f"📊 KẾT QUẢ PHÂN TÍCH")
    print(f"{'='*60}")
    
    # 1. Parsed Query
    print(f"\n📋 Parsed Query:")
    parsed = result.get("parsed_query", {})
    if parsed:
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        print("  (Chưa được parse)")
    
    # 2. Research Plan
    print(f"\n📋 Research Plan:")
    print(result.get('research_plan', 'Không có plan'))
    
    # 3. Agent Outputs Summary
    print(f"\n{'─'*60}")
    print(f"📊 AGENT OUTPUTS SUMMARY")
    print(f"{'─'*60}")
    
    for agent_name, field in [
        ("Technical", "technical_analysis"),
        ("Fundamental", "fundamental_analysis"),
        ("Sentiment", "sentiment_analysis"),
        ("Macro", "macro_analysis")
    ]:
        content = result.get(field)
        status = "✅ CÓ" if content else "❌ KHÔNG"
        length = len(str(content)) if content else 0
        print(f"  {agent_name}: {status} ({length} chars)")

def print_agent_outputs_detail(result: Dict[str, Any]):
    """
    In chi tiết output của từng agent.
    """
    print(f"\n{'='*60}")
    print(f"📄 CHI TIẾT OUTPUT TỪNG AGENT")
    print(f"{'='*60}")
    
    # Technical Analysis
    print(f"\n{'─'*60}")
    print(f"📈 TECHNICAL ANALYSIS:")
    print(f"{'─'*60}")
    tech = result.get("technical_analysis")
    if tech:
        print(tech)
    else:
        print("❌ Không có dữ liệu")
    
    # Fundamental Analysis
    print(f"\n{'─'*60}")
    print(f"📊 FUNDAMENTAL ANALYSIS:")
    print(f"{'─'*60}")
    fund = result.get("fundamental_analysis")
    if fund:
        print(fund)
    else:
        print("❌ Không có dữ liệu")
    
    # Sentiment Analysis
    print(f"\n{'─'*60}")
    print(f"📰 SENTIMENT ANALYSIS:")
    print(f"{'─'*60}")
    sent = result.get("sentiment_analysis")
    if sent:
        print(sent)
    else:
        print("❌ Không có dữ liệu")
    
    # Final Report
    print(f"\n{'='*60}")
    print(f"📄 FINAL REPORT (Tổng hợp từ Supervisor):")
    print(f"{'='*60}")
    report = result.get("final_report")
    if report:
        print(report)
    else:
        print("❌ Không có báo cáo tổng hợp")
    
    print(f"\n{'='*60}\n")

def save_result_to_json(result: Dict[str, Any]):
    """
    Lưu kết quả ra file JSON.
    """
    try:
        # Chuyển đổi các object không serializable
        def json_serializable(obj):
            if hasattr(obj, '__dict__'):
                return str(obj)
            return obj
        
        with open("analysis_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=json_serializable)
        print("✅ Đã lưu kết quả vào analysis_result.json")
    except Exception as e:
        print(f"⚠️ Không thể lưu JSON: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 FINANCIAL ANALYSIS AGENT")
    print("=" * 60 + "\n")
    
    # Lấy input từ user
    user_input = get_user_input()
    
    # Chạy phân tích
    result = run_financial_analysis(user_input)
    
    # In summary
    print("\n" + "=" * 60)
    print("✅ PHÂN TÍCH HOÀN TẤT")
    print("=" * 60)
    print(f"📊 Xem chi tiết trong file: analysis_result.json")