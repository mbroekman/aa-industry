# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.tests.factories import (
    EveTypeFactory,
    MemberOrderFactory,
    OrderItemFactory,
    ProductionTaskFactory,
)
from industry_reforged.utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_tasks_bom,
    get_recursive_bom_tree,
)


@pytest.mark.django_db
class TestBomEngineMore:

    @patch("industry_reforged.utils.bom_engine.get_sde_bom")
    @patch("industry_reforged.utils.bom_engine.get_blueprint_me")
    def test_calculate_order_bom(self, mock_bp_me, mock_get_sde):
        order = MemberOrderFactory(id=10)
        item_type = EveTypeFactory(name="Test Ship")
        OrderItemFactory(order=order, item_type=item_type, quantity=2)

        mock_get_sde.return_value = (
            [
                {"typeid": 34, "name": "Tritanium", "quantity": 100},
                {"typeid": 35, "name": "Pyerite", "quantity": 50},
            ],
            1,
            1,
        )

        mock_bp_me.return_value = (10, 1)

        res = calculate_order_bom(order)
        assert len(res) == 2
        assert res[34]["base_quantity"] == 200
        assert res[35]["base_quantity"] == 100

    @patch("industry_reforged.utils.bom_engine.get_sde_bom")
    @patch("industry_reforged.utils.bom_engine.get_blueprint_me")
    def test_calculate_tasks_bom(self, mock_bp_me, mock_get_sde):
        item_type = EveTypeFactory(name="Test Item")
        task1 = ProductionTaskFactory(item_type=item_type, quantity=3)
        task2 = ProductionTaskFactory(item_type=item_type, quantity=2)

        mock_get_sde.return_value = (
            [{"typeid": 34, "name": "Tritanium", "quantity": 10}],
            1,
            1,
        )
        mock_bp_me.return_value = (10, 1)

        res = calculate_tasks_bom([task1, task2])
        assert len(res) == 1
        assert res[34]["base_quantity"] == 50

    @patch("industry_reforged.utils.bom_engine.get_sde_bom")
    @patch("industry_reforged.utils.bom_engine.get_blueprint_me")
    def test_get_recursive_bom_tree(self, mock_bp_me, mock_get_sde):
        item_type = EveTypeFactory(name="Advanced Ship")

        def sde_bom_side_effect(type_id):
            if type_id == item_type.id:
                return ([{"typeid": 1000, "name": "Component A", "quantity": 2}], 1, 1)
            return ([{"typeid": 34, "name": "Tritanium", "quantity": 50}], 1, 1)

        mock_get_sde.side_effect = sde_bom_side_effect
        mock_bp_me.return_value = (10, 1)

        tree = get_recursive_bom_tree(item_type.id, 1, 10, {}, 1.0)
        assert tree is not None
        assert "sub_materials" in tree

    @patch("industry_reforged.utils.bom_engine.get_recursive_bom_tree")
    def test_calculate_recursive_order_bom(self, mock_tree):
        order = MemberOrderFactory(id=20)
        item_type = EveTypeFactory(name="Test Ship")
        OrderItemFactory(order=order, item_type=item_type, quantity=1)

        mock_tree.return_value = {
            "type_id": item_type.id,
            "name": "Test Ship",
            "quantity": 1,
            "materials": {
                34: {
                    "type_id": 34,
                    "name": "Tritanium",
                    "quantity": 100,
                    "materials": {},
                }
            },
        }

        flat_bom = calculate_recursive_order_bom(order)
        assert 34 in flat_bom[0]["materials"]
