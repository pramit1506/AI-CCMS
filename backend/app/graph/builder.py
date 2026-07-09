from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import GraphState
from app.graph.nodes import input_node, intent_node, entity_extraction_node, decision_node, tool_selection_node, tool_execution_node, response_node, output_node
from app.graph.router import route_after_intent, route_after_tool_selection, route_after_decision

def build_graph():
    """Compile and return the LangGraph workflow."""
    builder = StateGraph(GraphState)
    
    # Add nodes
    builder.add_node("input_node", input_node)
    builder.add_node("intent_node", intent_node)
    builder.add_node("entity_extraction_node", entity_extraction_node)
    builder.add_node("decision_node", decision_node)
    builder.add_node("tool_selection_node", tool_selection_node)
    builder.add_node("tool_execution_node", tool_execution_node)
    builder.add_node("response_node", response_node)
    builder.add_node("output_node", output_node)
    
    # Define edges
    builder.set_entry_point("input_node")
    builder.add_edge("input_node", "intent_node")
    
    # Conditional routing after intent
    builder.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "response_node": "response_node",
            "entity_extraction_node": "entity_extraction_node"
        }
    )
    
    # After entity extraction, always go to decision_node
    builder.add_edge("entity_extraction_node", "decision_node")
    
    # Conditional routing after decision
    builder.add_conditional_edges(
        "decision_node",
        route_after_decision,
        {
            "response_node": "response_node",
            "tool_selection_node": "tool_selection_node"
        }
    )
    
    # Conditional routing after tool selection
    builder.add_conditional_edges(
        "tool_selection_node",
        route_after_tool_selection,
        {
            "response_node": "response_node",
            "tool_execution_node": "tool_execution_node"
        }
    )
    
    builder.add_edge("tool_execution_node", "response_node")
    builder.add_edge("response_node", "output_node")
    builder.add_edge("output_node", END)
    
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# Provide a compiled instance
graph = build_graph()
