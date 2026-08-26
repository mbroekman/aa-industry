# Standard Library
import os

# Django
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings")
django.setup()

# Third Party
from eveuniverse.models import EveIndustryActivityProduct  # noqa: E402

# AA Industry App
from industry_reforged.models import CorporationIndustryJob  # noqa: E402

job = CorporationIndustryJob.objects.filter(
    product_type__name="Plasmonic Metamaterials"
).first()
if job:
    print(f"Found job: {job}")
    print(
        f"bp_type: {job.blueprint_type_id}, prod_type: {job.product_type_id}, activity: {job.activity_id}, runs: {job.runs}"
    )

    bp_prod = EveIndustryActivityProduct.objects.filter(
        eve_type_id=job.blueprint_type_id,
        product_eve_type_id=job.product_type_id,
        activity_id=job.activity_id,
    ).first()

    if bp_prod:
        print(f"bp_prod quantity: {bp_prod.quantity}")
    else:
        print("NO bp_prod FOUND")
else:
    print("No job found")
