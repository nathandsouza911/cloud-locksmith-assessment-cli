from __future__ import annotations
from graph.provider import GraphDataProvider
from graph.licenses import fetch_subscribed_skus
from models.findings import LicenseWasteFinding, FindingStatus
from pricing.sku_pricing import SKU_PRICING


class UnassignedLicenseFinder:
    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> LicenseWasteFinding:
        try:
            skus = fetch_subscribed_skus(self._provider)
            if not skus:
                return LicenseWasteFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="No SKU data available",
                )
            active = sum(s.prepaidUnits.enabled for s in skus)
            consumed = sum(s.consumedUnits for s in skus)
            unassigned = sum(max(0, s.prepaidUnits.enabled - s.consumedUnits) for s in skus)
            waste = sum(
                max(0, s.prepaidUnits.enabled - s.consumedUnits) * SKU_PRICING.get(s.skuPartNumber, 0.0)
                for s in skus
            )
            return LicenseWasteFinding(
                status=FindingStatus.SUCCESS,
                active_units=active,
                consumed_units=consumed,
                unassigned_units=unassigned,
                estimated_annual_waste_usd=round(waste, 2),
            )
        except Exception as exc:
            return LicenseWasteFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"License data unavailable: {exc}",
            )
