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
        default=False, help_text="Sync corporate inventory from this facility."
    )
    is_production_facility = models.BooleanField(
        default=False,
        help_text="Whether this facility is configured as a production facility.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default facility for the corporation.",
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
            35832: "Athanor",
            35833: "Tatara",
            35835: "Astrahus",
            35836: "Fortizar",
            35834: "Keepstar",
        }
        return names.get(self.type_id, str(self.type_id))


class IndustryRig(models.Model):
    type_id = models.IntegerField(primary_key=True, help_text="EveType ID of the Rig")
    name = models.CharField(max_length=255)
    me_bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Bonus as percentage (e.g. 2.0 for 2%)",
    )
    te_bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Bonus as percentage (e.g. 20.0 for 20%)",
    )
    applies_to_groups = models.TextField(
        help_text="Comma-separated list of EveGroup IDs this rig applies to. E.g. '419' for Battlecruisers",
        blank=True,
        null=True,
    )
    applies_to_categories = models.TextField(
        help_text="Comma-separated list of EveCategory IDs this rig applies to. E.g. '6' for Ships",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


class IndustryFacilityRig(models.Model):
    facility = models.ForeignKey(
        IndustryFacility, on_delete=models.CASCADE, related_name="rigs"
    )
    rig = models.ForeignKey(IndustryRig, on_delete=models.CASCADE)
    installed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("facility", "rig"),)

    def __str__(self):
        return f"{self.rig.name} at {self.facility.name}"


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
        verbose_name = _("Corporation Sync Configuration")
        verbose_name_plural = _("Corporation Sync Configurations")

    def __str__(self):
        return f"{self.corporation.corporation_name} Sync Config"


class CorporationWebhookConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="industry_webhooks",
    )
    orders_webhook = models.URLField(
        blank=True, null=True, help_text="Webhook URL for new Orders and Quotes."
    )
    directors_webhook = models.URLField(
        blank=True,
        null=True,
        help_text="Webhook URL for Director-specific action alerts (e.g. New Quotes Requested, Orders Ready for Delivery).",
    )
    jobs_webhook = models.URLField(
        blank=True,
        null=True,
        help_text="Webhook URL for Corporate Industry Jobs completion.",
    )
    wallets_webhook = models.URLField(
        blank=True, null=True, help_text="Webhook URL for low wallet balance warnings."
    )
    wallet_warning_threshold = models.BigIntegerField(
        default=500000000,
        help_text="Balance below which a warning is sent (default: 500 million ISK).",
    )
    inventory_webhook = models.URLField(
        blank=True, null=True, help_text="Webhook URL for low inventory warnings."
    )

    class Meta:
        verbose_name = _("Discord Webhook Configuration")
        verbose_name_plural = _("Discord Webhook Configurations")

    def __str__(self):
        return f"{self.corporation.corporation_name} Webhooks"


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
        return any(pin.utilization_pct > 75 for pin in self.storage_pins)

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


class CorpPricingConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="pricing_config"
    )
    default_discount_percent = models.FloatField(
        default=0.0,
        help_text="Default discount % applied to Jita prices (e.g. 10.0 for 10% off)",
    )
    builder_reward_percent = models.FloatField(
        default=0.0,
        help_text="Percentage of the item value given as a financial reward to the builder",
    )
    default_t1_me = models.IntegerField(
        default=10,
        help_text="Default Material Efficiency (ME) for Tech I blueprints",
    )
    default_t2_me = models.IntegerField(
        default=2,
        help_text="Default Material Efficiency (ME) for Tech II blueprints",
    )

    class Meta:
        verbose_name = _("Corp Pricing Config")
        verbose_name_plural = _("Corp Pricing Configs")

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
        verbose_name = _("Corp Type Discount")
        verbose_name_plural = _("Corp Type Discounts")
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
    target_facility = models.ForeignKey(
        IndustryFacility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targeted_orders",
        help_text="The facility where this order is planned to be built, used for quote calculation.",
    )
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="REQUESTED"
    )
    total_price = models.DecimalField(max_digits=17, decimal_places=2, default=0.00)
    upfront_payment = models.DecimalField(max_digits=17, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=17, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    quoted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    parent_order = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_orders",
        help_text="If this order was split, this is the parent order.",
    )

    payment_reference = models.CharField(
        max_length=50, unique=True, null=True, blank=True
    )
    is_paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Member Order")
        verbose_name_plural = _("Member Orders")

    def __str__(self):
        return f"Order #{self.id} by {self.character.character_name} - {self.status}"

    @property
    def remaining_balance(self):
        return max(0, self.total_price - self.amount_paid)

    @property
    def grand_total(self):
        """The sum of this order's total_price and all its child_orders' total_prices."""
        total = self.total_price
        for child in self.child_orders.all():
            total += child.total_price
        return total

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
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} for Order #{self.order_id}"

    @property
    def line_total(self):
        return self.price_per_unit * self.quantity

    @property
    def original_price_per_unit(self):
        if self.discount_applied == 0:
            return self.price_per_unit

        # Avoid division by zero if discount is somehow 100%
        if self.discount_applied >= 100:
            return self.price_per_unit

        return float(self.price_per_unit) / (1.0 - (self.discount_applied / 100.0))

    @property
    def original_line_total(self):
        return self.original_price_per_unit * self.quantity


