"""
App Models
"""

# Third Party
from eveuniverse.models import EveType

# Django
from django.db import models

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        """Meta definitions"""

        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("corp_access", "Can access corporate industry jobs"),
        )


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
        verbose_name = "Character Industry Job"
        verbose_name_plural = "Character Industry Jobs"

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
        verbose_name = "Corporation Industry Job"
        verbose_name_plural = "Corporation Industry Jobs"

    def __str__(self):
        return f"{self.corporation.corporation_name} - Job {self.job_id}"


class CorporationSyncConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="industry_sync_config",
    )
    sync_character = models.ForeignKey(
        EveCharacter,
        on_delete=models.CASCADE,
        help_text="Character with Director roles used for syncing.",
    )

    class Meta:
        verbose_name = "Corporation Sync Configuration"
        verbose_name_plural = "Corporation Sync Configurations"

    def __str__(self):
        return f"{self.corporation.corporation_name} Sync Config"


class CharacterPlanet(models.Model):
    character = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="planets"
    )
    planet_id = models.IntegerField()
    system_id = models.IntegerField()
    planet_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    upgrade_level = models.IntegerField(default=0)
    num_pins = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Character Planet"
        verbose_name_plural = "Character Planets"
        unique_together = (("character", "planet_id"),)

    def __str__(self):
        return f"{self.character.character_name} - Planet {self.planet_id}"


class PlanetPin(models.Model):
    planet = models.ForeignKey(
        CharacterPlanet, on_delete=models.CASCADE, related_name="pins"
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

    class Meta:
        verbose_name = "Planet Pin"
        verbose_name_plural = "Planet Pins"
        unique_together = (("planet", "pin_id"),)

    def __str__(self):
        return f"Pin {self.pin_id} on {self.planet}"

    @property
    def is_extractor(self):
        return self.type and "Extractor" in self.type.name

    @property
    def is_factory(self):
        return (
            self.type
            and "Facility" in self.type.name
            and "Storage" not in self.type.name
        )

    @property
    def is_storage(self):
        return self.type and (
            "Storage" in self.type.name
            or "Spaceport" in self.type.name
            or "Command Center" in self.type.name
            or "Launchpad" in self.type.name
        )

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
