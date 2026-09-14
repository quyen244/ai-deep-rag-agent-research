"""Real API-to-orchestrator-to-in-memory-MCP boundary coverage."""

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import Settings


def test_api_executes_and_persists_a_real_in_memory_mcp_analysis(tmp_path) -> None:  # type: ignore[no-untyped-def]
    app = create_app(
        settings=Settings(
            _env_file=None,
            app_environment="test",
            result_output_dir=tmp_path,
            cors_allowed_origins=["http://localhost:3000"],
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/analyses",
        json={"tickers": ["AAPL"], "domains": ["technical", "sentiment"]},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "succeeded"
    assert result["report"]["execution"]["requested_tasks"] == 2
    assert result["report"]["execution"]["succeeded_tasks"] == 2
    assert client.get(f"/api/v1/analyses/{result['run_id']}").json() == result
    assert (tmp_path / f"{result['run_id']}.json").exists()
