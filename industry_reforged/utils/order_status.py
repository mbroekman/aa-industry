"""Keep a member order's ACCEPTED / IN_PRODUCTION status in step with its work."""

# Django
from django.db.models import Q

# Statuses this sync may switch between; others (READY, DELIVERED, ...) are left alone.
SYNCABLE_STATUSES = ("ACCEPTED", "IN_PRODUCTION")
STARTED_TASK_STATUSES = ("IN_PRODUCTION", "COMPLETED")


def order_work_started(root) -> bool:
    """True if any task of the order family is claimed or done, or a buy item is bought."""
    # AA Industry App
    from industry_reforged.models import OrderItem, ProductionTask

    family = Q(created_from_order=root) | Q(created_from_order__parent_order=root)
    if ProductionTask.objects.filter(
        family, status__in=STARTED_TASK_STATUSES
    ).exists():
        return True
    return OrderItem.objects.filter(
        Q(order=root) | Q(order__parent_order=root), is_bought=True
    ).exists()


def sync_order_production_status(order) -> bool:
    """Move the root order between ACCEPTED and IN_PRODUCTION. Returns True if it changed."""
    if order is None:
        return False
    root = order.root_order
    root.refresh_from_db(fields=["status"])
    if root.status not in SYNCABLE_STATUSES:
        return False
    wanted = "IN_PRODUCTION" if order_work_started(root) else "ACCEPTED"
    if root.status == wanted:
        return False
    root.status = wanted
    root.save()  # save() propagates the status to the sub-orders
    return True


def sync_orders_for_tasks(tasks) -> None:
    """Sync every distinct order the given tasks were created from."""
    seen = set()
    for task in tasks:
        order = task.created_from_order
        if order is None:
            continue
        root_id = order.parent_order_id or order.id
        if root_id in seen:
            continue
        seen.add(root_id)
        sync_order_production_status(order)
