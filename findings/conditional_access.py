from __future__ import annotations
from graph.errors import GraphAPIError
from graph.provider import GraphDataProvider
from models.findings import ConditionalAccessFinding, FindingStatus


class ConditionalAccessFinder:
    """Conditional Access policy inventory — presence and state only, no rule internals."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> ConditionalAccessFinding:
        try:
            policies = self._provider.get_conditional_access_policies()
            enabled = [p for p in policies if p.state == "enabled"]
            report_only = [p for p in policies if p.state == "enabledForReportingButNotEnforced"]
            examples = [p.displayName for p in enabled[:3] if p.displayName]
            return ConditionalAccessFinding(
                status=FindingStatus.SUCCESS,
                policy_count=len(policies),
                enabled_count=len(enabled),
                report_only_count=len(report_only),
                examples=examples,
            )
        except GraphAPIError as exc:
            if exc.status_code == 403:
                return ConditionalAccessFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason=(
                        "Conditional Access inventory requires Policy.Read.All admin consent "
                        "and Microsoft Entra ID P1 or P2 licensing."
                    ),
                )
            return ConditionalAccessFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Conditional Access data unavailable: [{exc.status_code}] {exc.error_code}",
            )
        except Exception as exc:
            return ConditionalAccessFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Conditional Access data unavailable: {exc}",
            )
