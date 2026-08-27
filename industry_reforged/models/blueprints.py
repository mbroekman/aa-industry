"""
App Models for Blueprints
"""

# Third Party
from eveuniverse.models import EveType

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo


class CorpBlueprint(models.Model):
    item_id = models.BigIntegerField(primary_key=True)
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="blueprints"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    location_id = models.BigIntegerField()
    location_flag = models.CharField(max_length=50)
    quantity = models.IntegerField(default=-1)
    time_efficiency = models.IntegerField(default=0)
    material_efficiency = models.IntegerField(default=0)
    runs = models.IntegerField(default=-1)

    class Meta:
        verbose_name = _("Corp Blueprint")
        verbose_name_plural = _("Corp Blueprints")

    def __str__(self):
        return f"{self.eve_type.name} (ME: {self.material_efficiency}, TE: {self.time_efficiency})"

    @property
    def is_original(self):
        return self.quantity == -1 or self.quantity == -2 or self.runs == -1


class BlueprintRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("ACCEPTED", _("Accepted")),
        ("PROCESSED", _("Processed")),
        ("REJECTED", _("Rejected")),
        ("CANCELLED", _("Cancelled")),
    )

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blueprint_requests"
    )
    blueprint = models.ForeignKey(
        CorpBlueprint, on_delete=models.CASCADE, related_name="requests"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    requested_quantity = models.IntegerField(
        default=1, help_text=_("Number of copies requested")
    )
    requested_runs = models.IntegerField(
        default=1, help_text=_("Runs per copy requested")
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_blueprint_requests",
    )

    class Meta:
        verbose_name = _("Blueprint Request")
        verbose_name_plural = _("Blueprint Requests")

    def __str__(self):
        return (
            f"Request for {self.blueprint.eve_type.name} by {self.requester.username}"
        )
