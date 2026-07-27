# AI Decision Engine

## Overview
The AI Decision Engine acts as the central orchestration layer for the AI-First CCMS backend. It sits between Entity Extraction and Tool Execution, separating the "planning" from the "doing." 

It determines:
- **What** the user wants to accomplish (based on intent).
- **What** information is missing (based on the `InteractionDraft`).
- **Which** tool should eventually execute.
- **When** to clarify vs. when to execute.

## Enums
- `AgentAction`: `RESPOND`, `CONTINUE`, `CLARIFY`, `EXECUTE_TOOL`.
- `ToolReadiness`: `NOT_APPLICABLE`, `NOT_READY`, `READY`.
- `AgentState`: `IDLE`, `COLLECTING_INFORMATION`, `WAITING_FOR_USER`, `READY_TO_EXECUTE`, `COMPLETED`.

## Decision Output
The Decision Engine returns a strongly-typed `DecisionOutput` Pydantic model:
- `action`: The next action for the agent.
- `tool_readiness`: Whether the selected tool is ready.
- `selected_tool`: The target tool to execute (if any).
- `clarification_message`: The user-facing message to ask for missing fields.
- `clarification_reason`: The structured internal reason for clarification.
- `required_missing_fields`: Critical fields missing for the tool.
- `optional_missing_fields`: Optional fields missing for the tool.
- `decision_confidence`: Confidence score of the decision engine.
- `next_state`: The new state of the agent based on the decision.

## Routing Flow
1. **Input Node**: Receives the user message.
2. **Intent Node**: Determines intent. If `conversation`, routes straight to response.
3. **Entity Extraction Node**: Merges extracted entities into the immutable `InteractionDraft`.
4. **Decision Node**: The Decision Engine inspects the updated draft and intent, then generates the `DecisionOutput`.
5. **Conditional Routing**:
   - `RESPOND`, `CLARIFY`, `CONTINUE` -> `response_node`.
   - `EXECUTE_TOOL` -> `tool_selection_node`.
6. **Tool Selection Node**: Builds the argument schema for the selected tool.
7. **Tool Execution Node**: Executes the tool.
8. **Response Node**: Formats the output for the user.

## Clarification Lifecycle
When required fields are missing, the Decision Engine sets `AgentAction.CLARIFY`. The Graph routes this directly to the `response_node`, which issues the `clarification_message` to the user and enters `AgentState.WAITING_FOR_USER`. When the user replies, the cycle repeats. Once all fields are satisfied, the engine transitions to `AgentAction.EXECUTE_TOOL` and `AgentState.READY_TO_EXECUTE`.
