from app.graph.state import GraphState
from app.shared.enums import AgentAction
from loguru import logger

def route_after_intent(state: GraphState) -> str:
    """
    Route to the next node based on the detected intent.
    """
    intent = state.get("detected_intent")
    logger.info(f"[{state.get('request_id')}] Router decision (route_after_intent): intent='{intent}'")
    
    if intent == "conversation":
        next_node = "response_node"
    else:
        next_node = "entity_extraction_node"
        
    logger.info(f"[{state.get('request_id')}] Router Next Node: {next_node}")
    return next_node

def route_after_tool_selection(state: GraphState) -> str:
    """
    Route based on tool selection success.
    """
    tool = state.get("selected_tool")
    
    logger.info(f"[{state.get('request_id')}] Router decision (route_after_tool_selection): selected_tool={tool}")
    
    if not tool:
        next_node = "response_node"
    else:
        next_node = "tool_execution_node"
        
    logger.info(f"[{state.get('request_id')}] Router Next Node: {next_node}")
    return next_node

def route_after_decision(state: GraphState) -> str:
    """
    Route based on the decision engine's output.
    """
    decision = state.get("decision_output")
    
    if not decision:
        logger.warning(f"[{state.get('request_id')}] No decision output found, defaulting to response_node")
        return "response_node"
        
    action = decision.action
    logger.info(f"[{state.get('request_id')}] Router decision (route_after_decision): action='{action}'")
    
    if action == AgentAction.EXECUTE_TOOL:
        next_node = "tool_selection_node"
    else:
        # RESPOND, CONTINUE, CLARIFY all go to response_node
        next_node = "response_node"
        
    logger.info(f"[{state.get('request_id')}] Router Next Node: {next_node}")
    return next_node

