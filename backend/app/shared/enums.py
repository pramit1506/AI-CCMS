from enum import Enum

class PlaceholderEnum(str, Enum):
    """
    Placeholder enum for future use.
    """
    PLACEHOLDER = "placeholder"


class ComplaintStatus(str, Enum):
    PENDING_TRIAGE = "PENDING_TRIAGE"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class ComplaintSource(str, Enum):
    EMAIL = "EMAIL"
    CALL = "CALL"
    PDF = "PDF"
    PORTAL = "PORTAL"
    TEXT = "TEXT"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


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
    SAVE_COMPLAINT = "save_complaint"
    EDIT_COMPLAINT = "edit_complaint"
    RECOMMEND_CAPA = "recommend_capa"
    SUMMARIZE_COMPLAINT = "summarize_complaint"
    COMPLETENESS_CHECKER = "completeness_check"

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
