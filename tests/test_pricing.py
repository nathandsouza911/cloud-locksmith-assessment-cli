from pricing.sku_pricing import SKU_PRICING


def test_pricing_is_dict_of_str_to_float():
    assert isinstance(SKU_PRICING, dict)
    for k, v in SKU_PRICING.items():
        assert isinstance(k, str), f"Key {k!r} is not a string"
        assert isinstance(v, float), f"Value for {k!r} is not a float"


def test_known_skus_present():
    assert "SPE_E3" in SKU_PRICING
    assert "SPE_E5" in SKU_PRICING
    assert "ENTERPRISEPACK" in SKU_PRICING


def test_known_sku_prices_are_positive():
    assert SKU_PRICING["SPE_E3"] > 0
    assert SKU_PRICING["SPE_E5"] > 0


def test_unknown_sku_returns_zero():
    # Finders use .get(sku, 0.0) — verify that missing SKUs default to 0
    assert SKU_PRICING.get("UNKNOWN_SKU_XYZ", 0.0) == 0.0
