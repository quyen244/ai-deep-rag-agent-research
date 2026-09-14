from typing import Any

import pytest
from pydantic import SecretStr

from src.core.config import Settings
from src.core.errors import ConfigurationError
from src.core.model_factory import ModelFactory


class FakeChatModel:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


def test_factory_targets_configured_openai_model_without_network() -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key="sk-test-only",
        openai_model="gpt-5.6-luna",
        openai_temperature=0.2,
        openai_timeout_seconds=45,
        openai_max_retries=1,
    )

    model = ModelFactory(settings).create(FakeChatModel)

    assert model.kwargs["model"] == "gpt-5.6-luna"
    assert isinstance(model.kwargs["api_key"], SecretStr)
    assert model.kwargs["api_key"].get_secret_value() == "sk-test-only"
    assert model.kwargs["temperature"] == 0.2
    assert model.kwargs["timeout"] == 45
    assert model.kwargs["max_retries"] == 1
    assert "base_url" not in model.kwargs


def test_factory_rejects_missing_key_before_model_construction() -> None:
    settings = Settings(_env_file=None, openai_api_key=None)

    with pytest.raises(ConfigurationError):
        ModelFactory(settings).create(FakeChatModel)
