"""Capture deterministic, correlated Feature 08 evidence without network access."""

from __future__ import annotations

import argparse
import io
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import Settings
from src.mcp.client import FinanceMCPClient
from src.observability import (
    Observability,
    PersistenceTelemetryObserver,
    ToolTelemetryObserver,
)
from src.observability.logging import JsonFormatter, StructuredLogger
from src.orchestration.graph import AnalysisOrchestrator
from src.persistence.repository import FileResultRepository
from src.services.analysis import AnalysisService


@dataclass(frozen=True)
class CaptureSummary:
    """Stable summary of the representative API run."""

    run_id: str
    status: str
    requested_tasks: int
    log_events: int


def _capture_logger() -> tuple[logging.Logger, logging.StreamHandler[io.StringIO], io.StringIO]:
    stream = io.StringIO()
    logger = logging.getLogger("financial_analysis.verification_capture")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger, handler, stream


def capture(output_dir: Path) -> CaptureSummary:
    """Execute the representative AAPL/TSLA run and write inspectable artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    logger, handler, stream = _capture_logger()
    settings = Settings(
        _env_file=None,
        app_environment="test",
        mcp_transport="memory",
        result_output_dir=output_dir,
        cors_allowed_origins=["http://localhost:3000"],
    )
    observability = Observability(logger=StructuredLogger(logger))
    repository = FileResultRepository(
        output_dir, observer=PersistenceTelemetryObserver(observability)
    )
    orchestrator = AnalysisOrchestrator(
        mcp_client=FinanceMCPClient(settings, observer=ToolTelemetryObserver(observability)),
        observability=observability,
    )
    service = AnalysisService(
        runner=orchestrator,
        repository=repository,
        observability=observability,
    )

    try:
        with TestClient(create_app(settings=settings, service=service)) as client:
            response = client.post(
                "/api/v1/analyses",
                json={"request_text": "Analyze AAPL and TSLA"},
            )
            if response.status_code != 200:
                raise RuntimeError(f"Representative analysis failed with HTTP {response.status_code}.")
            result = response.json()
            metrics = client.get("/api/v1/metrics").json()
            openapi = client.get("/openapi.json").json()
    finally:
        logger.removeHandler(handler)

    run_id = str(result["run_id"])
    artifact_path = output_dir / f"{run_id}.json"
    if not artifact_path.exists():
        raise RuntimeError("The analysis response was not persisted as a JSON artifact.")
    persisted = json.loads(artifact_path.read_text(encoding="utf-8"))
    if persisted != result:
        raise RuntimeError("The persisted JSON artifact does not match the API response.")

    events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    if not events or any(event.get("run_id") != run_id for event in events):
        raise RuntimeError("Structured events are missing or are not correlated to the representative run.")

    summary = CaptureSummary(
        run_id=run_id,
        status=str(result["status"]),
        requested_tasks=int(result["report"]["execution"]["requested_tasks"]),
        log_events=len(events),
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "openapi.json").write_text(
        json.dumps(openapi, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "logs.jsonl").write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(asdict(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/feature-08"),
        help="Directory for the persisted run, logs, metrics, OpenAPI, and summary JSON.",
    )
    args = parser.parse_args()
    summary = capture(args.output_dir)
    print(json.dumps(asdict(summary), sort_keys=True))


if __name__ == "__main__":
    main()
