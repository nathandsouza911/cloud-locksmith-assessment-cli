from __future__ import annotations
from graph.provider import GraphDataProvider
from graph.licenses import fetch_subscribed_skus
from models.findings import LicenseWasteFinding, FindingStatus
from pricing.sku_pricing import get_pricing


class UnassignedLicenseFinder:
    """Estimate *potentially reclaimable* licensed seats and their annual/monthly cost.

    Unassigned seats are seats paid for but not currently assigned. They are
    "potentially reclaimable", not proven waste — a deliberate buffer of spare
    seats is legitimate. Dollar figures are estimates from an approximate public
    list-price map (or a user-supplied override) and must not be treated as
    authoritative billing data.
    """

    def __init__(self, provider: GraphDataProvider, pricing: dict[str, float] | None = None) -> None:
        self._provider = provider
        self._pricing = pricing if pricing is not None else get_pricing()

    def run(self) -> LicenseWasteFinding:
        try:
            skus = fetch_subscribed_skus(self._provider)
            if not skus:
                return LicenseWasteFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason=(
                        "No commercial Microsoft 365 subscriptions were found on this tenant. "
                        "Developer tenants, trial tenants, and some test environments may not "
                        "expose commercial subscription SKUs."
                    ),
                )
            active = sum(s.prepaidUnits.enabled for s in skus)
            consumed = sum(s.consumedUnits for s in skus)
            unassigned = sum(max(0, s.prepaidUnits.enabled - s.consumedUnits) for s in skus)

            priced_units = 0
            unpriced_units = 0
            annual = 0.0
            unknown: list[str] = []
            for s in skus:
                spare = max(0, s.prepaidUnits.enabled - s.consumedUnits)
                if s.skuPartNumber in self._pricing:
                    priced_units += spare
                    annual += spare * self._pricing[s.skuPartNumber]
                elif spare > 0:
                    unpriced_units += spare
                    if s.skuPartNumber not in unknown:
                        unknown.append(s.skuPartNumber)

            warning = (
                f"{unpriced_units} reclaimable seat(s) across {len(unknown)} SKU(s) have no "
                "pricing data; the dollar estimate covers only priced SKUs."
                if unpriced_units else None
            )
            return LicenseWasteFinding(
                status=FindingStatus.SUCCESS,
                active_units=active,
                consumed_units=consumed,
                unassigned_units=unassigned,
                estimated_reclaimable_annual_usd=round(annual, 2),
                estimated_reclaimable_monthly_usd=round(annual / 12, 2),
                priced_unassigned_units=priced_units,
                unpriced_unassigned_units=unpriced_units,
                unknown_skus=sorted(unknown),
                partial_pricing_warning=warning,
            )
        except Exception as exc:
            return LicenseWasteFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"License data unavailable: {exc}",
            )
