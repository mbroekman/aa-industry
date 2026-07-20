# Django
from django.core.management.base import BaseCommand

# AA Industry App
from industry_reforged.models import MemberOrder


class Command(BaseCommand):
    help = "Check orphaned orders"

    def handle(self, *args, **options):
        orders = MemberOrder.objects.all()
        orphans = []
        for o in orders:
            item_count = o.items.count()
            if item_count == 0 and o.parent_order_id is None:
                orphans.append(o)
                self.stdout.write(
                    f"Order {o.id} - Status: {o.status} - Items: {item_count} - Parent: {o.parent_order_id} - Character: {o.character}"
                )

        for o in orphans:
            self.stdout.write(f"Deleting order {o.id}...")
            o.delete()
        self.stdout.write("Done!")
