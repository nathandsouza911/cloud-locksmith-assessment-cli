from __future__ import annotations
from typing import Literal
from graph.provider import GraphDataProvider
from graph.roles import fetch_global_admins
from models.findings import GlobalAdminsFinding, FindingStatus


class GlobalAdminFinder:
    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> GlobalAdminsFinding:
        try:
            admins = fetch_global_admins(self._provider)
            if not admins:
                return GlobalAdminsFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="No Global Administrator role members found.",
                )
            count = len(admins)
            risk: Literal["Good", "Moderate", "High"] = (
                "Good" if count <= 3 else "Moderate" if count <= 5 else "High"
            )
            return GlobalAdminsFinding(
                status=FindingStatus.SUCCESS,
                count=count,
                risk_level=risk,
            )
        except Exception as exc:
            return GlobalAdminsFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Directory role data unavailable: {exc}",
            )
