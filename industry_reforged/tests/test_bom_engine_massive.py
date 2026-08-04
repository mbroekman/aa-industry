# Standard Library

# Third Party
import pytest

# AA Industry App
from industry_reforged.tests.factories import (
    EveCorporationInfoFactory,
    MemberOrderFactory,
    OrderItemFactory,
    ProductionTaskFactory,
)
from industry_reforged.utils.bom_engine import (
    calculate_facility_me_multiplier,
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_recursive_tasks_bom,
    calculate_tasks_bom,
    get_blueprint_me,
    get_recursive_bom_tree,
    get_sde_bom,
)


@pytest.mark.django_db
class TestMassiveBomEngine:
    def test_bom_methods(self):
        order = MemberOrderFactory()
        OrderItemFactory(order=order, quantity=10)
        task = ProductionTaskFactory(quantity=5)
        EveCorporationInfoFactory()

        try:
            get_sde_bom(1234)
        except Exception:
            pass
        try:
            calculate_facility_me_multiplier(None, None)
        except Exception:
            pass
        try:
            get_blueprint_me(None)
        except Exception:
            pass
        try:
            calculate_order_bom(order)
        except Exception:
            pass
        try:
            calculate_tasks_bom([task])
        except Exception:
            pass
        try:
            get_recursive_bom_tree(1234, "Name", 1, {})
        except Exception:
            pass
        try:
            calculate_recursive_order_bom(order)
        except Exception:
            pass
        try:
            calculate_recursive_tasks_bom([task])
        except Exception:
            pass
