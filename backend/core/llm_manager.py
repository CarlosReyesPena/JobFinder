from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
import logging
import asyncio
import instructor
from openai import OpenAI
from core.settings import settings

# Try to import Groq client if available.
try:
    from groq import Groq
except ImportError:
    Groq = None

class LLMManager:
    """
    Central class for managing LLM API interactions using the instructor library.
    
    This class initializes clients for different providers (OpenAI, Groq, and Ollama)
    using instructor's patching to support structured outputs via Pydantic models.
    """

    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self.current_provider: Optional[str] = None
        self.logger = logging.getLogger("LLMManager")
        self.logger.setLevel(logging.INFO)
        self._initialize_providers()  # Synchronous initialization

    def _initialize_providers(self):
        """Initialize LLM providers using instructor."""
        try:
            # OpenAI provider
            if settings.OPENAI_API_KEY:
                client_openai = instructor.from_openai(
                    OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                    )
                )
                client_openai.model = settings.OPENAI_MODEL
                self.clients["openai"] = client_openai

            # Groq provider (if available)
            if settings.GROQ_API_KEY and Groq is not None:
                client_groq = instructor.patch(
                    Groq(
                        api_key=settings.GROQ_API_KEY,
                    )
                )
                client_groq.model = settings.GROQ_MODEL
                self.clients["groq"] = client_groq

            # Ollama provider (using OpenAI compatibility)
            if settings.OLLAMA_HOST:
                client_ollama = instructor.from_openai(
                    OpenAI(
                        base_url=f"{settings.OLLAMA_HOST}/v1",
                        api_key="ollama",  # dummy API key, required by the API but not used
                    )
                )
                client_ollama.model = settings.OLLAMA_MODEL
                self.clients["ollama"] = client_ollama

            # Set the default provider based on settings or select the first available.
            if settings.DEFAULT_PROVIDER in self.clients:
                self.current_provider = settings.DEFAULT_PROVIDER
            elif self.clients:
                self.current_provider = next(iter(self.clients))
            else:
                self.logger.error("No providers were initialized.")
        except Exception as e:
            self.logger.error(f"Provider initialization error: {e}")
            raise

    async def switch_provider(self, provider_name: str):
        """Switch the active LLM provider."""
        if provider_name in self.clients:
            self.current_provider = provider_name
        else:
            raise ValueError(f"Provider {provider_name} not configured.")

    async def create_completion_async(
        self,
        response_model: Optional[Type[BaseModel]],
        messages: list,
        max_tokens: Optional[int] = None,
        retries: int = settings.DEFAULT_MAX_RETRIES,
    ) -> Optional[BaseModel]:
        """
        Create a completion using the current LLM provider via instructor.

        Parameters:
            response_model: The Pydantic model for structured output. If None, returns the raw response.
            messages: A list of message dictionaries (e.g., {"role": "user", "content": "..."})
            max_tokens: Maximum tokens allowed for the generation.
            retries: Number of retry attempts.

        Returns:
            A parsed response using the response_model if provided, otherwise the raw response; or None on failure.
        """
        if not self.current_provider:
            self.logger.error("No provider is configured.")
            return None

        client = self.clients[self.current_provider]

        def call_completion():
            return client.chat.completions.create(
                model=client.model,
                messages=messages,
                response_model=response_model,
                max_tokens=max_tokens,
            )

        for attempt in range(retries):
            try:
                result = await asyncio.to_thread(call_completion)
                return result
            except Exception as e:
                self.logger.error(
                    f"Error with provider '{self.current_provider}' on attempt {attempt + 1}: {e}"
                )
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    self.logger.error("Max retries reached. Returning None.")
                    return None

class LLMResponse(BaseModel):
    """Base model for LLM responses."""
    content: str
    metadata: Optional[dict] = None