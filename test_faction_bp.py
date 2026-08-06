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

# Let's find a faction product, e.g., "Federation Navy Comet" or "Vindicator"
product = EveType.objects.get(name="Federation Navy Comet")

print(f"Product: {product.name}")
bps = EveIndustryActivityProduct.objects.filter(product_eve_type=product, activity_id=1)
for bp_prod in bps:
    bp_type = bp_prod.eve_type
    print(f"Blueprint: {bp_type.name}")
    # Check if blueprint has ME research
    has_me_research = EveIndustryActivity.objects.filter(
        eve_type=bp_type, activity_id=4
    ).exists()
    print(f"Has ME research (activity 4): {has_me_research}")

# Let's find a normal T1 product
t1_product = EveType.objects.get(name="Incursus")
print(f"\nProduct: {t1_product.name}")
bps = EveIndustryActivityProduct.objects.filter(
    product_eve_type=t1_product, activity_id=1
)
for bp_prod in bps:
    bp_type = bp_prod.eve_type
    print(f"Blueprint: {bp_type.name}")
    has_me_research = EveIndustryActivity.objects.filter(
        eve_type=bp_type, activity_id=4
    ).exists()
    print(f"Has ME research (activity 4): {has_me_research}")
