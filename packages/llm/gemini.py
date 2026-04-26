"""Gemini model factories via LangChain wrappers with retry, callbacks, and structured output."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import LLMResult
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from packages.llm.settings import LLMSettings


@lru_cache(maxsize=1)
def _settings() -> LLMSettings:
    return LLMSettings()


class TokenCounterCallback(BaseCallbackHandler):
    """Callback that tracks token usage across LLM calls."""

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        self.call_count += 1
        for gen_list in response.generations:
            for gen in gen_list:
                info = gen.generation_info or {}
                usage = info.get("usage_metadata", {})
                self.total_input_tokens += usage.get("prompt_token_count", 0)
                self.total_output_tokens += usage.get("candidates_token_count", 0)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens


_token_counter = TokenCounterCallback()


def _build_callbacks() -> list[BaseCallbackHandler]:
    """Assemble the callback list (token counter + optional LangSmith)."""
    callbacks: list[BaseCallbackHandler] = [_token_counter]
    s = _settings()
    if s.langchain_tracing_v2 and s.langchain_api_key:
        try:
            from langsmith import Client

            Client(api_key=s.langchain_api_key)
        except Exception:
            logger.warning("LangSmith tracing enabled but client init failed")
    return callbacks


def get_gemini_pro() -> ChatGoogleGenerativeAI:
    """Return Gemini 1.5 Pro for complex reasoning tasks."""
    s = _settings()
    return ChatGoogleGenerativeAI(
        model=s.gemini_model_pro,
        google_api_key=s.google_api_key,
        temperature=s.llm_temperature,
        max_retries=s.llm_max_retries,
        callbacks=_build_callbacks(),
    )


def get_gemini_flash() -> ChatGoogleGenerativeAI:
    """Return Gemini 1.5 Flash for fast/cheap tasks."""
    s = _settings()
    return ChatGoogleGenerativeAI(
        model=s.gemini_model_flash,
        google_api_key=s.google_api_key,
        temperature=s.llm_temperature,
        max_retries=s.llm_max_retries,
        callbacks=_build_callbacks(),
    )


def get_structured_llm[T: BaseModel](model: BaseChatModel, output_schema: type[T]) -> BaseChatModel:
    """Wrap a chat model to emit structured Pydantic output."""
    return model.with_structured_output(output_schema)


def get_token_counter() -> TokenCounterCallback:
    """Return the global token counter singleton."""
    return _token_counter


@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
async def invoke_with_retry(chain, inputs: dict) -> object:
    """Invoke a LangChain chain/model with tenacity retry on transient errors."""
    return await chain.ainvoke(inputs)
