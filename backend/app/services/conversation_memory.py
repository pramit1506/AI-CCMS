from typing import List, Optional, Dict, Any
from app.schemas.memory import ConversationSummary, ConversationMetadata, Message, ResolvedContext
from app.repositories.conversation_repository import conversation_repository
from app.llm.factory import get_llm_provider
from app.prompts.loader import load_prompt
from loguru import logger
import json

# Constants for compression thresholds
MAX_CONTEXT_TOKENS = 3000
SUMMARY_AFTER_MESSAGES = 10

class ConversationMemoryService:
    def __init__(self):
        self.repo = conversation_repository

    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        metadata = await self.repo.get_metadata(conversation_id)
        if not metadata:
            metadata = ConversationMetadata()
            await self.repo.save_metadata(conversation_id, metadata)
        return metadata

    async def save_metadata(self, conversation_id: str, metadata: ConversationMetadata) -> None:
        await self.repo.save_metadata(conversation_id, metadata)

    async def get_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        return await self.repo.get_summary(conversation_id)

    async def get_recent_messages(self, conversation_id: str, limit: int = 5) -> List[Message]:
        return await self.repo.get_messages(conversation_id, limit=limit)

    async def append_message(self, conversation_id: str, role: str, content: str) -> None:
        msg = Message(role=role, content=content)
        await self.repo.append_message(conversation_id, msg)
        
        metadata = await self.get_metadata(conversation_id)
        metadata.message_count += 1
        # Simple heuristic: 1 token ~= 4 characters
        metadata.estimated_tokens += len(content) // 4
        
        await self.save_metadata(conversation_id, metadata)
        
        # Check compression thresholds
        if metadata.message_count >= SUMMARY_AFTER_MESSAGES or metadata.estimated_tokens > MAX_CONTEXT_TOKENS:
            await self.compress_history(conversation_id)

    async def compress_history(self, conversation_id: str) -> None:
        logger.info(f"[{conversation_id}] Compressing conversation history...")
        messages = await self.repo.get_messages(conversation_id)
        if not messages:
            return
            
        current_summary = await self.get_summary(conversation_id)
        llm = get_llm_provider()
        
        # In a real scenario we'd use a dedicated summarization prompt
        # but for now we format a simple prompt.
        prompt_text = "Summarize the following conversation as valid JSON, focusing on extracted entities, user preferences, and pending tasks."
        if current_summary:
            prompt_text += f"\n\nExisting Summary:\n{current_summary.model_dump_json(indent=2)}"
            
        prompt_text += "\n\nRecent Messages:\n" + "\n".join([f"{m.role}: {m.content}" for m in messages[-SUMMARY_AFTER_MESSAGES:]])
        
        try:
            new_summary = await llm.generate_structured(
                messages=[{"role": "user", "content": prompt_text}],
                schema=ConversationSummary
            )
            await self.repo.save_summary(conversation_id, new_summary)
            
            # Reset counters (in a real system we might keep recent N messages and trim the rest)
            metadata = await self.get_metadata(conversation_id)
            metadata.message_count = 0 
            metadata.estimated_tokens = 0
            await self.save_metadata(conversation_id, metadata)
            logger.info(f"[{conversation_id}] History compressed successfully.")
        except Exception as e:
            logger.error(f"[{conversation_id}] Error compressing history: {e}")

    async def resolve_context(self, conversation_id: str, user_message: str) -> ResolvedContext:
        """
        Attempts to resolve references (like 'him', 'that meeting') using previous conversation context.
        Returns a ResolvedContext with confidence score.
        """
        summary = await self.get_summary(conversation_id)
        recent = await self.get_recent_messages(conversation_id, limit=3)
        entities = await self.repo.get_resolved_entities(conversation_id)
        
        # In a fully realized system, we would ask the LLM to resolve references:
        llm = get_llm_provider()
        prompt = (
            "Given the user's message, resolve any ambiguous references (e.g. 'him', 'it', 'yesterday's meeting') "
            "using the current conversation summary and recent messages.\n"
            f"User Message: {user_message}\n"
            f"Summary: {summary.model_dump_json() if summary else 'None'}\n"
            f"Recent: {[m.content for m in recent]}\n"
            f"Known Entities: {entities}\n"
        )
        
        try:
            resolved = await llm.generate_structured(
                messages=[{"role": "user", "content": prompt}],
                schema=ResolvedContext
            )
            # Update known entities with new ones if high confidence
            if resolved.confidence >= 0.8:
                entities.update(resolved.resolved_entities)
                await self.repo.save_resolved_entities(conversation_id, entities)
            else:
                resolved.requires_clarification = True
                
            return resolved
        except Exception as e:
            logger.error(f"[{conversation_id}] Context resolution error: {e}")
            return ResolvedContext(confidence=0.0, requires_clarification=True)

conversation_memory_service = ConversationMemoryService()
