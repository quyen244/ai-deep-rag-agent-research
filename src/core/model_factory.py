"""OpenAI chat-model construction behind an injectable factory."""

from collections.abc import Callable
from typing import Any

from src.core.config import Settings
from src.core.errors import ConfigurationError


class ModelFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self, model_class: Callable[..., Any] | None = None) -> Any:
        """Create a LangChain-compatible OpenAI model without making a network call."""

        self._settings.require_openai()
        if model_class is None:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as exc:
                raise ConfigurationError(
                    "The OpenAI model adapter is not installed.",
                    operation="model_import",
                    context={"dependency": "langchain-openai"},
                ) from exc
            model_class = ChatOpenAI

        return model_class(
            model=self._settings.openai_model,
            api_key=self._settings.openai_api_key,
            temperature=self._settings.openai_temperature,
            timeout=self._settings.openai_timeout_seconds,
            max_retries=self._settings.openai_max_retries,
        )
