# Feature 01 foundation progress

Status: complete
Date: 2026-09-11

## Outcome

The backend now has a validated, side-effect-free foundation for OpenAI configuration, typed requests and results, lifecycle state, safe application errors, UTC clocks, run IDs, and deterministic testing. OpenRouter configuration was removed from the declared dependency and configuration surface.

## Implemented files

- `pyproject.toml` and `requirements.txt`: supported Python range and pinned direct runtime/development dependencies.
- `src/core/config.py`: Pydantic settings, runtime readiness, MCP transport validation, and output-directory checks.
- `src/core/model_factory.py`: injectable LangChain `ChatOpenAI` construction targeting `gpt-5.6-luna`.
- `src/core/errors.py` and `src/core/redaction.py`: central exception taxonomy and safe serialization.
- `src/core/clock.py` and `src/core/ids.py`: injectable UTC clock and UUID run identity.
- `src/schemas/*`: strict request, domain, evidence, report, error, and run-state contracts.
- `src/config.py`: side-effect-free compatibility import for the new settings API.
- `tests/unit/*`: configuration, redaction, model-factory, lifecycle, and JSON round-trip coverage.

## Verification evidence

Command:

```text
.\venv\Scripts\python.exe -m pytest
```

Result:

```text
22 passed in 0.74s
```

Additional checks:

- `python -m pip check`: no broken requirements found.
- `python -m compileall -q src/core src/schemas tests`: passed.
- Real `ChatOpenAI` construction returned `ChatOpenAI gpt-5.6-luna` without a network request.
- A subprocess import test proves `src.core.config` and `src.schemas` write nothing to stdout or stderr.
- Redaction tests prove common API key, token, authorization, and Bearer values do not survive error serialization.

## Known pre-existing issue

A full `src` compile still stops in the user-modified legacy `src/supervisor.py` because `timeout` is supplied twice in one call. That file was deliberately not overwritten in this feature. The approved orchestration feature replaces this legacy implementation after the MCP and executor layers exist.

## Next dependency

Feature 02 can now build the deterministic provider fixtures, finance FastMCP server, and typed client adapter on these contracts.
