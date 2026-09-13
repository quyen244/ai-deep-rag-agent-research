"""Validated runtime configuration with no import-time output or filesystem writes."""

from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Self

from pydantic import AliasChoices, Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.errors import ConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Multi-Agent Financial Analysis"
    app_environment: Literal["development", "test", "production"] = "development"

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    openai_timeout_seconds: float = Field(default=60.0, gt=0.0, le=300.0)
    openai_max_retries: int = Field(default=2, ge=0, le=5)

    langsmith_tracing: bool = Field(
        default=False,
        validation_alias=AliasChoices("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"),
    )
    langsmith_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
    )
    langsmith_project: str = Field(
        default="multi-agent-financial-analysis",
        validation_alias=AliasChoices("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT"),
    )
    langsmith_endpoint: HttpUrl = Field(
        default="https://api.smith.langchain.com",
        validation_alias=AliasChoices("LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT"),
    )

    result_output_dir: Path = Path("outputs")
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    mcp_transport: Literal["memory", "stdio", "http"] = "memory"
    mcp_url: HttpUrl | None = None

    @field_validator("openai_model", "app_name", "langsmith_project")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, values: list[str]) -> list[str]:
        """Require explicit browser origins; wildcard CORS is never an MVP default."""

        normalized: list[str] = []
        for value in values:
            origin = value.strip().rstrip("/")
            if not origin.startswith(("http://", "https://")) or "/" in origin.split("://", 1)[1]:
                raise ValueError("CORS origins must be scheme and host only")
            if origin == "*":
                raise ValueError("wildcard CORS origins are not allowed")
            if origin not in normalized:
                normalized.append(origin)
        if not normalized:
            raise ValueError("at least one CORS origin is required")
        return normalized

    @model_validator(mode="after")
    def validate_transport(self) -> Self:
        if self.mcp_transport == "http" and self.mcp_url is None:
            raise ValueError("MCP_URL is required when MCP_TRANSPORT=http")
        return self

    def require_openai(self) -> Self:
        if self.openai_api_key is None or not self.openai_api_key.get_secret_value().strip():
            raise ConfigurationError(
                "OpenAI is not configured.",
                operation="model_initialization",
                context={"setting": "OPENAI_API_KEY"},
            )
        return self

    def prepare_output_directory(self) -> Path:
        """Create and verify the configured result directory at application startup."""

        output_dir = self.result_output_dir.resolve()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            if not output_dir.is_dir():
                raise NotADirectoryError(str(output_dir))
            with NamedTemporaryFile(prefix=".write-check-", dir=output_dir, delete=True):
                pass
        except OSError as exc:
            raise ConfigurationError(
                "The result output directory is unavailable.",
                operation="output_directory_check",
                context={"path": output_dir},
            ) from exc
        return output_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load one immutable-by-convention settings object for dependency injection."""

    return Settings()
