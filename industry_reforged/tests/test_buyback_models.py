# Standard Library
from decimal import Decimal

# Third Party
import pytest

from .factories import BuybackContractFactory, BuybackContractItemFactory, EveTypeFactory


@pytest.mark.django_db
class TestBuybackContractProperties:
    def test_gross_appraisal_adds_back_donation(self):
        contract = BuybackContractFactory(quoted_price=Decimal("900.00"), donation_amount=Decimal("100.00"))
        assert contract.gross_appraisal == Decimal("1000.00")

    def test_base_appraisal_total_sums_item_base_line_totals(self):
        contract = BuybackContractFactory(quoted_price=Decimal("180.00"))
        eve_type_a = EveTypeFactory()
        eve_type_b = EveTypeFactory()
        BuybackContractItemFactory(
            contract=contract, eve_type=eve_type_a, quantity=2,
            unit_price=Decimal("90.00"), base_unit_price=Decimal("100.00"),
        )
        BuybackContractItemFactory(
            contract=contract, eve_type=eve_type_b, quantity=1,
            unit_price=Decimal("45.00"), base_unit_price=Decimal("50.00"),
        )

        # base totals: 2*100 + 1*50 = 250
        assert contract.base_appraisal_total == Decimal("250.00")

    def test_base_appraisal_total_zero_without_items(self):
        contract = BuybackContractFactory()
        assert contract.base_appraisal_total == Decimal("0.00")

    def test_modifier_impact_negative_for_a_discount(self):
        contract = BuybackContractFactory(quoted_price=Decimal("90.00"), donation_amount=Decimal("0.00"))
        BuybackContractItemFactory(
            contract=contract, quantity=1,
            unit_price=Decimal("90.00"), base_unit_price=Decimal("100.00"),
        )
        # base 100 - gross_appraisal 90 = -10 (the modifier cost the member 10 ISK)
        assert contract.modifier_impact == Decimal("-10.00")

    def test_modifier_impact_positive_for_a_bonus(self):
        contract = BuybackContractFactory(quoted_price=Decimal("110.00"), donation_amount=Decimal("0.00"))
        BuybackContractItemFactory(
            contract=contract, quantity=1,
            unit_price=Decimal("110.00"), base_unit_price=Decimal("100.00"),
        )
        assert contract.modifier_impact == Decimal("10.00")

    def test_modifier_impact_accounts_for_donation_too(self):
        # base 100, donated 20, net quoted_price 80 -> gross_appraisal = 100 -> modifier_impact = 0
        contract = BuybackContractFactory(quoted_price=Decimal("80.00"), donation_amount=Decimal("20.00"))
        BuybackContractItemFactory(
            contract=contract, quantity=1,
            unit_price=Decimal("100.00"), base_unit_price=Decimal("100.00"),
        )
        assert contract.modifier_impact == Decimal("0.00")

    def test_base_line_total_on_item(self):
        item = BuybackContractItemFactory(quantity=3, base_unit_price=Decimal("25.00"))
        assert item.base_line_total == Decimal("75.00")
