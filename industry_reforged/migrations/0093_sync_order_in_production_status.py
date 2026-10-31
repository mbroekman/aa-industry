"""Move ACCEPTED orders that already have work started to IN_PRODUCTION.

Before this release no code ever set an order to IN_PRODUCTION, so existing orders
with claimed or completed tasks (or bought items) are still ACCEPTED.
"""

# Django
from django.db import migrations
from django.db.models import Q


def forwards(apps, schema_editor):
    MemberOrder = apps.get_model("industry_reforged", "MemberOrder")
    ProductionTask = apps.get_model("industry_reforged", "ProductionTask")
    OrderItem = apps.get_model("industry_reforged", "OrderItem")

    for root in MemberOrder.objects.filter(
        parent_order__isnull=True, status="ACCEPTED"
    ):
        started = (
            ProductionTask.objects.filter(
                Q(created_from_order=root) | Q(created_from_order__parent_order=root),
                status__in=["IN_PRODUCTION", "COMPLETED"],
            ).exists()
            or OrderItem.objects.filter(
                Q(order=root) | Q(order__parent_order=root), is_bought=True
            ).exists()
        )
        if started:
            MemberOrder.objects.filter(Q(id=root.id) | Q(parent_order=root)).update(
                status="IN_PRODUCTION"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("industry_reforged", "0092_webhook_discord_language"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
