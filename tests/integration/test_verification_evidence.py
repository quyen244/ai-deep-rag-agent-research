"""Feature 08 evidence command contract."""

import json

from scripts.capture_verification_evidence import capture


def test_representative_capture_crosses_every_local_boundary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    summary = capture(tmp_path)

    result = json.loads((tmp_path / f"{summary.run_id}.json").read_text())
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    openapi = json.loads((tmp_path / "openapi.json").read_text())
    events = [json.loads(line) for line in (tmp_path / "logs.jsonl").read_text().splitlines()]

    assert summary.status == "succeeded"
    assert summary.requested_tasks == 8
    assert result["report"]["comparison"] is not None
    assert metrics["analyses_submitted"] == 1
    assert metrics["analyses_succeeded"] == 1
    assert metrics["tools"]["get_ohlcv"]["succeeded"] == 2
    assert metrics["synthesis"]["report_synthesis"]["succeeded"] == 1
    assert metrics["persistence"]["result_save"]["succeeded"] == 1
    assert "/api/v1/analyses" in openapi["paths"]
    assert all(event["run_id"] == summary.run_id for event in events)
    assert {event["event"] for event in events} >= {
        "analysis_request_accepted",
        "pipeline_started",
        "mcp_tool_completed",
        "agent_execution_completed",
        "synthesis_completed",
        "persistence_completed",
        "analysis_execution_completed",
    }
