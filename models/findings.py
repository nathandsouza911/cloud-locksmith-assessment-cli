from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class UserSummary(BaseModel):
    display_name: str
    user_principal_name: str


class LicenseWasteFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    active_units: int = 0
    consumed_units: int = 0
    unassigned_units: int = 0
    estimated_annual_waste_usd: float = 0.0


class DormantUsersFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class DisabledLicensedFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class GlobalAdminsFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    count: int = 0
    risk_level: Literal["Good", "Moderate", "High"] = "Good"


class MFACoverageFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    privileged_user_count: int = 0
    mfa_registered_count: int = 0
    coverage_pct: float = 0.0
