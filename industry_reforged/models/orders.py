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
        "CorpPricingConfig", on_delete=models.CASCADE, related_name="type_discounts"
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
        "IndustryFacility",
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
        on_delete=models.CASCADE,
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

    def save(self, *args, **kwargs):
        # Force suborders to mirror parent status before saving
        if self.parent_order:
            self.status = self.parent_order.status

        super().save(*args, **kwargs)

        # Propagate status to children if this is a parent order
        if not self.parent_order:
            self.child_orders.update(status=self.status)

    @property
    def root_order(self):
        root = self
        while root.parent_order:
            root = root.parent_order
        return root

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
        "MemberOrder", on_delete=models.CASCADE, related_name="items"
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
        "MemberOrder", on_delete=models.CASCADE, related_name="fit"
    )
    raw_fit_text = models.TextField()

    class Meta:
        verbose_name = _("Order Fit")
        verbose_name_plural = _("Order Fits")

    def __str__(self):
        return f"Fit for Order #{self.order_id}"


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
        "MemberOrder",
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
        "BuilderPayoutBatch",
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


class OrderBlueprintOverride(models.Model):
    order = models.ForeignKey(
        "MemberOrder", on_delete=models.CASCADE, related_name="bp_overrides"
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


class CorpBuyOrder(models.Model):
    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("FULFILLED", "Fulfilled"),
    )
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="buy_orders"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Corporate Buy Order")
        verbose_name_plural = _("Corporate Buy Orders")

    def __str__(self):
        return f"Buy Order #{self.id} - {self.quantity}x {self.item_type.name} ({self.status})"
