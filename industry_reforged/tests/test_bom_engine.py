# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.tests.factories import (
    EveTypeFactory,
)
from industry_reforged.utils.bom_engine import (
    calculate_facility_me_multiplier,
    get_sde_bom,
)


@pytest.mark.django_db
class TestBomEngine:

    @patch(
        "industry_reforged.utils.bom_engine.EveIndustryActivityProduct.objects.filter"
    )
    @patch(
        "industry_reforged.utils.bom_engine.EveIndustryActivityMaterial.objects.filter"
    )
    def test_get_sde_bom_with_industry_activity(
        self, mock_material_filter, mock_product_filter
    ):
        # Mock product
        class MockProduct:
            eve_type_id = 100
            activity_id = 1
            quantity = 1

        mock_product_filter.return_value.first.return_value = MockProduct()

        # Mock material
        class MockEveType:
            name = "Tritanium"

        class MockMaterial:
            material_eve_type_id = 34
            material_eve_type = MockEveType()
            quantity = 100

        mock_material_filter.return_value.exists.return_value = True
        mock_material_filter.return_value.__iter__.return_value = [MockMaterial()]

        materials, yield_qty, _activity = get_sde_bom(200)

        assert yield_qty == 1
        assert len(materials) == 1
        assert materials[0]["typeid"] == 34
        assert materials[0]["quantity"] == 100
        assert materials[0]["name"] == "Tritanium"

    def test_calculate_facility_me_multiplier_no_facility(self):
        product_type = EveTypeFactory()
        mult = calculate_facility_me_multiplier(None, product_type)
        assert mult == 1.0

        mult, sec, rig = calculate_facility_me_multiplier(
            None, product_type, return_breakdown=True
        )
        assert mult == 1.0
        assert sec == 0.0
        assert rig == 0.0
