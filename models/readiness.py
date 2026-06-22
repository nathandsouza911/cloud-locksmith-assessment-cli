from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class ControlResult(BaseModel):
    name: str
    status: Literal["PASS", "WARNING", "FAIL", "SKIPPED"]
    detail: str
    points: int


class InsuranceReadiness(BaseModel):
    controls: list[ControlResult] = Field(default_factory=list)
    total_score: int
    max_possible_score: int
    score_pct: float
    skipped_controls: list[str] = Field(default_factory=list)
    tier: Literal["Poor", "Fair", "Good", "Strong"]
