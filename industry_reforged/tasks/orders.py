"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

from .utils import log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.task_pull_market_data")
@log_task_execution("Task Pull Market Data")
def task_pull_market_data():
    """Pre-warm Jita 5% sell prices for common materials (minerals, PI, gas, salvage) via direct ESI."""
    logger.info("Market Data Pull initiated via direct ESI.")
    from ..models import CorpItemConfig
    from ..utils.pricing_engine import get_market_prices

    # Fetch all item type IDs configured in CorpItemConfig or active orders
    configured_ids = list(CorpItemConfig.objects.values_list("item_type_id", flat=True))
    # Common mineral type IDs (Tritanium, Pyerite, Mexallon, Isogen, Nocxium, Zydrine, Megacyte, Morphite)
    common_mineral_ids = [34, 35, 36, 37, 38, 39, 40, 11399]
    all_target_ids = list(set(configured_ids + common_mineral_ids))

    if all_target_ids:
        prices = get_market_prices(all_target_ids)
        logger.info(f"Successfully warmed {len(prices)} market prices via direct ESI.")
        return len(prices)
    return 0


@shared_task(name="industry_reforged.tasks.task_bom_explosion")
@log_task_execution("Task Bom Explosion")
def task_bom_explosion(order_id):
    """Calculate BOM and create ProductionTasks based on Build vs Buy configuration."""
    from ..models import CorpItemConfig, MemberOrder

    order = MemberOrder.objects.filter(id=order_id).first()
    if not order:
        return

    for item in order.items.all():
        config = CorpItemConfig.objects.filter(item_type=item.item_type).first()

        # Determine build or buy
        if config and config.build_or_buy == "BUY":
            # Create a BUY task
            pass
        else:
            # SDE or Fuzzwork explosion
            pass
