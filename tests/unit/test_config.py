from pathlib import Path
import subprocess
import sys

import pytest

from src.core.config import Settings
from src.core.errors import ConfigurationError


def test_settings_have_safe_openai_defaults() -> None:
    settings = Settings(_env_file=None, openai_api_key="test-key")

    assert settings.openai_model == "gpt-5.6-luna"
    assert settings.openai_temperature == 0.0
    assert settings.mcp_transport == "memory"
    assert "test-key" not in repr(settings)


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-luna-custom")
    monkeypatch.setenv("RESULT_OUTPUT_DIR", "test-artifacts")

    settings = Settings(_env_file=None, openai_api_key="test-key")

    assert settings.openai_model == "gpt-5.6-luna-custom"
    assert settings.result_output_dir == Path("test-artifacts")


def test_missing_openai_key_raises_typed_safe_error() -> None:
    settings = Settings(_env_file=None, openai_api_key=None)

    with pytest.raises(ConfigurationError) as caught:
        settings.require_openai()

    detail = caught.value.to_detail()
    assert detail.code == "configuration_error"
    assert detail.context == {
        "setting": "OPENAI_API_KEY",
        "operation": "model_initialization",
    }
    assert "sk-" not in detail.message


def test_output_directory_is_created_and_write_checked(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "outputs"
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        result_output_dir=output_dir,
    )

    assert settings.prepare_output_directory() == output_dir.resolve()
    assert output_dir.is_dir()


def test_file_cannot_be_used_as_output_directory(tmp_path: Path) -> None:
    invalid_path = tmp_path / "not-a-directory"
    invalid_path.write_text("occupied", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        result_output_dir=invalid_path,
    )

    with pytest.raises(ConfigurationError) as caught:
        settings.prepare_output_directory()

    assert caught.value.to_detail().context["path"] == str(invalid_path.resolve())


def test_http_mcp_transport_requires_url() -> None:
    with pytest.raises(ValueError, match="MCP_URL"):
        Settings(_env_file=None, openai_api_key="test-key", mcp_transport="http")


def test_foundation_imports_have_no_console_side_effects() -> None:
    completed = subprocess.run(
        [sys.executable, "-c", "import src.config, src.core.config, src.schemas"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == ""
    assert completed.stderr == ""
