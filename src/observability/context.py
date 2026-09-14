"""Scoped correlation context inherited by async tasks through ``contextvars``."""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, Mapping
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ObservationContext:
    """Stable identifiers and LangChain metadata for one accepted request."""

    run_id: str
    request_id: str
    trace_metadata: Mapping[str, str]


_CURRENT_CONTEXT: ContextVar[ObservationContext | None] = ContextVar(
    "financial_analysis_observation_context", default=None
)


def new_request_id() -> str:
    """Create an opaque request correlation ID independent of client input."""

    return str(uuid4())


def current_context() -> ObservationContext | None:
    """Return the active request context, if a boundary established one."""

    return _CURRENT_CONTEXT.get()


@contextmanager
def run_scope(
    run_id: str,
    *,
    request_id: str | None = None,
    trace_metadata: Mapping[str, str] | None = None,
) -> Iterator[ObservationContext]:
    """Bind run metadata for synchronous code and all spawned async tasks."""

    if not run_id.strip():
        raise ValueError("run_id is required for an observation scope")
    active = current_context()
    resolved_request_id = request_id or (active.request_id if active else new_request_id())
    metadata = {
        **{str(key): str(value) for key, value in (trace_metadata or {}).items()},
        "run_id": run_id,
        "request_id": resolved_request_id,
    }
    context = ObservationContext(
        run_id=run_id,
        request_id=resolved_request_id,
        trace_metadata=metadata,
    )
    token: Token[ObservationContext | None] = _CURRENT_CONTEXT.set(context)
    try:
        yield context
    finally:
        _CURRENT_CONTEXT.reset(token)
