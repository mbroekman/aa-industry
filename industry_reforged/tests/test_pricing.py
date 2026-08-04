# Standard Library
from decimal import Decimal
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.pricing_engine import (
    calculate_quote,
    get_fuzzwork_prices,
    get_prices_with_overrides,
)

from .factories import (
    CorpPricingConfigFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
)


@pytest.fixture
def mock_fuzzwork():
    with patch("industry_reforged.utils.pricing_engine.requests.get") as mock_get:
        yield mock_get


@pytest.mark.django_db
class TestPricingEngine:
    def test_get_fuzzwork_prices(self, mock_fuzzwork):
        # Mocking the JSON response from fuzzwork
        mock_response = mock_fuzzwork.return_value
        mock_response.json.return_value = {
            "34": {"sell": {"min": 10.0, "percentile": 12.0}},
            "35": {"sell": {"min": 20.0, "percentile": 25.0}},
        }

        # Test basic fetching
        prices = get_fuzzwork_prices([34, 35])
        assert prices[34] == 12.0
        assert prices[35] == 25.0

    @patch("industry_reforged.utils.pricing_engine.get_fuzzwork_prices")
    def test_get_prices_with_overrides(self, mock_get_fw):
        # Mocking fuzzwork baseline
        mock_get_fw.return_value = {34: 12.0, 35: 25.0}

        corp = EveCorporationInfoFactory()

        # We need a CorpItemConfig to test manual override
        # AA Industry App
        from industry_reforged.models import CorpItemConfig

        type_34 = EveTypeFactory(id=34)
        CorpItemConfig.objects.create(
            corporation=corp, item_type=type_34, manual_price=Decimal("15.50")
        )

        prices = get_prices_with_overrides([34, 35], corporation=corp)

        # ID 34 should be overridden, 35 should remain from fuzzwork
        assert prices[34] == 15.50
        assert prices[35] == 25.0

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

        # Let's add a specific type discount for type_b of 20%
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
