# Conversation Memory & Context Management

This document outlines the architecture and lifecycle for handling multi-turn conversations and context management within the AI-First CCMS Customer Backend (Phase 2C).

## Architecture

The conversation memory feature adheres to the existing LangGraph orchestration by introducing three new components:

1.  **`ConversationRepository`**: A data layer responsible for storing conversation histories, metadata, summaries, and extracted entities. Currently implemented in-memory to prevent database migrations during prototyping, but provides a standard async interface for future persistent data stores (e.g., PostgreSQL).
2.  **`ConversationMemoryService`**: The core business logic service that manages memory. It handles appending messages, triggering summarizations, resolving contextual references (e.g., "him", "that complaint") based on previous turns, and calculating memory compression triggers.
3.  **`ContextBuilder`**: A service exclusively responsible for assembling structured context strings (combining Conversation Summary, active Clarifications, Complaint Drafts, etc.) to be injected into LLM prompts.

## `conversation_id` Lifecycle

The `conversation_id` acts as the primary key identifying a single conversation thread.
1.  **Ingestion**: When a request hits the API, the `conversation_id` is parsed and attached to the `GraphState`.
2.  **Memory Storage**: The `input_node` and `response_node` intercept the user and assistant messages, respectively, passing the `conversation_id` to the `ConversationMemoryService` to be logged into the repository.
3.  **Graph Decoupling**: Large message histories (`message_history`) are no longer transported on the ephemeral `GraphState` through every node. Instead, nodes request only necessary context from `ContextBuilder`, which queries the memory service using the `conversation_id`.

## Clarification Lifecycle

To support fluid multi-turn clarification (e.g., the assistant asks "Was that an email or a phone call?" and the user responds "Phone call"):

1.  **Initiation**: `decision_node` decides an action cannot proceed due to missing requirements. It flags `AgentAction.CLARIFY`.
2.  **State Creation**: A `ClarificationState` object is populated and added to `GraphState`, detailing which tool is missing fields.
3.  **Next Turn**: When the user provides the answer, the graph execution begins again. The `intent_node` detects that a `ClarificationState` is active and **skips** generic intent detection, ensuring the context remains anchored to the active tool.
4.  **Extraction & Resume**: The `entity_extraction_node` merges the new user answer into the `InteractionDraft`.
5.  **Completion**: The `decision_node` evaluates if the draft now satisfies the tool's requirements. If so, it clears the `ClarificationState` and proceeds to `EXECUTE_TOOL`.

## Memory Compression Strategies

To maintain high performance and avoid context limits:
- Summarizations are triggered dynamically when a conversation breaches a configurable threshold.
- The `ConversationMemoryService` tracks both raw `message_count` and `estimated_tokens`.
- Upon breaching `SUMMARY_AFTER_MESSAGES` (e.g., 10 messages) or `MAX_CONTEXT_TOKENS` (e.g., 3000 tokens), an LLM summarization process consolidates older history into the `ConversationSummary`.
