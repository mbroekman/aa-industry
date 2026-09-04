# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.pricing_engine import (
    calculate_percentile_price,
    calculate_quote,
    fetch_single_market_price,
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
