from typing import Any, Dict, Type, Optional
from pydantic import BaseModel
import logging
import asyncio

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from .settings import settings

class LLMManager:
    """
    Central class for managing LLM API interactions using LangChain's chat models.
    Providers are initialized with fixed parameters (read from environment variables via settings)
    and the chat invocation is handled via a unified interface.
    """

    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self.current_provider: Optional[str] = None
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("LLMManager")
        self.logger.setLevel(logging.INFO)
        # Initialize providers asynchronously
        asyncio.create_task(self._initialize_providers())

    async def _initialize_providers(self):
        """Initialize LLM providers from settings."""
        try:
            # OpenAI configuration using LangChain's ChatOpenAI
            if settings.OPENAI_API_KEY:
                llm_openai = ChatOpenAI(
                    model_name=settings.OPENAI_MODEL,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    max_retries=settings.DEFAULT_MAX_RETRIES,
                    max_tokens=settings.DEFAULT_MAX_TOKENS,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                await self._add_provider("openai", llm_openai)


            # Groq configuration using LangChain's ChatGroq
            if settings.GROQ_API_KEY:
                llm_groq = ChatGroq(
                    model=settings.GROQ_MODEL,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    max_retries=settings.DEFAULT_MAX_RETRIES,
                    max_tokens=settings.DEFAULT_MAX_TOKENS,
                    groq_api_key=settings.GROQ_API_KEY,
                )


                await self._add_provider("groq", llm_groq)

            # Ollama configuration using LangChain's ChatOllama
            if settings.OLLAMA_HOST:
                llm_ollama = ChatOllama(
                    model=settings.OLLAMA_MODEL,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    num_predict=settings.DEFAULT_MAX_TOKENS,
                    base_url=settings.OLLAMA_HOST,
                )
                await self._add_provider("ollama", llm_ollama)
                # If a structured model is defined, instantiate a dedicated structured client.
                if settings.OLLAMA_STRUCTURED_MODEL is not None:
                    llm_ollama_structured = ChatOllama(
                        model=settings.OLLAMA_STRUCTURED_MODEL,
                        temperature=settings.DEFAULT_TEMPERATURE,
                        num_predict=settings.DEFAULT_MAX_TOKENS,
                        base_url=settings.OLLAMA_HOST,
                    )
                    await self._add_provider("ollama_structured", llm_ollama_structured)

            # Set the default provider based on settings.DEFAULT_PROVIDER if it is available; otherwise choose the first available provider.
            if settings.DEFAULT_PROVIDER in self.clients:
                self.current_provider = settings.DEFAULT_PROVIDER
            elif self.clients:
                self.current_provider = next(iter(self.clients))
        except Exception as e:
            self.logger.error(f"Provider initialization error: {e}")
            raise

    async def _add_provider(self, name: str, client: Any):
        """Add a new LLM provider."""
        async with self.lock:
            self.clients[name] = client

    async def switch_provider(self, provider_name: str):
        """Switch the active LLM provider."""
        async with self.lock:
            if provider_name in self.clients:
                self.current_provider = provider_name
            else:
                raise ValueError(f"Provider {provider_name} not configured")

    def _convert_messages(self, messages: list) -> list:
        """
        Convert a list of message dictionaries to the tuple format expected by LangChain.
        Remaps the role 'user' to 'human'; other roles remain unchanged.
        """
        def map_role(role: str) -> str:
            return "human" if role == "user" else role

        return [(map_role(m.get("role", "")), m.get("content", "")) for m in messages]

    async def create_completion_async(
        self,
        response_model: Optional[Type[BaseModel]],
        messages: list,
        max_tokens: Optional[int] = None,
        retries: int = settings.DEFAULT_MAX_RETRIES
    ) -> Optional[BaseModel]:
        """


        Create a completion using the current LLM provider.


        Parameters:
            response_model: The Pydantic model for the structured output. If None, a raw response is returned.
            messages: A list of messages as dictionaries with keys "role" and "content".
            max_tokens: Maximum tokens allowed for the generation.
            retries: Number of retry attempts.

        Returns:
            A parsed response using response_model if provided, otherwise the raw response; or None on failure.
        """
        if not self.current_provider:
            self.logger.error("No provider is configured.")
            return None

        conv_messages = self._convert_messages(messages)

        for attempt in range(retries):
            async with self.lock:
                try:
                    client = self.clients[self.current_provider]
                    # Special handling for Ollama's structured output.
                    if (
                        self.current_provider == "ollama" and
                        response_model and
                        "ollama_structured" in self.clients
                    ):
                        # Step 1: Get the raw output using the default Ollama client.
                        raw_invoke_kwargs = {"num_predict": max_tokens} if max_tokens is not None else {}
                        raw_response = await self.clients["ollama"].ainvoke(conv_messages, **raw_invoke_kwargs)
                        raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

                        # Step 2: Use the pre-instantiated structured client.
                        structured_client = self.clients["ollama_structured"].with_structured_output(response_model)
                        parse_messages = [
                            ("system", "Convert the following text into a structured JSON following the provided schema."),
                            ("human", raw_text)
                        ]
                        parse_invoke_kwargs = {"num_predict": max_tokens} if max_tokens is not None else {}
                        structured_response = await structured_client.ainvoke(parse_messages, **parse_invoke_kwargs)
                        return structured_response
                    else:
                        invoke_kwargs = {}
                        if max_tokens is not None:
                            if self.current_provider == "ollama":
                                invoke_kwargs = {"num_predict": max_tokens}
                            else:
                                invoke_kwargs = {"max_tokens": max_tokens}
                        if response_model:
                            structured = client.with_structured_output(response_model)
                            response = await structured.ainvoke(conv_messages, **invoke_kwargs)
                        else:
                            response = await client.ainvoke(conv_messages, **invoke_kwargs)
                        return response
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