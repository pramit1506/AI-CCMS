from enum import Enum

class PlaceholderEnum(str, Enum):
    """
    Placeholder enum for future use.
    """
    PLACEHOLDER = "placeholder"


class InteractionStatus(str, Enum):
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class InteractionType(str, Enum):
    EMAIL = "EMAIL"
    IN_PERSON = "IN_PERSON"
    VIRTUAL = "VIRTUAL"
    PHONE = "PHONE"


class DraftStatus(str, Enum):
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    READY = "READY"
    CONFIRMED = "CONFIRMED"
    SAVED = "SAVED"

class AgentAction(str, Enum):
    RESPOND = "RESPOND"
    CONTINUE = "CONTINUE"
    CLARIFY = "CLARIFY"
    EXECUTE_TOOL = "EXECUTE_TOOL"

class ToolReadiness(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_READY = "NOT_READY"
    READY = "READY"

class AgentState(str, Enum):
    IDLE = "IDLE"
    COLLECTING_INFORMATION = "COLLECTING_INFORMATION"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    READY_TO_EXECUTE = "READY_TO_EXECUTE"
    COMPLETED = "COMPLETED"

class ToolName(str, Enum):
    LOG_INTERACTION = "log_interaction"
    EDIT_INTERACTION = "edit_interaction"
    GENERATE_FOLLOWUP = "generate_followup"
    SUMMARIZE_INTERACTION = "summarize_interaction"
    COMPLIANCE_CHECKER = "compliance_check"

class ConversationStatus(str, Enum):
    COLLECTING_INFORMATION = "COLLECTING_INFORMATION"
    AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    EXECUTING_TOOL = "EXECUTING_TOOL"
    COMPLETED = "COMPLETED"

class ClarificationLifecycle(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    RESOLVED = "RESOLVED"
    CLEARED = "CLEARED"
