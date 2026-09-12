# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.models import (
    AIMarketLog,
    Basket,
    BasketItem,
    ProductionTask,
)
from industry_reforged.tasks.ai_manager import evaluate_baskets

from .factories import EveCorporationInfoFactory, EveTypeFactory


@pytest.mark.django_db
class TestEvaluateBasketsTask:
    @patch("industry_reforged.utils.ai_engine.calculate_profitability")
    def test_evaluate_baskets_recreates_deleted_tasks_when_criteria_met(
        self, mock_profit
    ):
        # 1. Setup Corp, EveType, Basket and BasketItem
        corp = EveCorporationInfoFactory()
        eve_type = EveTypeFactory(id=587, name="Rifter")

        basket = Basket.objects.create(
            name="Combat Frigates",
            corporation=corp,
            is_active=True,
            min_profit_margin=10.0,
        )
        basket_item = BasketItem.objects.create(
            basket=basket,
            eve_type=eve_type,
            target_stock_level=10,
            batch_size=5,
        )

        # Mock profitability: margin 25%, sell 1M, build 800k (meets criteria >= 10%)
        mock_profit.return_value = (25.0, 1000000.0, 800000.0)

        # 2. First evaluation: No stock, no in-flight tasks -> creates ProductionTask(qty=10)
        evaluate_baskets(basket_id=basket.id)

        assert ProductionTask.objects.filter(item_type=eve_type).count() == 1
        task = ProductionTask.objects.filter(item_type=eve_type).first()
        assert task.quantity == 10
        assert task.status == "UNCLAIMED"

        log = AIMarketLog.objects.filter(basket_item=basket_item).first()
        assert log.action_taken == "Ordered"

        # 3. Second evaluation: Task is in flight -> skips creating duplicate
        evaluate_baskets(basket_id=basket.id)
        assert ProductionTask.objects.filter(item_type=eve_type).count() == 1
        latest_log = AIMarketLog.objects.filter(basket_item=basket_item).first()
        assert latest_log.action_taken == "Skipped"

        # 4. User/director deletes the task
        task.delete()
        assert ProductionTask.objects.filter(item_type=eve_type).count() == 0

        # 5. Third evaluation: Task is gone, stock is 0 -> detects shortage and recreates task
        evaluate_baskets(basket_id=basket.id)
        assert ProductionTask.objects.filter(item_type=eve_type).count() == 1
        new_task = ProductionTask.objects.filter(item_type=eve_type).first()
        assert new_task.quantity == 10
        assert new_task.status == "UNCLAIMED"
        recreated_log = AIMarketLog.objects.filter(basket_item=basket_item).first()
        assert recreated_log.action_taken == "Ordered"

        # 6. If task is deleted again, but profitability drops below min_margin (e.g. 5% < 10%), it skips
        new_task.delete()
        mock_profit.return_value = (5.0, 1000000.0, 950000.0)
        evaluate_baskets(basket_id=basket.id)
        assert ProductionTask.objects.filter(item_type=eve_type).count() == 0
        skipped_log = AIMarketLog.objects.filter(basket_item=basket_item).first()
        assert skipped_log.action_taken == "Skipped"
        assert "below minimum" in skipped_log.reason
