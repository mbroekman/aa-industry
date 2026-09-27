import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings")
django.setup()
from industry_reforged.models import CorpBlueprint
print(f"Total blueprints: {CorpBlueprint.objects.count()}")
bpos = CorpBlueprint.objects.filter(quantity__gte=1)
print(f"BPOs (qty >= 1): {bpos.count()}")
bpcs = CorpBlueprint.objects.filter(quantity=-2)
print(f"BPCs (qty = -2): {bpcs.count()}")
bpcs2 = CorpBlueprint.objects.filter(runs__gte=1)
print(f"BPCs (runs >= 1): {bpcs2.count()}")
for bp in CorpBlueprint.objects.all()[:5]:
    print(f"ID: {bp.item_id}, Qty: {bp.quantity}, Runs: {bp.runs}, is_original: {bp.is_original}")
