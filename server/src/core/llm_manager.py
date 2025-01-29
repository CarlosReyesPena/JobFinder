from typing import Dict, Type, Any, Optional
from openai import AsyncOpenAI
from groq import AsyncGroq
import instructor
from pydantic import BaseModel
import logging
import asyncio
from .settings import settings

class LLMManager:
    """Central class for managing LLM API interactions"""

    def __init__(self):
        self._clients: Dict[str, Any] = {}
        self._current_provider = "openai"
        self._lock = asyncio.Lock()  # Using asyncio.Lock instead of threading.Lock
        self._configure_logger()
        asyncio.create_task(self._initialize_providers())  # Initialize providers asynchronously

    def _configure_logger(self):
        """Configure logging system"""
        self.logger = logging.getLogger("LLMManager")
        self.logger.setLevel(logging.INFO)

    async def _initialize_providers(self):
        """Initialize LLM providers from settings"""
        try:
            # OpenAI Configuration
            if settings.OPENAI_API_KEY:
                await self.add_provider(
                    "openai",
                    instructor.patch(AsyncOpenAI(api_key=settings.OPENAI_API_KEY)),
                    default_model="gpt-4o-mini"
                )

            # Groq Configuration
            if settings.GROQ_API_KEY:
                await self.add_provider(
                    "groq",
                    instructor.patch(AsyncGroq(api_key=settings.GROQ_API_KEY)),
                    default_model="llama3-70b-8192"
                )

        except Exception as e:
            self.logger.error(f"Provider initialization error: {e}")
            raise

    async def add_provider(self, name: str, client: Any, default_model: str):
        """
        Add a new LLM provider
        Args:
            name (str): Provider name
            client (Any): Provider client
            default_model (str): Default model to use
        """
        async with self._lock:
            self._clients[name] = {
                "client": client,
                "models": [default_model],
                "default_model": default_model
            }

    async def switch_provider(self, provider_name: str):
        """
        Switch active LLM provider
        Args:
            provider_name (str): Name of the provider to switch to
        """
        async with self._lock:
            if provider_name in self._clients:
                self._current_provider = provider_name
            else:
                raise ValueError(f"Provider {provider_name} not configured")

    async def get_client(self, provider: Optional[str] = None) -> Any:
        """
        Get client for specific provider
        Args:
            provider (Optional[str]): Provider name, uses current if None
        Returns:
            Any: Provider client
        """
        provider = provider or self._current_provider
        return self._clients.get(provider, {}).get("client")

    async def create_completion_async(
        self,
        response_model: Type[BaseModel],
        messages: list,
        max_retries: int = 2,
        **kwargs
    ) -> Optional[BaseModel]:
        """
        Create completion with the current LLM provider
        Args:
            response_model (Type[BaseModel]): Expected response model
            messages (list): Messages for completion
            max_retries (int): Maximum number of retries
            **kwargs: Additional arguments for completion
        Returns:
            Optional[BaseModel]: Completion response
        """
        for attempt in range(max_retries):
            async with self._lock:
                try:
                    client_info = self._clients[self._current_provider]
                    client = client_info["client"]
                    model = kwargs.pop("model", client_info["default_model"])

                    return await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        response_model=response_model,
                        **kwargs
                    )

                except Exception as e:
                    self.logger.error(f"Error with {self._current_provider}: {str(e)}")
                    if attempt < max_retries - 1:
                        await self._switch_to_fallback()
                    else:
                        raise

    async def _switch_to_fallback(self):
        """Switch to another available provider"""
        async with self._lock:
            available = list(self._clients.keys())
            if available:
                new_provider = next(p for p in available if p != self._current_provider)
                self._current_provider = new_provider
                self.logger.info(f"Switching to {new_provider}")

class LLMResponse(BaseModel):
    """Base model for LLM responses"""
    content: str
    metadata: Optional[dict] = None