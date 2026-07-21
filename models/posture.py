from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

# Grade bands for the Security Posture Score (percentage of achievable points).
GRADE_BANDS: list[tuple[float, str]] = [
    (90.0, "Strong"),
    (70.0, "Good"),
    (40.0, "Fair"),
    (0.0, "Weak"),
]


class ControlResult(BaseModel):
    name: str
    status: Literal["PASS", "WARNING", "FAIL", "SKIPPED"]
    detail: str
    points: int
    max_points: int = 2


class PostureScore(BaseModel):
    """Identity Security Posture Score — a roll-up of the evaluated identity/access
    controls (points earned / points achievable across evaluated controls).

    It reflects only the Microsoft 365 identity/access controls this tool could
    evaluate. It is NOT a measure of overall cybersecurity maturity, breach
    likelihood, compliance, or cyber-insurance eligibility.
    """
    controls: list[ControlResult] = Field(default_factory=list)
    total_score: int
    max_possible_score: int
    score_pct: float
    skipped_controls: list[str] = Field(default_factory=list)
    grade: Literal["Weak", "Fair", "Good", "Strong"]
    grade_cap_reason: str | None = None
