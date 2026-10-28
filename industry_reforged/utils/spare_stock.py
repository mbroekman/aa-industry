"""Spare stock for open order tasks: facility stock not already spoken for.

Order acceptance only deducts the stock that sits at the order's facility at that
moment. Items that show up later (left over from other work, or bought) never
reduce a task. This helper tells the builder how many of their item lie spare at
the order's facility, so they can decide to build fewer.

Output already made for open orders sits in the same hangar, so it is not spare:
- delivered EVE runs of tasks still being built;
- completed tasks whose parent has not consumed them yet.
"""

# Standard Library
from collections import defaultdict

# Django
from django.db.models import Sum

OPEN_ORDER_STATUSES = ("ACCEPTED", "IN_PRODUCTION")


def _facility_key(task):
    order = task.created_from_order
    if not order or not order.target_facility_id or not order.character_id:
        return None
    return (
        order.character.corporation_id,
        order.target_facility.facility_id,
        task.item_type_id,
    )


def _delivered_output(task) -> int:
    delivered = 0
    for link in task.linked_jobs.all():
        job = link.character_job or link.corporation_job
        if job and job.status == "delivered":
            delivered += link.linked_runs * task.portion_size
    return min(delivered, task.quantity)


def _parent_consumed(task) -> bool:
    parent = task.bom_parent
    if parent is None:
        return False
    if parent.status == "COMPLETED":
        return True
    return parent.status == "IN_PRODUCTION" and parent.linked_jobs.exists()


def _reserved_output(task) -> int:
    """How much of this task's output is in the hangar, waiting for its order."""
    if task.status == "COMPLETED":
        return 0 if _parent_consumed(task) else task.quantity
    return _delivered_output(task)


def annotate_spare_stock(tasks) -> None:
    """Set ``task.spare_stock_qty`` on each open order task (0 when none)."""
    # AA Industry App
    from industry_reforged.models import CorpInventory, ProductionTask

    keys = {}
    for task in tasks:
        task.spare_stock_qty = 0
        if task.status != "COMPLETED":
            key = _facility_key(task)
            if key:
                keys[task.pk] = key
    if not keys:
        return

    wanted = set(keys.values())
    stock = defaultdict(int)
    for corp_id, location_id, type_id in wanted:
        stock[(corp_id, location_id, type_id)] = (
            CorpInventory.objects.filter(
                corporation__corporation_id=corp_id,
                location_id=location_id,
                item_type_id=type_id,
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    reserved = defaultdict(int)
    open_tasks = (
        ProductionTask.objects.filter(
            created_from_order__status__in=OPEN_ORDER_STATUSES,
            created_from_order__target_facility__isnull=False,
            item_type_id__in={type_id for _, _, type_id in wanted},
        )
        .select_related(
            "item_type",
            "bom_parent",
            "created_from_order__character",
            "created_from_order__target_facility",
        )
        .prefetch_related(
            "linked_jobs__character_job",
            "linked_jobs__corporation_job",
        )
    )
    for other in open_tasks:
        key = _facility_key(other)
        if key in wanted:
            reserved[key] += _reserved_output(other)

    for task in tasks:
        key = keys.get(task.pk)
        if key:
            task.spare_stock_qty = max(0, stock[key] - reserved[key])
