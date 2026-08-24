# Node : is a Python function receiving State and return Updated state 
from src.state import AgentState
def node_a(state : AgentState) -> dict:
    return {
        'text' : state['text'] + 'a',
        'count' : state.get('count', 0) + 1
    }



def node_b(state : AgentState) -> dict:
    return {
        'text' : state.get('text' , '') + 'b'
    }








