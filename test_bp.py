# Standard Library
import os

# Django
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings")
django.setup()

# Third Party
from eveuniverse.models import (  # noqa: E402
    EveIndustryActivity,
    EveIndustryActivityProduct,
    EveType,
)

product = EveType.objects.get(name="Federation Navy Comet")
bps = EveIndustryActivityProduct.objects.filter(product_eve_type=product, activity_id=1)
for bp_prod in bps:
    print(f"Faction BP: {bp_prod.eve_type.name}")
    try:
        has_me = EveIndustryActivity.objects.filter(
            eve_type=bp_prod.eve_type, activity_id=4
        ).exists()
        print(f"Has ME Activity: {has_me}")
    except Exception as e:
        print(f"Error checking ME: {e}")

product_t1 = EveType.objects.get(name="Incursus")
bps_t1 = EveIndustryActivityProduct.objects.filter(
    product_eve_type=product_t1, activity_id=1
)
for bp_prod in bps_t1:
    print(f"T1 BP: {bp_prod.eve_type.name}")
    try:
        has_me = EveIndustryActivity.objects.filter(
            eve_type=bp_prod.eve_type, activity_id=4
        ).exists()
        print(f"Has ME Activity: {has_me}")
    except Exception as e:
        print(f"Error checking ME: {e}")
