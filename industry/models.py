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
            (
                "industrialist_access",
                "Can access the industrialist dashboard and claim jobs",
            ),
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


class CorpPricingConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="pricing_config"
    )
    default_discount_percent = models.FloatField(
        default=0.0,
        help_text="Default discount % applied to Jita prices (e.g. 10.0 for 10% off)",
    )

    class Meta:
        verbose_name = "Corp Pricing Config"
        verbose_name_plural = "Corp Pricing Configs"

    def __str__(self):
        return f"{self.corporation.corporation_name} Pricing"


class CorpTypeDiscount(models.Model):
    config = models.ForeignKey(
        CorpPricingConfig, on_delete=models.CASCADE, related_name="type_discounts"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    discount_percent = models.FloatField(
        help_text="Discount % for this specific item type"
    )

    class Meta:
        verbose_name = "Corp Type Discount"
        verbose_name_plural = "Corp Type Discounts"
        unique_together = (("config", "eve_type"),)

    def __str__(self):
        return f"{self.eve_type.name} - {self.discount_percent}% off"


class MemberOrder(models.Model):
    ORDER_STATUS_CHOICES = (
        ("REQUESTED", "Requested"),
        ("QUOTED", "Quoted"),
        ("ACCEPTED", "Accepted"),
        ("IN_PRODUCTION", "In Production"),
        ("READY", "Ready for Pickup"),
        ("DELIVERED", "Delivered"),
        ("REJECTED", "Rejected"),
    )

    character = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="industry_orders"
    )
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="REQUESTED"
    )
    total_price = models.DecimalField(max_digits=17, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Member Order"
        verbose_name_plural = "Member Orders"

    def __str__(self):
        return f"Order #{self.id} by {self.character.character_name} - {self.status}"

    @property
    def progress_percent(self):
        total_tasks = self.production_tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.production_tasks.filter(status="COMPLETED").count()
        return int((completed_tasks / total_tasks) * 100)


class OrderItem(models.Model):
    order = models.ForeignKey(
        MemberOrder, on_delete=models.CASCADE, related_name="items"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=17, decimal_places=2, default=0.00)
    discount_applied = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} for Order #{self.order_id}"

    @property
    def line_total(self):
        return self.price_per_unit * self.quantity


class OrderFit(models.Model):
    order = models.OneToOneField(
        MemberOrder, on_delete=models.CASCADE, related_name="fit"
    )
    raw_fit_text = models.TextField()

    class Meta:
        verbose_name = "Order Fit"
        verbose_name_plural = "Order Fits"

    def __str__(self):
        return f"Fit for Order #{self.order_id}"


class CorpMOTD(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="motd"
    )
    message = models.TextField(help_text="Message of the day for industrialists")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        EveCharacter, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Corp MOTD"
        verbose_name_plural = "Corp MOTDs"

    def __str__(self):
        return f"MOTD for {self.corporation.corporation_name}"


class ProductionTask(models.Model):
    STATUS_CHOICES = (
        ("UNCLAIMED", "Unclaimed"),
        ("IN_PRODUCTION", "In Production"),
        ("COMPLETED", "Completed"),
    )

    PRIORITY_CHOICES = (
        ("HIGH", "High"),
        ("NORMAL", "Normal"),
        ("LOW", "Low"),
    )

    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="UNCLAIMED"
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="NORMAL"
    )
    hidden = models.BooleanField(
        default=False, help_text="Hide from standard Industrialist Job Market"
    )

    # Relationships
    created_from_order = models.ForeignKey(
        MemberOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_tasks",
    )
    assigned_to = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claimed_tasks",
    )
    bom_parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bom_children",
        help_text="The parent task that requires this sub-component",
    )

    # Gamification
    gamification_value = models.DecimalField(
        max_digits=17,
        decimal_places=2,
        default=0.00,
        help_text="Calculated ISK value of the task for leaderboards",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Production Task"
        verbose_name_plural = "Production Tasks"

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} - {self.status}"


class CorpItemConfig(models.Model):
    BOM_CHOICES = (
        ("SDE", "Eve SDE (Database)"),
        ("FUZZWORK", "Fuzzwork API"),
    )

    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="item_configs"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")

    manual_me = models.IntegerField(
        default=0, help_text="Manual Material Efficiency override (0-10)"
    )
    manual_te = models.IntegerField(
        default=0, help_text="Manual Time Efficiency override (0-20)"
    )
    manual_price = models.DecimalField(
        max_digits=17,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override price, especially useful for Faction items",
    )

    target_threshold = models.IntegerField(
        default=0, help_text="Minimum stock level required in Hangars"
    )
    auto_produce = models.BooleanField(
        default=False,
        help_text="Automatically create ProductionTask if stock < threshold",
    )

    build_or_buy = models.CharField(
        max_length=10, choices=(("BUILD", "Build"), ("BUY", "Buy")), default="BUILD"
    )
    bom_source = models.CharField(
        max_length=10, choices=BOM_CHOICES, default="FUZZWORK"
    )

    class Meta:
        verbose_name = "Corp Item Config"
        verbose_name_plural = "Corp Item Configs"
        unique_together = (("corporation", "item_type"),)

    def __str__(self):
        return f"Config for {self.item_type.name}"


class CorpHangarConfig(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="hangar_configs"
    )
    location_id = models.BigIntegerField(help_text="The station or structure ID")
    flag_id = models.IntegerField(help_text="The hangar flag ID (e.g. 4 for Hangar 1)")
    description = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="User friendly name for this hangar",
    )

    class Meta:
        verbose_name = "Corp Hangar Config"
        verbose_name_plural = "Corp Hangar Configs"

    def __str__(self):
        return f"{self.corporation.corporation_ticker} Hangar: {self.description or self.flag_id}"


class CorpInventory(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="inventory"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.BigIntegerField(default=0)

    location_id = models.BigIntegerField()
    flag_id = models.IntegerField()

    manual_override = models.BooleanField(
        default=False, help_text="If true, ESI sync will not overwrite this quantity"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Corp Inventory"
        verbose_name_plural = "Corp Inventories"
        unique_together = (("corporation", "item_type", "location_id", "flag_id"),)

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} at {self.location_id}"


class TaxConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="tax_config"
    )
    industry_tax_rate = models.FloatField(
        default=0.0, help_text="Tax % applied to industry jobs"
    )
    broker_fee_rate = models.FloatField(default=0.0, help_text="Broker fee %")

    class Meta:
        verbose_name = "Tax Config"
        verbose_name_plural = "Tax Configs"

    def __str__(self):
        return f"{self.corporation.corporation_ticker} Tax Config"
