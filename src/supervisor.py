# supervisor.py
from langgraph_supervisor import create_supervisor
from langgraph.graph import StateGraph, END, START
from langsmith import traceable
from langsmith.wrappers import wrap_openai

from src.state import AgentState
from src.agent import (
    create_technical_agent,
    create_fundamental_agent,
    create_sentiment_agent
)
from src.node import create_research_plan
from .config import Config

def get_llm():
    """Khởi tạo LLM với LangSmith tracing"""
    
    from openai import OpenAI
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=Config.OPENROUTER_API_KEY,
        timeout=120,  # ✅ Tăng timeout
        max_retries=3,
        model=Config.MODEL_NAME,
                temperature=Config.temperature,
                max_tokens=4096,
                openrouter_api_key=Config.OPENROUTER_API_KEY,
                timeout=120,  # ✅ Tăng timeout
                max_retries=3,  # ✅ Thêm retry
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Financial Analysis Agent",
                }
    )
    
    if Config.LANGCHAIN_TRACING_V2:
        from langsmith.wrappers import wrap_openai
        client = wrap_openai(client)

    return client
    
    

@traceable(name="build_supervisor", run_type="chain")
def build_supervisor_with_tracing():
    """Build supervisor với tracing"""
    model = get_llm()
    
    technical_agent = create_technical_agent(model)
    fundamental_agent = create_fundamental_agent(model)
    sentiment_agent = create_sentiment_agent(model)
    
    supervisor_graph = create_supervisor(
        agents=[technical_agent, fundamental_agent, sentiment_agent],
        model=model,
        prompt="""
        ⚠️ QUY TRÌNH BẮT BUỘC:
        
        Bạn là Giám đốc phân tích tài chính.
        Điều phối các chuyên gia:
        - 'technical_analyst': Phân tích kỹ thuật - BẮT BUỘC gọi get_ohlcv_data và calculate_technical_indicators
        - 'fundamental_analyst': Phân tích cơ bản - BẮT BUỘC gọi get_financial_statements và calculate_fundamental_metrics
        - 'sentiment_analyst': Phân tích cảm xúc - BẮT BUỘC gọi get_news_sentiment
        
        KHÔNG TỰ SUY LUẬN NẾU CHƯA GỌI TOOL.
        """
    )
    
    return supervisor_graph.compile()

def build_financial_agent():
    """Xây dựng workflow hoàn chỉnh"""
    
    print("🔄 Building financial agent...")
    
    # Build supervisor với tracing
    supervisor_runnable = build_supervisor_with_tracing()
    
    # Tạo workflow
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("create_plan", create_research_plan)
    workflow.add_node("supervisor", supervisor_runnable)
    
    # Flow
    workflow.add_edge(START, "create_plan")
    workflow.add_edge("create_plan", "supervisor")
    workflow.add_edge("supervisor", END)
    
    print("✅ Workflow ready!")
    return workflow.compile()