class OrderFit(models.Model):
    order = models.OneToOneField(
        MemberOrder, on_delete=models.CASCADE, related_name="fit"
    )
    raw_fit_text = models.TextField()

    class Meta:
        verbose_name = _("Order Fit")
        verbose_name_plural = _("Order Fits")

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
        verbose_name = _("Corp MOTD")
        verbose_name_plural = _("Corp MOTDs")

    def __str__(self):
        return f"MOTD for {self.corporation.corporation_name}"


class BuilderPayoutBatch(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="payout_batches"
    )
    builder = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="payout_batches"
    )
    total_amount = models.DecimalField(max_digits=17, decimal_places=2)
    payment_reference = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=(("PENDING", "Pending"), ("PAID", "Paid")),
        default="PENDING",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Builder Payout Batch")
        verbose_name_plural = _("Builder Payout Batches")

    def __str__(self):
        return (
            f"{self.payment_reference} - {self.builder.character_name} ({self.status})"
        )


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
    activity_id = models.IntegerField(default=1)
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
    builder_reward = models.DecimalField(
        max_digits=17,
        decimal_places=2,
        default=0.00,
        help_text="Actual calculated ISK payout reward for completing this task",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    payout_batch = models.ForeignKey(
        BuilderPayoutBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    class Meta:
        verbose_name = _("Production Task")
        verbose_name_plural = _("Production Tasks")

    @property
    def activity_name(self):
        mapping = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            11: "Reactions",
        }
        return mapping.get(self.activity_id, f"Activity {self.activity_id}")

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} for Job {self.id}"


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
    max_runs = models.IntegerField(
        default=0, help_text="Max runs per BPC (0 = infinite/BPO)"
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
    last_low_stock_warning = models.DateTimeField(null=True, blank=True)
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

    exclude_from_orders = models.BooleanField(
        default=False, help_text="Remove this item from member orders automatically."
    )
    exclude_warning_message = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Message to display to the user if this item is removed (e.g. 'Please acquire deadspace items yourself').",
    )

    class Meta:
        verbose_name = _("Corp Item Config")
        verbose_name_plural = _("Corp Item Configs")
        unique_together = (("corporation", "item_type"),)

    def __str__(self):
        return f"Config for {self.item_type.name}"


class CorpInventory(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="inventory"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.BigIntegerField(default=0)

    location_id = models.BigIntegerField()

    manual_override = models.BooleanField(
        default=False, help_text="If true, ESI sync will not overwrite this quantity"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Corp Inventory")
        verbose_name_plural = _("Corp Inventories")
        unique_together = (("corporation", "item_type", "location_id"),)

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} in {self.corporation.corporation_ticker}"


class WalletJournalSyncState(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="wallet_sync_state"
    )
    last_journal_id = models.BigIntegerField(default=0)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Wallet Journal Sync State")
        verbose_name_plural = _("Wallet Journal Sync States")

    def __str__(self):
        return (
            f"{self.corporation.corporation_ticker} - Last ID: {self.last_journal_id}"
        )


class TaxConfig(models.Model):
    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="tax_config"
    )
    industry_tax_rate = models.FloatField(
        default=0.0, help_text="Tax % applied to industry jobs"
    )
    broker_fee_rate = models.FloatField(default=0.0, help_text="Broker fee %")

    class Meta:
        verbose_name = _("Tax Config")
        verbose_name_plural = _("Tax Configs")

    def __str__(self):
        return f"{self.corporation.corporation_ticker} Tax Config"


class CorpWalletDivision(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="wallet_divisions"
    )
    division = models.IntegerField()
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    last_warning = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Corp Wallet Division")
        verbose_name_plural = _("Corp Wallet Divisions")
        unique_together = (("corporation", "division"),)

    def __str__(self):
        return (
            f"{self.corporation.corporation_ticker} - {self.name} (Div {self.division})"
        )


class CorpWalletJournal(models.Model):
    division = models.ForeignKey(
        CorpWalletDivision, on_delete=models.CASCADE, related_name="journal_entries"
    )
    journal_id = models.BigIntegerField()
    date = models.DateTimeField()
    ref_type = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    reason = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    first_party_id = models.BigIntegerField(null=True, blank=True)
    second_party_id = models.BigIntegerField(null=True, blank=True)
    tax = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tax_receiver_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Corp Wallet Journal")
        verbose_name_plural = _("Corp Wallet Journals")
        unique_together = (("division", "journal_id"),)
        ordering = ["-date"]

    def __str__(self):
        return f"Journal {self.journal_id} - {self.ref_type}"


class TaskExecutionLog(models.Model):
    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("RUNNING", "Running"),
    )
    task_name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RUNNING")
    last_run = models.DateTimeField(auto_now=True)
    duration_seconds = models.FloatField(default=0.0)
    message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Task Execution Log")
        verbose_name_plural = _("Task Execution Logs")

    def __str__(self):
        return f"{self.task_name} - {self.status}"


class OrderBlueprintOverride(models.Model):
    order = models.ForeignKey(
        MemberOrder, on_delete=models.CASCADE, related_name="bp_overrides"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    manual_me = models.IntegerField(default=0)
    max_runs = models.IntegerField(default=0)

    class Meta:
        verbose_name = _("Order BP Override")
        verbose_name_plural = _("Order BP Overrides")
        unique_together = (("order", "item_type"),)

    def __str__(self):
        return f"Override ME {self.manual_me} for {self.item_type.name} on Order #{self.order.id}"
