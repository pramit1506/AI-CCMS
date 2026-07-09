from app.llm.base import BaseLLMProvider
from app.llm.providers.groq_provider import GroqProvider

def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function to get the configured LLM provider.
    Currently defaults to GroqProvider.
    """
    return GroqProvider()
