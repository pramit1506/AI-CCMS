import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.dependencies.graph import get_graph
from app.dependencies.db import get_db_session
from app.shared.responses import APIResponse
from app.core.config import settings
from app.tools.context import ToolExecutionContext
from app.llm.factory import get_llm_provider
from app.schemas.chat import ChatRequest, ConversationResponse
from app.utils.response_mapper import ConversationResponseMapper

router = APIRouter()

@router.post("/", response_model=APIResponse[ConversationResponse])
async def chat_endpoint(
    request: ChatRequest,
    graph: CompiledStateGraph = Depends(get_graph),
    db: AsyncSession = Depends(get_db_session)
) -> APIResponse[ConversationResponse]:
    request_id = str(uuid.uuid4())
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    input_state = {
        "conversation_id": conversation_id,
        "request_id": request_id,
        "user_message": request.user_message,
        "message_history": request.message_history,
        # Ephemeral fields are cleared on every turn
        "tool_status": None,
        "tool_result": None,
        "validation_errors": None,
        "llm_response": None,
        # Note: We omit selected_tool, tool_arguments, and metadata
        # so they are preserved by the MemorySaver checkpointer.
        "model_name": settings.DEFAULT_MODEL
    }
    
    tool_context = ToolExecutionContext(
        db=db,
        request_id=request_id,
        conversation_id=conversation_id,
        logger=logger,
        settings=settings,
        current_user=None,
        llm_provider=get_llm_provider()
    )
    
    config = {"configurable": {"tool_context": tool_context, "thread_id": conversation_id}}
    
    try:
        # Execute the graph asynchronously
        final_state = await graph.ainvoke(input_state, config=config)
        
        # Atomic metadata sync
        from datetime import datetime, timezone
        metadata = final_state.get("metadata", {})
        metadata["message_count"] = metadata.get("message_count", 0) + 1
        metadata["last_activity"] = datetime.now(timezone.utc).isoformat()
        
        draft = final_state.get("complaint_draft")
        if draft:
            metadata["active_customer"] = draft.customer_name or draft.customer_id
            
        tool_result = final_state.get("tool_result")
        if tool_result and isinstance(tool_result, dict) and "complaint_number" in tool_result:
            metadata["active_complaint"] = tool_result.get("complaint_number")
            if tool_result.get("id"):
                metadata["active_complaint_id"] = str(tool_result.get("id"))
            selected_tool = final_state.get("selected_tool")
            metadata["last_tool"] = selected_tool.value if hasattr(selected_tool, "value") else selected_tool
            
        if final_state.get("clarification_state"):
            metadata["clarification_state_status"] = final_state.get("clarification_state").status.value
        else:
            metadata["clarification_state_status"] = None
            
        await graph.aupdate_state(config, {"metadata": metadata})
        final_state["metadata"] = metadata
        
        # Map state to unified response model
        chat_response = ConversationResponseMapper.map_to_response(final_state)
        
        return APIResponse(
            success=True,
            message="Chat processed successfully",
            data=chat_response
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error executing chat workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during conversation processing: {str(e)}"
        )
