from __future__ import annotations
from graph.errors import GraphAPIError
from graph.provider import GraphDataProvider
from models.findings import SecurityDefaultsFinding, FindingStatus


class SecurityDefaultsFinder:
    """Whether Microsoft Entra Security Defaults are enabled."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> SecurityDefaultsFinding:
        try:
            policy = self._provider.get_security_defaults()
            return SecurityDefaultsFinding(
                status=FindingStatus.SUCCESS,
                enabled=policy.isEnabled,
            )
        except GraphAPIError as exc:
            if exc.status_code == 403:
                return SecurityDefaultsFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="Security Defaults status requires Policy.Read.All admin consent.",
                )
            return SecurityDefaultsFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Security Defaults unavailable: [{exc.status_code}] {exc.error_code}",
            )
        except Exception as exc:
            return SecurityDefaultsFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Security Defaults unavailable: {exc}",
            )
