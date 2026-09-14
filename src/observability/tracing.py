"""Exact LangChain/LangSmith metadata derived from the active run context."""

import inspect
from typing import Any

from src.observability.context import current_context


def langchain_trace_config(operation: str) -> dict[str, object] | None:
    """Return metadata that LangChain forwards to enabled LangSmith tracing."""

    context = current_context()
    if context is None:
        return None
    return {
        "metadata": {**context.trace_metadata, "operation": operation},
        "tags": [f"run_id:{context.run_id}", f"request_id:{context.request_id}"],
    }


async def ainvoke_with_trace_metadata(runnable: Any, payload: object, *, operation: str) -> Any:
    """Call compatible LangChain runnables without requiring tracing to be enabled."""

    config = langchain_trace_config(operation)
    if config is None or not _supports_config(runnable):
        return await runnable.ainvoke(payload)
    return await runnable.ainvoke(payload, config=config)


def _supports_config(runnable: Any) -> bool:
    try:
        parameters = inspect.signature(runnable.ainvoke).parameters.values()
    except (TypeError, ValueError):
        return True
    return any(
        parameter.name == "config" or parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
