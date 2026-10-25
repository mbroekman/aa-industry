# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.pricing_engine import (
    calculate_bom_cost,
    calculate_percentile_price,
    calculate_quote,
    calculate_structure_job_costs,
    fetch_single_market_price,
    fetch_system_cost_indices,
    get_detailed_prices,
    get_fuzzwork_prices,
    get_market_prices,
    get_prices_with_overrides,
)

from .factories import (
    CorpPricingConfigFactory,
    EveCorporationInfoFactory,
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


class TestCalculatePercentilePrice:
    def test_empty_orders_returns_zero(self):
        assert calculate_percentile_price([]) == 0.0

    def test_only_buy_orders_returns_zero(self):
        orders = [
            {
                "price": 100.0,
                "volume_remain": 1000,
                "is_buy_order": True,
                "location_id": 60003760,
            }
        ]
        assert calculate_percentile_price(orders) == 0.0

    def test_single_sell_order(self):
        orders = [
            {
                "price": 150.0,
                "volume_remain": 500,
                "is_buy_order": False,
                "location_id": 60003760,
            }
        ]
        assert calculate_percentile_price(orders) == 150.0

    def test_percentile_calculation_across_multiple_orders(self):
        # Total volume = 1000. 5% threshold = 50.
        # Order 1: price 10.0, volume 20 -> cum = 20 (< 50)
        # Order 2: price 12.0, volume 100 -> cum = 120 (>= 50) -> returns 12.0
        # Order 3: price 20.0, volume 880
        orders = [
            {
                "price": 20.0,
                "volume_remain": 880,
                "is_buy_order": False,
                "location_id": 60003760,
            },
            {
                "price": 10.0,
                "volume_remain": 20,
                "is_buy_order": False,
                "location_id": 60003760,
            },
            {
                "price": 12.0,
                "volume_remain": 100,
                "is_buy_order": False,
                "location_id": 60003760,
            },
        ]
        assert calculate_percentile_price(orders, percentile=0.05) == 12.0

    def test_prefers_jita_station_over_other_regional_stations(self):
        orders = [
            # Cheaper in another system/station
            {
                "price": 5.0,
                "volume_remain": 1000,
                "is_buy_order": False,
                "location_id": 60000001,
            },
            # Jita 4-4 station
            {
                "price": 10.0,
                "volume_remain": 1000,
                "is_buy_order": False,
                "location_id": 60003760,
            },
        ]
        assert calculate_percentile_price(orders, station_id=60003760) == 10.0


@pytest.mark.django_db
class TestPricingEngine:
    def test_get_market_prices_from_esi(self, mock_esi_orders):
        # Mocking the JSON response from ESI for type 34 and 35
        def side_effect(url, params=None, **kwargs):
            mock_res = MagicMock()
            mock_res.status_code = 200
            type_id = params.get("type_id")
            if type_id == 34:
                mock_res.json.return_value = [
                    {
                        "price": 12.5,
                        "volume_remain": 1000,
                        "is_buy_order": False,
                        "location_id": 60003760,
                    }
                ]
            elif type_id == 35:
                mock_res.json.return_value = [
                    {
                        "price": 25.0,
                        "volume_remain": 1000,
                        "is_buy_order": False,
                        "location_id": 60003760,
                    }
                ]
            else:
                mock_res.json.return_value = []
            return mock_res

        mock_esi_orders.side_effect = side_effect

        prices = get_market_prices([34, 35])
        assert prices[34] == 12.5
        assert prices[35] == 25.0

        # Backwards compatibility alias
        assert get_fuzzwork_prices([34, 35]) == {34: 12.5, 35: 25.0}

    def test_fallback_to_evetype_price_on_esi_failure(self, mock_esi_orders):
        mock_res = MagicMock()
        mock_res.status_code = 500
        mock_esi_orders.return_value = mock_res

        # Third Party
        from eveuniverse.models import EveMarketPrice

        type_fallback = EveTypeFactory(id=999)
        EveMarketPrice.objects.update_or_create(
            eve_type=type_fallback,
            defaults={
                "average_price": Decimal("42.00"),
                "adjusted_price": Decimal("42.00"),
            },
        )

        price = fetch_single_market_price(type_fallback.id)
        assert price == 42.0

    @patch("industry_reforged.utils.pricing_engine.get_market_prices")
    def test_get_prices_with_overrides(self, mock_get_market):
        mock_get_market.return_value = {34: 12.0, 35: 25.0}

        corp = EveCorporationInfoFactory()

        # AA Industry App
        from industry_reforged.models import CorpItemConfig

        type_34 = EveTypeFactory(id=34)
        CorpItemConfig.objects.create(
            corporation=corp, item_type=type_34, manual_price=Decimal("15.50")
        )

        prices = get_prices_with_overrides([34, 35], corporation=corp)

        # ID 34 should be overridden, 35 should remain from market
        assert prices[34] == 15.50
        assert prices[35] == 25.0

    @patch("industry_reforged.utils.pricing_engine.get_market_prices")
    def test_get_detailed_prices(self, mock_get_market):
        mock_get_market.return_value = {34: 12.0, 35: 25.0}
        corp = EveCorporationInfoFactory()

        # AA Industry App
        from industry_reforged.models import CorpItemConfig

        type_34 = EveTypeFactory(id=34)
        CorpItemConfig.objects.create(
            corporation=corp, item_type=type_34, manual_price=Decimal("18.00")
        )

        detailed = get_detailed_prices([34, 35], corporation=corp)
        assert detailed[34]["original_jita_price"] == 12.0
        assert detailed[34]["final_price"] == 18.0
        assert detailed[35]["original_jita_price"] == 25.0
        assert detailed[35]["final_price"] == 25.0

    @patch("industry_reforged.utils.pricing_engine.get_prices_with_overrides")
    def test_calculate_quote(self, mock_overrides):
        type_a = EveTypeFactory(id=101)
        type_b = EveTypeFactory(id=102)

        # Baseline prices
        mock_overrides.return_value = {101: 100.0, 102: 50.0}

        corp = EveCorporationInfoFactory()
        config = CorpPricingConfigFactory(
            corporation=corp,
            default_discount_percent=10.0,  # 10% global discount
        )

        # AA Industry App
        from industry_reforged.models import CorpTypeDiscount

        CorpTypeDiscount.objects.create(
            config=config, eve_type=type_b, discount_percent=20.0
        )

        parsed_items = {
            type_a: 2,  # 2 * 100 * 0.9 = 180
            type_b: 10,  # 10 * 50 * 0.8 = 400
        }

        total_price, item_details = calculate_quote(parsed_items, corp)

        assert total_price == Decimal("580.00")
        assert len(item_details) == 2

        for detail in item_details:
            if detail["eve_type"] == type_a:
                assert detail["discount_percent"] == 10.0
                assert detail["final_price_per_unit"] == Decimal("90.00")
                assert detail["line_total"] == Decimal("180.00")
            elif detail["eve_type"] == type_b:
                assert detail["discount_percent"] == 20.0
                assert detail["final_price_per_unit"] == Decimal("40.00")
                assert detail["line_total"] == Decimal("400.00")

    def test_calculate_percentile_price_filters_lowball_troll_buy_orders(self):
        # A genuine buy order exists, along with a massive 0.01 troll order
        orders = [
            {
                "price": 1000.0,
                "volume_remain": 500,
                "is_buy_order": True,
                "location_id": 60003760,
            },
            {
                "price": 950.0,
                "volume_remain": 1000,
                "is_buy_order": True,
                "location_id": 60003760,
            },
            {
                "price": 0.01,
                "volume_remain": 100_000_000,  # massive troll volume
                "is_buy_order": True,
                "location_id": 60003760,
            },
        ]
        price = calculate_percentile_price(orders, percentile=0.05, order_type="buy")
        assert price >= 950.0
        assert price != 0.01

    def test_fetch_single_market_price_buy_fallback_to_sell_on_illiquid_book(
        self, mock_esi_orders
    ):
        # ESI returns high sell orders but only a 0.01 buy order
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = [
            {
                "price": 5000.0,
                "volume_remain": 100,
                "is_buy_order": False,
                "location_id": 60003760,
            },
            {
                "price": 0.01,
                "volume_remain": 1000,
                "is_buy_order": True,
                "location_id": 60003760,
            },
        ]
        mock_esi_orders.return_value = mock_res

        # Requesting buy price should reject 0.01 and fallback to sell price 5000.0
        price = fetch_single_market_price(9999, order_type="buy")
        assert price == 5000.0

    def test_fetch_system_cost_indices_fallback(self):
        # Django
        from django.core.cache import cache

        cache.clear()

        with patch("requests.get", side_effect=Exception("ESI down")):
            indices = fetch_system_cost_indices(solar_system_id=30004582)
            assert indices["manufacturing"] == 0.02
            assert indices["reaction"] == 0.01

    def test_fetch_system_cost_indices_caching(self):
        # Django
        from django.core.cache import cache

        cache.clear()

        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = [
            {
                "solar_system_id": 30004582,
                "cost_indices": [
                    {"activity": "manufacturing", "cost_index": 0.0266},
                    {"activity": "reaction", "cost_index": 0.0083},
                ],
            }
        ]
        with patch("requests.get", return_value=mock_res):
            indices = fetch_system_cost_indices(solar_system_id=30004582)
            assert indices["manufacturing"] == 0.0266
            assert indices["reaction"] == 0.0083

            # Second call should use cache without calling requests.get
            with patch("requests.get") as mock_get_again:
                cached_indices = fetch_system_cost_indices(solar_system_id=30004582)
                mock_get_again.assert_not_called()
                assert cached_indices["manufacturing"] == 0.0266

    def test_calculate_structure_job_costs(self):
        # Third Party
        from eveuniverse.models import EveMarketPrice

        # AA Industry App
        from industry_reforged.models import IndustryFacility, TaxConfig

        corp = EveCorporationInfoFactory(corporation_id=123)
        TaxConfig.objects.create(corporation=corp, industry_tax_rate=10.0)

        fac = IndustryFacility.objects.create(
            facility_id=1001,
            name="Test Sotiyo",
            owner_id=corp.corporation_id,
            solar_system_id=30004582,
            is_default=True,
        )

        prod_type = EveTypeFactory(id=88001, name="Titan Hull")
        EveMarketPrice.objects.create(
            eve_type=prod_type,
            adjusted_price=Decimal("10000000.00"),  # 10M EIV
        )

        mock_tree = [
            {
                "type_id": prod_type.id,
                "name": prod_type.name,
                "quantity": 1,
                "activity_id": 1,
                "sub_materials": [
                    {
                        "type_id": 999,
                        "name": "Raw Ore",
                        "quantity": 100,
                        "sub_materials": [],
                    }
                ],
            }
        ]

        with patch(
            "industry_reforged.utils.pricing_engine.fetch_system_cost_indices",
            return_value={"manufacturing": 0.02, "reaction": 0.01},
        ):
            # Fee: 10,000,000 * 1 * 0.02 (SCI) * 1.10 (Tax) = 220,000.00 ISK
            fees = calculate_structure_job_costs(
                mock_tree, target_facility=fac, corporation=corp
            )
            assert fees == Decimal("220000.00")

    def test_calculate_bom_cost_blueprint_ownership_rules(self):
        # AA Industry App
        from industry_reforged.models import CorpBlueprint

        corp = EveCorporationInfoFactory(corporation_id=456)
        owned_bp = EveTypeFactory(id=77001, name="Owned BPO")
        unowned_bp = EveTypeFactory(id=77002, name="Unowned BPO")

        # Corp owns owned_bp
        CorpBlueprint.objects.create(
            corporation=corp, eve_type=owned_bp, item_id=10, location_id=20, runs=-1
        )

        # Mock recursive bom tree containing both blueprints and a raw material
        mock_tree = {
            "type_id": 8888,
            "name": "Finished Ship",
            "quantity": 1,
            "activity_id": 1,
            "sub_materials": [
                {
                    "type_id": owned_bp.id,
                    "name": owned_bp.name,
                    "quantity": 1,
                    "activity_id": 5,
                    "sub_materials": [],
                },
                {
                    "type_id": unowned_bp.id,
                    "name": unowned_bp.name,
                    "quantity": 1,
                    "activity_id": 5,
                    "sub_materials": [],
                },
                {
                    "type_id": 34,
                    "name": "Tritanium",
                    "quantity": 1000,
                    "activity_id": 0,
                    "sub_materials": [],
                },
            ],
        }

        with (
            patch(
                "industry_reforged.utils.bom_engine.get_recursive_bom_tree",
                return_value=mock_tree,
            ),
            patch(
                "industry_reforged.utils.pricing_engine.get_market_prices",
                return_value={
                    owned_bp.id: 1_000_000_000.0,
                    unowned_bp.id: 50_000_000.0,
                    34: 5.0,
                },
            ),
            patch(
                "industry_reforged.utils.pricing_engine.calculate_structure_job_costs",
                return_value=Decimal("0.00"),
            ),
        ):
            parsed_items = {EveTypeFactory(id=8888): 1}
            total_cost = calculate_bom_cost(parsed_items, corporation=corp)
            # Owned BPO (1 Billion) = 0 ISK
            # Unowned BPO = 50 Million ISK
            # Tritanium (1000 * 5) = 5,000 ISK
            # Total = 50,005,000.00 ISK
            assert total_cost == Decimal("50005000.00")
