from langchain_openrouter import ChatOpenRouter
from langgraph_supervisor import create_supervisor
from langgraph.graph import StateGraph , START , END 
from langgraph.prebuilt import create_react_agent


from src.state import AgentState
from src.agent import (
    create_technical_agent,
    create_fundamental_agent,
    create_sentiment_agent
)
from src.node import create_research_plan
from src.config import Config


def build_finanial_agent():
    """create the entire workflow"""

    # 1. initialize LLM 
    print('Creating llm ...')

    model = ChatOpenRouter(
        model=Config.MODEL_NAME,
        temperature=Config.temperature,
        max_retries=2,
        max_tokens=4096,  # Chỉ dùng max_tokens là đủ
        openrouter_api_key=Config.OPENROUTER_API_KEY,
    )

    # 2. create sub agents 
    print('Creating agents ...')
    technical_agent = create_technical_agent(model)
    fundamental_agent = create_fundamental_agent(model)
    sentiment_agent = create_sentiment_agent(model)


    # 3. Tạo Supervisor
    print('Creating supervisor ...')
    supervisor_graph = create_supervisor(
        agents=[technical_agent, fundamental_agent, sentiment_agent],
        model=model,
        prompt="""
        Bạn là Giám đốc phân tích tài chính tại một quỹ đầu tư lớn.
        
        Nhiệm vụ của bạn: Điều phối nhóm chuyên gia để trả lời câu hỏi về thị trường.
        Nhóm của bạn gồm:
        - 'technical_analyst': Chuyên gia phân tích kỹ thuật
        - 'fundamental_analyst': Chuyên gia phân tích cơ bản  
        - 'sentiment_analyst': Chuyên gia phân tích cảm xúc thị trường
        
        Quy trình làm việc:
        1. Xác định cần phân tích khía cạnh nào dựa trên câu hỏi
        2. Giao việc cho các chuyên gia phù hợp (song song)
        3. Tổng hợp kết quả thành câu trả lời cuối cùng
        
        Lưu ý: 
        - Không đưa ra lời khuyên mua/bán cụ thể
        - Luôn trích dẫn nguồn số liệu
        - Nếu dữ liệu không đủ, thông báo rõ
        """
    )
    supervisor_runnable = supervisor_graph.compile()

    print('Creating workflow ...')
    # 4. workflow 
    workflow = StateGraph(AgentState)
    
    # add nodes 
    workflow.add_node('create_plan', create_research_plan)
    print('Plan is added ...')
    # add supervisor 
    workflow.add_node('supervisor' , supervisor_runnable)
    print('Supervisor is added ...')

    # flow definition 
    workflow.add_edge(START , 'create_plan')
    workflow.add_edge('create_plan' , 'supervisor')
    workflow.add_edge('supervisor' , END)


    # compiler 
    app = workflow.compile()

    return app 






