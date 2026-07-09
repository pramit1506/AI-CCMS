from langgraph.graph.state import CompiledStateGraph
from app.graph.builder import graph

def get_graph() -> CompiledStateGraph:
    """Dependency to provide the compiled LangGraph instance."""
    return graph
