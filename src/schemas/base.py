"""Shared Pydantic behavior for strict API and persistence contracts."""

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
