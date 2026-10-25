# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest
from eveuniverse.models import EveCategory, EveTypeMaterial

# AA Industry App
from industry_reforged.utils.pricing_engine import (
    calculate_buyback_quote,
    calculate_price_density_tax,
    get_buyback_value_variants,
    get_reprocessing_value,
)

from .factories import (
    BuybackProgramFactory,
    BuybackWatchlistItemFactory,
    EveGroupFactory,
    EveTypeFactory,
)


def _ore_type(**kwargs):
    """An item in EVE's Asteroid category (ore, ice, moon ore)."""
    asteroid, _ = EveCategory.objects.get_or_create(
        id=25, defaults={"name": "Asteroid", "published": True}
    )
    return EveTypeFactory(eve_group=EveGroupFactory(eve_category=asteroid), **kwargs)


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
        {
            "price": price,
            "volume_remain": 1000,
            "is_buy_order": False,
            "location_id": 60003760,
        }
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

    def test_value_scaled_by_efficiency(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=100
        )
        mock_esi_orders.return_value = _market_response(10.0)

        value = get_reprocessing_value(eve_type, 2, efficiency=0.5)
        # 100 tritanium/unit * 10.0 isk * 2 units * 0.5 efficiency = 1000.0
        assert value == Decimal("1000.00") or value == Decimal("1000")

    def test_yield_is_per_portion(self, mock_esi_orders):
        """Ore yields are per 100 units; one unit yields a hundredth."""
        ore = _ore_type(portion_size=100)
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=ore, material_eve_type=tritanium, quantity=400
        )
        mock_esi_orders.return_value = _market_response(5.0)

        # 400 tritanium per 100 ore -> 4 per unit * 5 ISK * 1000 units = 20,000
        assert get_reprocessing_value(ore, 1000) == Decimal("20000")

    def test_price_overrides_win_over_market(self, mock_esi_orders):
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=10
        )
        mock_esi_orders.return_value = _market_response(5.0)

        value = get_reprocessing_value(
            eve_type, 1, price_overrides={tritanium.id: Decimal("7.00")}
        )
        assert value == Decimal("70.00")


@pytest.mark.django_db
class TestReprocessingPriceBasis:
    """Reprocessed materials follow the program's price type (TASK-272)."""

    def _setup(self):
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=10
        )
        return eve_type, tritanium

    def _prices(self, tritanium):
        table = {"buy": 4.0, "sell": 6.0}
        return lambda ids, order_type="sell": {tritanium.id: table[order_type]}

    @pytest.mark.parametrize(
        ("order_type", "expected"),
        [("buy", Decimal("40")), ("sell", Decimal("60")), ("split", Decimal("50"))],
    )
    def test_materials_use_the_requested_price_basis(self, order_type, expected):
        eve_type, tritanium = self._setup()
        with patch(
            "industry_reforged.utils.pricing_engine.get_market_prices",
            side_effect=self._prices(tritanium),
        ):
            value = get_reprocessing_value(eve_type, 1, order_type=order_type)
        assert value == expected


