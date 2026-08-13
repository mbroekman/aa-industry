# Django
from django.db import migrations
from django.utils import timezone


def restore_active_jobs(apps, schema_editor):
    CorporationIndustryJob = apps.get_model(
        "industry_reforged", "CorporationIndustryJob"
    )
    CharacterIndustryJob = apps.get_model("industry_reforged", "CharacterIndustryJob")

    now = timezone.now()

    # Restore Corporation jobs that were incorrectly marked as delivered
    # but still have an end_date in the future.
    CorporationIndustryJob.objects.filter(status="delivered", end_date__gt=now).update(
        status="active"
    )

    # Do the same for Character jobs, just in case they suffered the same fate.
    CharacterIndustryJob.objects.filter(status="delivered", end_date__gt=now).update(
        status="active"
    )


def reverse_restore_active_jobs(apps, schema_editor):
    # Reversing this is not strictly possible or desired, since it was a bug fix.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("industry_reforged", "0042_migrate_existing_transactions"),
    ]

    operations = [
        migrations.RunPython(restore_active_jobs, reverse_restore_active_jobs),
    ]
