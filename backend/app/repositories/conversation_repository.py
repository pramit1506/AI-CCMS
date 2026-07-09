from typing import Optional, Dict, Any, List
from app.schemas.memory import ConversationSummary, ConversationMetadata, Message

# In-memory store for now to avoid database migrations during phase 2C.
# Can be replaced with SQLAlchemy models later.
_conversations_db: Dict[str, Dict[str, Any]] = {}

class ConversationRepository:
    """
    Repository for persisting conversation history, summaries, and metadata.
    Currently uses an in-memory store to avoid database migrations, but provides 
    an asynchronous interface suitable for future database integration.
    """
    
    async def get_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        conv = _conversations_db.get(conversation_id)
        if conv and "summary" in conv:
            return ConversationSummary.model_validate(conv["summary"])
        return None

    async def save_summary(self, conversation_id: str, summary: ConversationSummary) -> None:
        if conversation_id not in _conversations_db:
            _conversations_db[conversation_id] = {"messages": [], "metadata": {}}
        _conversations_db[conversation_id]["summary"] = summary.model_dump()

    async def get_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        conv = _conversations_db.get(conversation_id)
        if conv and "metadata" in conv:
            # Reconstruct from dict
            return ConversationMetadata.model_validate(conv["metadata"])
        return None

    async def save_metadata(self, conversation_id: str, metadata: ConversationMetadata) -> None:
        if conversation_id not in _conversations_db:
            _conversations_db[conversation_id] = {"messages": [], "metadata": {}}
        _conversations_db[conversation_id]["metadata"] = metadata.model_dump()

    async def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        conv = _conversations_db.get(conversation_id)
        if not conv or "messages" not in conv:
            return []
        messages = [Message.model_validate(m) for m in conv["messages"]]
        if limit:
            return messages[-limit:]
        return messages

    async def append_message(self, conversation_id: str, message: Message) -> None:
        if conversation_id not in _conversations_db:
            _conversations_db[conversation_id] = {"messages": [], "metadata": {}}
        _conversations_db[conversation_id]["messages"].append(message.model_dump())

    async def get_resolved_entities(self, conversation_id: str) -> Dict[str, Any]:
        conv = _conversations_db.get(conversation_id)
        if conv and "resolved_entities" in conv:
            return conv["resolved_entities"]
        return {}

    async def save_resolved_entities(self, conversation_id: str, entities: Dict[str, Any]) -> None:
        if conversation_id not in _conversations_db:
            _conversations_db[conversation_id] = {"messages": [], "metadata": {}}
        _conversations_db[conversation_id]["resolved_entities"] = entities

conversation_repository = ConversationRepository()