@pytest.mark.django_db
class TestGetBuybackValueVariants:
    def test_non_ore_is_valued_at_market_only(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=10
        )
        mock_esi_orders.return_value = _market_response(50.0)

        assert get_buyback_value_variants(eve_type, 1, program) == {
            "market": Decimal("50.0")
        }

    def test_order_type_buy_uses_buy_price(self, mock_esi_orders):
        program = BuybackProgramFactory(price_type="BUY")
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "price": 80.0,
                    "volume_remain": 100,
                    "is_buy_order": True,
                    "location_id": 60003760,
                },
                {
                    "price": 100.0,
                    "volume_remain": 100,
                    "is_buy_order": False,
                    "location_id": 60003760,
                },
            ],
        )

        assert get_buyback_value_variants(eve_type, 1, program) == {
            "market": Decimal("80.0")
        }

    def test_ore_offers_raw_and_refined(self, mock_esi_orders):
        program = BuybackProgramFactory(refining_rate=100.0)
        ore = _ore_type(portion_size=100)
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=ore, material_eve_type=tritanium, quantity=400
        )

        def side_effect(url, params=None, **kwargs):
            price = 15.0 if params.get("type_id") == ore.id else 5.0
            return _market_response(price)

        mock_esi_orders.side_effect = side_effect

        variants = get_buyback_value_variants(ore, 100, program)
        assert variants == {"market": Decimal("1500.0"), "refined": Decimal("2000")}

    def test_ore_toggles_switch_variants_off(self, mock_esi_orders):
        program = BuybackProgramFactory(
            use_raw_ore_value=False, use_refined_value=False
        )
        ore = _ore_type()
        mock_esi_orders.return_value = _market_response(15.0)

        assert get_buyback_value_variants(ore, 1, program) == {}

    def test_compressed_variant(self, mock_esi_orders):
        program = BuybackProgramFactory(
            use_raw_ore_value=False, use_refined_value=False, use_compressed_value=True
        )
        ore = _ore_type(name="Veldspar")
        compressed = _ore_type(name="Compressed Veldspar")

        def side_effect(url, params=None, **kwargs):
            if params.get("type_id") == compressed.id:
                return _market_response(30.0)
            return _empty_response()

        mock_esi_orders.side_effect = side_effect

        assert get_buyback_value_variants(ore, 10, program) == {
            "compressed": Decimal("300.0")
        }

    def test_t1_scrap_only_for_meta_level_up_to_four(self, mock_esi_orders):
        program = BuybackProgramFactory(
            use_reprocessed_value_for_t1=True, t1_refining_rate=50.0
        )
        module_category, _ = EveCategory.objects.get_or_create(
            id=7, defaults={"name": "Module", "published": True}
        )
        module = EveTypeFactory(
            eve_group=EveGroupFactory(eve_category=module_category)
        )
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=module, material_eve_type=tritanium, quantity=1000
        )
        mock_esi_orders.return_value = _market_response(1.0)

        meta_level = "industry_reforged.utils.buyback_data.meta_level"
        with patch(meta_level, return_value=0):
            assert get_buyback_value_variants(module, 1, program)["scrap"] == Decimal(
                "500"
            )
        with patch(meta_level, return_value=8):
            assert "scrap" not in get_buyback_value_variants(module, 1, program)
        with patch(meta_level, return_value=None):
            assert "scrap" not in get_buyback_value_variants(module, 1, program)


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
        program = MagicMock(
            price_density_threshold=10.0, price_density_tax_percent=20.0
        )
        # density = 100/50 = 2.0 isk/m3, below the 10.0 threshold -> taxed
        tax = calculate_price_density_tax(Decimal("100.00"), 50.0, program)
        assert tax == Decimal("20.00")

    def test_no_tax_when_no_volume(self):
        program = MagicMock(
            price_density_threshold=10.0, price_density_tax_percent=20.0
        )
        tax = calculate_price_density_tax(Decimal("100.00"), 0, program)
        assert tax == Decimal("0.00")


