# Django
from django.core.management.base import BaseCommand

# AA Industry App
from industry_reforged.models import CorpInventory
from industry_reforged.tasks.inventory import task_sync_corp_inventory


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Before sync:", CorpInventory.objects.count(), "items")
        try:
            task_sync_corp_inventory()
            print("Done")
        except Exception as e:
            print("Error:", e)
            # Standard Library
            import traceback

            traceback.print_exc()
        print("After sync:", CorpInventory.objects.count(), "items")
        for i in CorpInventory.objects.all()[:10]:
            print(i)
