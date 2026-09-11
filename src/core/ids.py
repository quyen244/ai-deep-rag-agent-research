"""Stable identifier helpers."""

from uuid import UUID, uuid4


def new_run_id() -> UUID:
    """Create the stable identity for a single analysis execution."""

    return uuid4()
