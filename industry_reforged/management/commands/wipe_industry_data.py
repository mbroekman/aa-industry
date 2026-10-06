# Django
from django.core.management.base import BaseCommand

# AA Industry App
from industry_reforged.models import (
    BuilderPayoutBatch, 
    MemberOrder, 
    ProductionTask,
    CorpBuyOrder
)

class Command(BaseCommand):
    help = "Wipes all industry MemberOrders, ProductionTasks, BuilderPayoutBatches, and CorpBuyOrders. Use with caution!"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("Starting wipe of Industry Reforged data...")
        )

        order_count = MemberOrder.objects.count()
        task_count = ProductionTask.objects.count()
        payout_count = BuilderPayoutBatch.objects.count()
        buy_order_count = CorpBuyOrder.objects.count()

        if order_count == 0 and task_count == 0 and payout_count == 0 and buy_order_count == 0:
            self.stdout.write(
                self.style.SUCCESS("Database is already clean. Nothing to delete.")
            )
            return

        self.stdout.write(
            f"Deleting {order_count} MemberOrders (and cascading items)..."
        )
        MemberOrder.objects.all().delete()

        remaining_tasks = ProductionTask.objects.count()
        if remaining_tasks > 0:
            self.stdout.write(
                f"Deleting {remaining_tasks} remaining ProductionTasks..."
            )
            ProductionTask.objects.all().delete()

        if payout_count > 0:
            self.stdout.write(f"Deleting {payout_count} BuilderPayoutBatches...")
            BuilderPayoutBatch.objects.all().delete()
            
        if buy_order_count > 0:
            self.stdout.write(f"Deleting {buy_order_count} CorpBuyOrders...")
            CorpBuyOrder.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("Successfully wiped all old orders, tasks, buy orders and payouts!")
        )
