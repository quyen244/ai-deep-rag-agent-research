# # Node : is a Python function receiving State and return Updated state 
# from src.state import AgentState
# def node_a(state : AgentState) -> dict:
#     return {
#         'text' : state['text'] + 'a',
#         'count' : state.get('count', 0) + 1
#     }



# def node_b(state : AgentState) -> dict:
#     return {
#         'text' : state.get('text' , '') + 'b'
#     }


from typing import Dict , Any , List 
import re 
from datetime import datetime 
from src.state import AgentState


def create_research_plan(state : AgentState)-> Dict[str , Any]:
    """node 2 : create a plan"""

    print('[ Node 2 ] - Creating a plan ...')
    query = state['query']

    plan_parts = []

    for ticker in query['tickers']:
        for analysis_type in query['analysis_types']:
            plan_parts.append(f'Analyzing {analysis_type} for {ticker}')


    research_plan = '\n'.join(plan_parts)

    return {
        'research_plan' : research_plan,
        'current_step' : 'plan_created'
    }







