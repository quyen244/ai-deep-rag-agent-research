from typing_extensions import TypedDict
from  typing import List , Dict , Optional , Any , Annotated
from datetime import datetime
from langgraph.graph.message import add_messages

 # class AgentState(TypedDict):
#     """Workflow common state"""
#     text : str 
#     count : int 

from langchain_core.messages import BaseMessage



class Query(TypedDict):
    """data structure after parsing question"""
    tickers : List[str] # ['AAPL', 'TSLA']v
    timeframes : List[str]  # ['1y', '3m']
    analysis_types : List[str]   # ['technical', 'fundamental', 'sentiment']
    focus_area : Optional[List[str]]  # ['profitability', 'growth']
    questions : List[str] # specific question 


class AgentState(TypedDict):
    """main state of the entire workflow"""
    # input layer
    query : Query


    # orchestration layer 
    messages : Annotated[List[BaseMessage] , add_messages] # message history 
    research_plan : Optional[str]


    # agent execution layer 
    technical_analysis : Optional[Dict[str , Any]]
    fundamental_analysis : Optional[Dict[str , Any]]
    sentiment_analysis : Optional[Dict[str , Any]]
    macro_analysis : Optional[Dict[str , Any]]

    # Validation layer 

    validation_errors : Optional[List[str]]
    missing_data : Optional[List[str]]

    # synthesis layer 
    final_report : Optional[str]

    # metadata 
    current_step : str # current step 
    errors : Optional[List[str]]
