from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.shared.enums import AgentAction, ToolReadiness, AgentState, ToolName

class DecisionOutput(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    action: AgentAction = Field(..., description="The next action the agent should take.")
    tool_readiness: ToolReadiness = Field(..., description="Whether a tool is ready to be executed based on the current draft.")
    selected_tool: Optional[ToolName] = Field(None, description="The tool to execute, if applicable.")
    clarification_message: Optional[str] = Field(None, description="The message to show the user if clarification is needed.")
    clarification_reason: Optional[str] = Field(None, description="The internal reason for the clarification.")
    required_missing_fields: List[str] = Field(default_factory=list, description="Fields that are absolutely required for the selected tool but are missing.")
    optional_missing_fields: List[str] = Field(default_factory=list, description="Fields that are optional for the selected tool and are missing.")
    decision_confidence: float = Field(..., description="Confidence score of the decision engine (0.0 to 1.0).")
    next_state: AgentState = Field(..., description="The next state the agent should transition to.")
    reset_context: bool = Field(False, description="Flag indicating if the current interaction context should be reset.")