@pytest.mark.django_db
class TestCalculateBuybackQuote:
    def test_picks_best_of_market_and_refined(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = _ore_type()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=1000
        )

        def side_effect(url, params=None, **kwargs):
            if params.get("type_id") == eve_type.id:
                return _market_response(10.0)  # market: 10.0/unit
            return _market_response(
                1.0
            )  # tritanium: 1.0/unit -> reprocessed 1000.0/unit

        mock_esi_orders.side_effect = side_effect

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert details[0]["value_source"] == "refined"
        # refined is 1000.0/unit at 100% efficiency, scaled by the program's
        # default 90% refining_rate
        assert total == Decimal("900.00")

    def test_refining_rate_scales_refined_value(self, mock_esi_orders):
        program = BuybackProgramFactory(refining_rate=50.0)
        eve_type = _ore_type()
        tritanium = EveTypeFactory(name="Tritanium")
        EveTypeMaterial.objects.create(
            eve_type=eve_type, material_eve_type=tritanium, quantity=1000
        )

        def side_effect(url, params=None, **kwargs):
            if params.get("type_id") == eve_type.id:
                return _market_response(10.0)  # market: 10.0/unit
            return _market_response(
                1.0
            )  # tritanium: 1.0/unit -> reprocessed 1000.0/unit @ 100%

        mock_esi_orders.side_effect = side_effect

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert details[0]["value_source"] == "refined"
        assert total == Decimal("500.00")

    def test_price_type_split_averages_buy_and_sell(self, mock_esi_orders):
        program = BuybackProgramFactory(price_type="SPLIT")
        eve_type = EveTypeFactory()

        def side_effect(url, params=None, **kwargs):
            if params.get("order_type") == "all":
                return MagicMock(
                    status_code=200,
                    json=lambda: [
                        {
                            "price": 80.0,
                            "volume_remain": 100,
                            "is_buy_order": True,
                            "location_id": 60003760,
                        },
                        {
                            "price": 100.0,
                            "volume_remain": 100,
                            "is_buy_order": False,
                            "location_id": 60003760,
                        },
                    ],
                )
            return _empty_response()

        mock_esi_orders.side_effect = side_effect

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        # buy 80.0, sell 100.0 -> split 90.0/unit
        assert total == Decimal("90.00")

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

    def test_base_unit_price_reflects_pre_modifier_value(self, mock_esi_orders):
        program = BuybackProgramFactory(price_modifier_percent=-10.0)
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 2}, program)
        assert details[0]["base_unit_price"] == Decimal("100.00")
        assert details[0]["base_line_total"] == Decimal("200.00")
        assert details[0]["unit_price"] == Decimal("90.00")
        assert total == Decimal("180.00")

    def test_blocked_item_has_zero_base_price(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        BuybackWatchlistItemFactory(
            program=program, eve_type=eve_type, blocks_submission=True
        )
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert details[0]["base_unit_price"] == Decimal("0.00")
        assert details[0]["base_line_total"] == Decimal("0.00")

    def test_watchlist_blocking_item_excluded_from_total(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        BuybackWatchlistItemFactory(
            program=program, eve_type=eve_type, blocks_submission=True
        )
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("0.00")
        assert details[0]["blocked"] is True

    def test_watchlist_non_blocking_item_included_but_flagged(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        BuybackWatchlistItemFactory(
            program=program, eve_type=eve_type, blocks_submission=False
        )
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({eve_type: 1}, program)
        assert total == Decimal("100.00")
        assert details[0]["blocked"] is False
        assert details[0]["flagged"] is True

    def test_accepted_categories_block_items_from_other_categories(
        self, mock_esi_orders
    ):
        program = BuybackProgramFactory()
        accepted = EveTypeFactory()
        other = EveTypeFactory()
        program.accepted_categories.add(accepted.eve_group.eve_category)
        mock_esi_orders.return_value = _market_response(100.0)

        total, details = calculate_buyback_quote({accepted: 1, other: 1}, program)

        by_type = {d["eve_type"]: d for d in details}
        assert by_type[accepted]["blocked"] is False
        assert by_type[other]["blocked"] is True
        assert "category" in by_type[other]["blocked_reason"]
        assert total == Decimal("100.00")

    def test_empty_accepted_categories_accepts_everything(self, mock_esi_orders):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _market_response(100.0)

        _, details = calculate_buyback_quote({eve_type: 1}, program)

        assert details[0]["blocked"] is False

    def test_empty_input_returns_zero(self, mock_esi_orders):
        program = BuybackProgramFactory()
        total, details = calculate_buyback_quote({}, program)
        assert total == Decimal("0.00")
        assert details == []

    def test_unrecognized_valuation_logs_and_returns_zero_not_raise(
        self, mock_esi_orders
    ):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        mock_esi_orders.return_value = _empty_response()

        total, details = calculate_buyback_quote({eve_type: 3}, program)
        assert total == Decimal("0.00")
        assert details[0]["unit_price"] == Decimal("0.00")
