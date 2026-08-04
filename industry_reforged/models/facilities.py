"""
App Models
"""

# Third Party

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _


class IndustryFacility(models.Model):
    SECURITY_SPACE_CHOICES = (
        ("HIGHSEC", "High Security (1.0 - 0.5)"),
        ("LOWSEC", "Low Security (0.4 - 0.1)"),
        ("NULLSEC_WH", "Null Security / Wormhole (0.0 - -1.0)"),
    )
    facility_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    owner_id = models.IntegerField(null=True, blank=True)
    solar_system_id = models.IntegerField(null=True, blank=True)
    type_id = models.IntegerField(null=True, blank=True)
    security_space = models.CharField(
        max_length=15, choices=SECURITY_SPACE_CHOICES, default="HIGHSEC"
    )
    last_updated = models.DateTimeField(auto_now=True)

    sync_inventory = models.BooleanField(
        default=False, help_text=_("Sync corporate inventory from this facility.")
    )
    is_production_facility = models.BooleanField(
        default=False,
        help_text=_("Whether this facility is configured as a production facility."),
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_("Whether this is the default facility for the corporation."),
    )

    class Meta:
        verbose_name = _("Industry Facility")
        verbose_name_plural = _("Industry Facilities")

    def __str__(self):
        return f"{self.name} ({self.facility_id})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Unset default on all other facilities
            IndustryFacility.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    @property
    def type_name(self):
        names = {
            35825: "Raitaru",
            35826: "Azbel",
            35827: "Sotiyo",
            35832: "Astrahus",
            35833: "Fortizar",
            35834: "Keepstar",
            35835: "Athanor",
            35836: "Tatara",
        }
        return names.get(self.type_id, str(self.type_id))


class IndustryRig(models.Model):
    type_id = models.IntegerField(
        primary_key=True, help_text=_("EveType ID of the Rig")
    )
    name = models.CharField(max_length=255)
    me_bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_("Bonus as percentage (e.g. 2.0 for 2%)"),
    )
    te_bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_("Bonus as percentage (e.g. 20.0 for 20%)"),
    )
    applies_to_groups = models.TextField(
        help_text=_(
            "Comma-separated list of EveGroup IDs this rig applies to. E.g. '419' for Battlecruisers"
        ),
        blank=True,
        null=True,
    )
    applies_to_categories = models.TextField(
        help_text=_(
            "Comma-separated list of EveCategory IDs this rig applies to. E.g. '6' for Ships"
        ),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


class IndustryFacilityRig(models.Model):
    facility = models.ForeignKey(
        "IndustryFacility", on_delete=models.CASCADE, related_name="rigs"
    )
    rig = models.ForeignKey("IndustryRig", on_delete=models.CASCADE)
    installed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("facility", "rig"),)

    def __str__(self):
        return f"{self.rig.name} at {self.facility.name}"
