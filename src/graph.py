from langgraph.graph import StateGraph , START , END
from src.state import AgentState
from src.node import node_a , node_b
# 1. graph initialization 
graph = StateGraph(AgentState)

# 2. add node 

graph.add_node('node_a' ,node_a)
graph.add_node('node_b' , node_b)


# 3. flow definition : START -> node_a -> node_b -> END 

graph.add_edge(START , 'node_a')
graph.add_edge('node_a', 'node_b')
graph.add_edge('node_b', END)

# 4. graph compiler 
app = graph.compile()

# invoke 

initial_state = {'text' : '', 'count' : 0}
final_state = app.invoke(initial_state)


print(final_state)

