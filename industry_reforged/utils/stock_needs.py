"""What the corporation is short of: low-stock targets minus stock and work in progress."""

# Django
from django.db.models import Sum


def low_stock_rows(corporation) -> list[dict]:
    """One row per item whose stock plus open production tasks and buy orders
    is below its low-stock target (CorpItemConfig.target_threshold)."""
    from ..models import CorpBuyOrder, CorpInventory, CorpItemConfig, ProductionTask

    configs = CorpItemConfig.objects.filter(
        corporation=corporation, target_threshold__gt=0
    ).select_related("item_type")
    if not configs:
        return []

    stock = dict(
        CorpInventory.objects.filter(corporation=corporation, quantity__gt=0)
        .values("item_type_id")
        .annotate(total=Sum("quantity"))
        .values_list("item_type_id", "total")
    )
    open_tasks = dict(
        ProductionTask.objects.filter(
            created_from_order__isnull=True,
            bom_parent__isnull=True,
            status__in=["UNCLAIMED", "IN_PRODUCTION"],
        )
        .values("item_type_id")
        .annotate(total=Sum("quantity"))
        .values_list("item_type_id", "total")
    )
    open_buys = dict(
        CorpBuyOrder.objects.filter(
            corporation=corporation, status__in=["OPEN", "IN_PROGRESS"]
        )
        .values("item_type_id")
        .annotate(total=Sum("quantity"))
        .values_list("item_type_id", "total")
    )

    rows = []
    for config in configs:
        type_id = config.item_type_id
        current_qty = stock.get(type_id, 0)
        in_progress = open_tasks.get(type_id, 0) + open_buys.get(type_id, 0)
        effective_qty = current_qty + in_progress
        if effective_qty < config.target_threshold:
            rows.append(
                {
                    "item_type": config.item_type,
                    "current_qty": current_qty,
                    "in_progress": in_progress,
                    "target": config.target_threshold,
                    "deficit": config.target_threshold - effective_qty,
                    "build_or_buy": config.build_or_buy,
                }
            )
    return rows


def stock_deficits(corporation) -> dict[int, int]:
    """{type_id: units short} for everything below its low-stock target."""
    return {row["item_type"].id: row["deficit"] for row in low_stock_rows(corporation)}
