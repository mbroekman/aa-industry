import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings")
django.setup()

from industry_reforged.tasks.inventory import task_sync_corp_inventory
task_sync_corp_inventory()
