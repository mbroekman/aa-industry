# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest
from eveuniverse.models import EveTypeMaterial

# AA Industry App
from industry_reforged.utils.pricing_engine import (
    calculate_buyback_quote,
    calculate_price_density_tax,
    get_item_value_variants,
    get_reprocessing_value,
)

from .factories import (
    BuybackProgramFactory,
    BuybackWatchlistItemFactory,
    EveTypeFactory,
)


@pytest.fixture
def mock_esi_orders():
    # Django
    from django.core.cache import cache

    cache.clear()
    with patch("requests.Session.get") as mock_get:
        yield mock_get
        cache.clear()


def _market_response(price):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = [
        {"price": price, "volume_remain": 1000, "is_buy_order": False, "location_id": 60003760}
    ]
    return mock_res


def _empty_response():
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = []
    return mock_res


@pytest.mark.django_db
class TestGetReprocessingValue:
    def test_none_when_not_reprocessable(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        assert get_reprocessing_value(eve_type, 1) is None

    def test_value_from_materials(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=100
        )
        mock_esi_orders.return_value = _market_response(10.0)

        value = get_reprocessing_value(eve_type, 2)
        # 100 tritanium/unit * 10.0 isk * 2 units = 2000.0
        assert value == Decimal("2000.00") or value == Decimal("2000")


@pytest.mark.django_db
class TestGetItemValueVariants:
    def test_market_only_when_not_reprocessable(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _market_response(50.0)

        variants = get_item_value_variants(eve_type, 1)
        assert variants == {"market": Decimal("50.0")}

    def test_reprocessed_only_when_no_market_price(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=10
        )

        def side_effect(url, params=None, **kwargs):
            if params.get("type_id") == eve_type.id:
                return _empty_response()
            return _market_response(5.0)

        mock_esi_orders.side_effect = side_effect

        variants = get_item_value_variants(eve_type, 1)
        assert "market" not in variants
        assert variants["reprocessed"] == Decimal("50.00") or variants["reprocessed"] == Decimal("50.0")

    def test_empty_when_no_market_and_not_reprocessable(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _empty_response()
        assert get_item_value_variants(eve_type, 1) == {}


class TestCalculatePriceDensityTax:
    def test_no_tax_when_threshold_disabled(self):
        program = MagicMock(price_density_threshold=0.0, price_density_tax_percent=10.0)
        tax = calculate_price_density_tax(Decimal("100.00"), 50.0, program)
        assert tax == Decimal("0.00")

    def test_no_tax_above_threshold(self):
        program = MagicMock(price_density_threshold=1.0, price_density_tax_percent=10.0)
        # density = 100/50 = 2.0 isk/m3, above the 1.0 threshold -> no tax
        tax = calculate_price_density_tax(Decimal("100.00"), 50.0, program)
        assert tax == Decimal("0.00")

    def test_tax_applied_below_threshold(self):
        program = MagicMock(price_density_threshold=10.0, price_density_tax_percent=20.0)
        # density = 100/50 = 2.0 isk/m3, below the 10.0 threshold -> taxed
        tax = calculate_price_density_tax(Decimal("100.00"), 50.0, program)
        assert tax == Decimal("20.00")

    def test_no_tax_when_no_volume(self):
        program = MagicMock(price_density_threshold=10.0, price_density_tax_percent=20.0)
        tax = calculate_price_density_tax(Decimal("100.00"), 0, program)
        assert tax == Decimal("0.00")


@pytest.mark.django_db
class TestCalculateBuybackQuote:
    def test_picks_best_of_market_and_reprocessed(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=1000
        )

        def side_effect(url, params=None, **kwargs):
            if params.get("type_id") == eve_type.id:
                return _market_response(10.0)  # market: 10.0/unit
            return _market_response(1.0)  # tritanium: 1.0/unit -> reprocessed 1000.0/unit

        mock_esi_orders.side_effect = side_effect

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert details[0]["value_source"] == "reprocessed"
        assert total == Decimal("1000.00")

    def test_positive_price_modifier_increases_payout(self, mock_esi_orders):
        program = BuybackProgramFactory(price_modifier_percent=10.0)
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("110.00")

    def test_negative_price_modifier_decreases_payout(self, mock_esi_orders):
        program = BuybackProgramFactory(price_modifier_percent=-10.0)
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("90.00")

    def test_watchlist_blocking_item_excluded_from_total(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        BuybackWatchlistItemFactory(program=program, eve_type=eve_type, blocks_submission=True)
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("0.00")
        assert details[0]["blocked"] is True

    def test_watchlist_non_blocking_item_included_but_flagged(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        BuybackWatchlistItemFactory(program=program, eve_type=eve_type, blocks_submission=False)
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("100.00")
        assert details[0]["blocked"] is False
        assert details[0]["flagged"] is True

    def test_empty_input_returns_zero(self, mock_esi_orders):
        program = BuybackProgramFactory()
        total, details = calculate_buyback_quote({}, program)
        assert total == Decimal("0.00")
        assert details == []

    def test_unrecognized_valuation_logs_and_returns_zero_not_raise(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _empty_response()

        total, details = calculate_buyback_quote({eve_type: 3}, program)
        assert total == Decimal("0.00")
        assert details[0]["unit_price"] == Decimal("0.00")
