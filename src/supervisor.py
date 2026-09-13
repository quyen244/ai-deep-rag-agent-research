"""Retired model-controlled supervisor entry point.

Feature 04 replaces this compatibility boundary with deterministic LangGraph
task planning and concurrent typed-executor fan-out. Keeping a clear runtime
message here avoids importing the removed ReAct and third-party supervisor
dependencies from legacy scripts.
"""


def build_financial_agent() -> None:
    raise RuntimeError(
        "The legacy supervisor was retired. Use the typed executors now; "
        "the deterministic LangGraph workflow arrives in Feature 04."
    )
