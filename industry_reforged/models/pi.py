"""
App Models
"""

# Third Party
from eveuniverse.models import EveType

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter


class UserPIConfig(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="industry_pi_config"
    )
    storage_warning_threshold = models.IntegerField(default=75)

    class Meta:
        verbose_name = _("User PI Config")
        verbose_name_plural = _("User PI Configs")

    def __str__(self):
        return f"{self.user.username} PI Config"


class CharacterPlanet(models.Model):
    character = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="planets"
    )
    planet_id = models.IntegerField()
    system_id = models.IntegerField()
    eve_system = models.ForeignKey(
        "eveuniverse.EveSolarSystem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    eve_planet = models.ForeignKey(
        "eveuniverse.EvePlanet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    planet_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    upgrade_level = models.IntegerField(default=0)
    num_pins = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Character Planet")
        verbose_name_plural = _("Character Planets")
        unique_together = (("character", "planet_id"),)

    def __str__(self):
        return f"{self.character.character_name} - Planet {self.planet_id}"

    @property
    def has_expired_extractors(self):
        return any(pin.is_extractor and pin.is_expired for pin in self.pins.all())

    @property
    def has_full_storage(self):
        threshold = 75
        try:
            if hasattr(self.character.character_ownership.user, "industry_pi_config"):
                threshold = (
                    self.character.character_ownership.user.industry_pi_config.storage_warning_threshold
                )
        except Exception:
            pass
        return any(pin.utilization_pct >= threshold for pin in self.storage_pins)

    @property
    def factory_summary(self):
        factories = [pin for pin in self.pins.all() if pin.is_factory]
        summary = {}
        for f in factories:
            key = (f.type, f.product_type)
            if key not in summary:
                summary[key] = {
                    "type": f.type,
                    "product_type": f.product_type,
                    "count": 0,
                }
            summary[key]["count"] += 1
        return summary.values()

    @property
    def end_products(self):
        """Returns a list of EveType objects representing the highest tier products produced on this planet."""
        high_tech = self.high_tech_factories
        if high_tech:
            return list({f.product_type for f in high_tech if f.product_type})
        advanced = self.advanced_factories
        if advanced:
            return list({f.product_type for f in advanced if f.product_type})
        basic = self.basic_factories
        if basic:
            return list({f.product_type for f in basic if f.product_type})

        # Fallback to raw materials from extractors if this is an extraction-only planet
        extractors = self.extractors
        if extractors:
            return list({e.product_type for e in extractors if e.product_type})

        return []

    @property
    def extractors(self):
        return [p for p in self.pins.all() if p.is_extractor]

    @property
    def basic_factories(self):
        return [p for p in self.pins.all() if p.is_basic_factory]

    @property
    def advanced_factories(self):
        return [p for p in self.pins.all() if p.is_advanced_factory]

    @property
    def high_tech_factories(self):
        return [p for p in self.pins.all() if p.is_high_tech_factory]

    @property
    def storage_pins(self):
        return [p for p in self.pins.all() if p.is_storage_facility or p.is_launchpad]

    @property
    def command_centers(self):
        return [p for p in self.pins.all() if p.is_command_center]

    @property
    def earliest_extractor_expiry(self):
        extractors = self.extractors
        if not extractors:
            return None
        valid_expiries = [e.expiry_time for e in extractors if e.expiry_time]
        if not valid_expiries:
            return None
        return min(valid_expiries)


class PlanetPin(models.Model):
    planet = models.ForeignKey(
        "CharacterPlanet", on_delete=models.CASCADE, related_name="pins"
    )
    pin_id = models.BigIntegerField()
    type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )

    # For extractors
    install_time = models.DateTimeField(null=True, blank=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    cycle_time = models.IntegerField(null=True, blank=True)
    extraction_yield = models.FloatField(null=True, blank=True)
    product_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    # For factories
    schematic_id = models.IntegerField(null=True, blank=True)
    last_cycle_start = models.DateTimeField(null=True, blank=True)

    # For storage & infrastructure
    contents_volume = models.FloatField(default=0.0)
    capacity = models.FloatField(default=0.0)
    contents = models.JSONField(default=dict, blank=True)

    # Notifications
    notification_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Planet Pin")
        verbose_name_plural = _("Planet Pins")
        unique_together = (("planet", "pin_id"),)

    def __str__(self):
        return f"Pin {self.pin_id} on {self.planet}"

    @property
    def utilization_pct(self):
        if self.capacity and self.capacity > 0:
            return min(100.0, (self.contents_volume / self.capacity) * 100.0)
        return 0.0

    @property
    def is_extractor(self):
        return self.type and "Extractor" in self.type.name

    @property
    def is_factory(self):
        return (
            self.type
            and ("Facility" in self.type.name or "Plant" in self.type.name)
            and "Storage" not in self.type.name
        )

    @property
    def is_basic_factory(self):
        return self.type and "Basic Industry Facility" in self.type.name

    @property
    def is_advanced_factory(self):
        return self.type and "Advanced Industry Facility" in self.type.name

    @property
    def is_high_tech_factory(self):
        return self.type and "High Tech Production Plant" in self.type.name

    @property
    def is_launchpad(self):
        return self.type and "Launchpad" in self.type.name

    @property
    def is_storage_facility(self):
        return self.type and "Storage Facility" in self.type.name

    @property
    def is_command_center(self):
        return self.type and "Command Center" in self.type.name

    @property
    def is_storage(self):
        return self.is_launchpad or self.is_storage_facility or self.is_command_center

    @property
    def status_label(self):
        if self.is_extractor:
            return "Expired" if self.is_expired else "Running"
        if self.is_factory:
            if self.schematic_id:
                return "Configured"
            return "Idle"
        return "Online"

    @property
    def progress_percent(self):
        if not self.install_time or not self.expiry_time:
            return 0
        # Django
        from django.utils import timezone

        now = timezone.now()
        if now >= self.expiry_time:
            return 100
        if now <= self.install_time:
            return 0
        total_duration = (self.expiry_time - self.install_time).total_seconds()
        elapsed = (now - self.install_time).total_seconds()
        if total_duration <= 0:
            return 100
        return int((elapsed / total_duration) * 100)

    @property
    def is_expired(self):
        if not self.expiry_time:
            return False
        # Django
        from django.utils import timezone

        return timezone.now() >= self.expiry_time
