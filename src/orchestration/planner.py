"""Task planning with one explicit task per requested ticker and domain."""

from collections.abc import Sequence

from src.orchestration.contracts import TaskSpec
from src.schemas.request import NormalizedRequest


def ensure_unique_tasks(tasks: Sequence[TaskSpec]) -> list[TaskSpec]:
    """Validate task identity before a graph can dispatch work."""

    validated = [TaskSpec.model_validate(task) for task in tasks]
    identities = [task.identity for task in validated]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate task identity is not allowed")
    return validated


class TaskPlanner:
    def plan(self, *, run_id: str, request: NormalizedRequest) -> list[TaskSpec]:
        tasks = [
            TaskSpec.create(
                run_id=run_id,
                ticker=ticker,
                domain=domain,
                timeframe=request.timeframe,
                focus_areas=request.focus_areas,
            )
            for ticker in request.tickers
            for domain in request.domains
        ]
        return ensure_unique_tasks(tasks)
