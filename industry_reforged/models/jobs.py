"""
App Models
"""

# Third Party
from eveuniverse.models import EveType

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo


class CharacterIndustryJob(models.Model):
    character = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="industry_jobs"
    )
    job_id = models.IntegerField(primary_key=True)
    activity_id = models.IntegerField()
    blueprint_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    product_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    status = models.CharField(max_length=50)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    runs = models.IntegerField(default=1)
    probability = models.FloatField(null=True, blank=True)
    successful_runs = models.IntegerField(null=True, blank=True)
    cost = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    facility_id = models.BigIntegerField(null=True, blank=True)
    station_id = models.BigIntegerField(null=True, blank=True)
    location_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Character Industry Job")
        verbose_name_plural = _("Character Industry Jobs")

    @property
    def activity_name(self):
        mapping = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            9: "Reactions",
        }
        return mapping.get(self.activity_id, f"Activity {self.activity_id}")

    @property
    def is_ready(self):
        # Django
        from django.utils import timezone

        if self.status == "ready":
            return True
        if (
            self.status == "active"
            and self.end_date
            and self.end_date <= timezone.now()
        ):
            return True
        return False

    @property
    def expected_output(self):
        portion = getattr(self.product_type, "portion_size", 1) or 1
        return self.runs * portion

    def __str__(self):
        return f"{self.character.character_name} - Job {self.job_id}"


class CorporationIndustryJob(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="industry_jobs"
    )
    installer = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="installed_corp_jobs",
    )
    job_id = models.IntegerField(primary_key=True)
    activity_id = models.IntegerField()
    blueprint_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    product_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    status = models.CharField(max_length=50)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    runs = models.IntegerField(default=1)
    probability = models.FloatField(null=True, blank=True)
    successful_runs = models.IntegerField(null=True, blank=True)
    cost = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    facility_id = models.BigIntegerField(null=True, blank=True)
    station_id = models.BigIntegerField(null=True, blank=True)
    location_id = models.BigIntegerField(null=True, blank=True)
    wallet_division = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Corporation Industry Job")
        verbose_name_plural = _("Corporation Industry Jobs")

    @property
    def activity_name(self):
        mapping = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            9: "Reactions",
        }
        return mapping.get(self.activity_id, f"Activity {self.activity_id}")

    @property
    def is_ready(self):
        # Django
        from django.utils import timezone

        if self.status == "ready":
            return True
        if (
            self.status == "active"
            and self.end_date
            and self.end_date <= timezone.now()
        ):
            return True
        return False

    @property
    def expected_output(self):
        portion = getattr(self.product_type, "portion_size", 1) or 1
        return self.runs * portion

    def __str__(self):
        return f"{self.corporation.corporation_name} - Job {self.job_id}"


class TaskJobLink(models.Model):
    task = models.ForeignKey(
        "ProductionTask", on_delete=models.CASCADE, related_name="linked_jobs"
    )
    character_job = models.ForeignKey(
        "CharacterIndustryJob", on_delete=models.CASCADE, null=True, blank=True
    )
    corporation_job = models.ForeignKey(
        "CorporationIndustryJob", on_delete=models.CASCADE, null=True, blank=True
    )

    # Amount of runs linked from this job to this task
    linked_runs = models.IntegerField(default=1)

    class Meta:
        verbose_name = _("Task Job Link")
        verbose_name_plural = _("Task Job Links")

    def __str__(self):
        return f"Link Task {self.task_id} -> Job {self.character_job_id or self.corporation_job_id}"
