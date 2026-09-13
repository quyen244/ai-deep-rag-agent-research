"""Bounded Luna structured-output interpretation for executor narratives."""

import json
from typing import Any, Protocol

from pydantic import ValidationError

from src.core.config import Settings
from src.core.errors import AgentExecutionError
from src.core.model_factory import ModelFactory
from src.executors.contracts import GroundedInterpretation


StructuredInterpretation = GroundedInterpretation


class SupportsStructuredOutput(Protocol):
    def with_structured_output(self, schema: type[GroundedInterpretation]) -> Any: ...


class LunaStructuredInterpreter:
    """Use a LangChain-compatible Luna model with one schema-repair retry.

    The facts payload is intentionally compact and the model schema has no data
    fields. It can add concise interpretation only; MCP-derived values remain
    owned by the deterministic executor data models.
    """

    def __init__(self, model: SupportsStructuredOutput) -> None:
        self._model = model

    async def interpret(
        self,
        *,
        domain: str,
        ticker: str,
        facts: dict[str, object],
        evidence_ids: list[str],
    ) -> GroundedInterpretation:
        runnable = self._model.with_structured_output(GroundedInterpretation)
        prompt = self._prompt(
            domain=domain,
            ticker=ticker,
            facts=facts,
            evidence_ids=evidence_ids,
        )
        for attempt in range(2):
            try:
                response = await runnable.ainvoke(prompt)
                interpretation = GroundedInterpretation.model_validate(response)
                unknown_ids = set(interpretation.evidence_ids).difference(evidence_ids)
                if unknown_ids:
                    raise ValueError("interpretation cited evidence outside the supplied set")
                return interpretation
            except (ValidationError, TypeError, ValueError, KeyError) as exc:
                if attempt == 1:
                    raise AgentExecutionError(
                        "The structured interpretation could not be validated.",
                        agent=f"{domain}_executor",
                        operation="structured_interpretation",
                        context={"failure_type": type(exc).__name__, "attempts": attempt + 1},
                    ) from exc
        raise AssertionError("unreachable")

    @staticmethod
    def _prompt(
        *, domain: str, ticker: str, facts: dict[str, object], evidence_ids: list[str]
    ) -> str:
        return (
            "You are a bounded financial-analysis narrator. Return only the requested "
            "structured schema. Do not create data fields, values, dates, sources, or "
            "evidence IDs. Base every statement only on FACTS and cite one or more IDs "
            "from ALLOWED_EVIDENCE_IDS. Do not give trading instructions.\n"
            f"DOMAIN: {domain}\nTICKER: {ticker}\n"
            f"FACTS: {json.dumps(facts, sort_keys=True, separators=(',', ':'), default=str)}\n"
            f"ALLOWED_EVIDENCE_IDS: {json.dumps(evidence_ids)}"
        )


def build_luna_interpreter(
    settings: Settings, *, model_factory: ModelFactory | None = None
) -> LunaStructuredInterpreter:
    """Build the optional Luna interpretation boundary from validated settings."""

    return LunaStructuredInterpreter((model_factory or ModelFactory(settings)).create())
