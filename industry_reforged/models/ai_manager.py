# Third Party
from eveuniverse.models import EveType

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

from .facilities import IndustryFacility


class Basket(models.Model):
    """Represents a configured basket of goods to monitor and build."""

    name = models.CharField(max_length=255, help_text=_("Name of the basket"))
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="baskets", null=True
    )
    is_active = models.BooleanField(
        default=True, help_text=_("Whether this basket is currently active")
    )
    target_region_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text=_("ESI Region ID for region-based market checking."),
    )
    target_hub = models.ForeignKey(
        IndustryFacility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Specific facility (hub) to monitor."),
    )
    min_profit_margin = models.FloatField(
        default=15.0,
        help_text=_("Minimum acceptable profit margin % for building this basket."),
    )
    run_interval_hours = models.IntegerField(
        default=24,
        help_text=_("How often (in hours) should this basket run automatically."),
    )
    last_run = models.DateTimeField(
        null=True, blank=True, help_text=_("The last time this basket was evaluated.")
    )
    is_running = models.BooleanField(
        default=False,
        help_text=_(
            "Whether the basket is currently being evaluated in the background."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Basket")
        verbose_name_plural = _("Baskets")

    def __str__(self):
        return self.name


class BasketItem(models.Model):
    """Links a specific EveType (Item) to a Basket with configuration thresholds."""

    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    target_stock_level = models.PositiveIntegerField(
        help_text=_("The minimum quantity the market should always have available.")
    )
    batch_size = models.PositiveIntegerField(
        default=1, help_text=_("The default batch size to order when stock is low.")
    )

    class Meta:
        verbose_name = _("Basket Item")
        verbose_name_plural = _("Basket Items")

    def __str__(self):
        return f"{self.eve_type.name} in {self.basket.name}"


class AIMarketLog(models.Model):
    """Historical ledger explaining why the AI did or didn't create an order."""

    basket_item = models.ForeignKey(
        BasketItem, on_delete=models.SET_NULL, null=True, related_name="logs"
    )
    action_taken = models.CharField(
        max_length=255, help_text=_("e.g., 'Ordered', 'Skipped'")
    )
    margin = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Calculated profit margin at the time of check"),
    )
    stock_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Calculated current stock at the time of check"),
    )
    reason = models.TextField(help_text=_("Reasoning for the action taken"))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("AI Market Log")
        verbose_name_plural = _("AI Market Logs")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp}] {self.action_taken} - {getattr(self.basket_item, 'eve_type', 'Unknown Item')}"


class MarketOpportunity(models.Model):
    """Stores the latest calculated market opportunity for a specific item in a region for a corporation."""

    corporation = models.ForeignKey(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="market_opportunities",
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    region_id = models.BigIntegerField(help_text=_("ESI Region ID"))
    target_hub = models.ForeignKey(
        IndustryFacility,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("Specific facility if scanned for a hub."),
    )
    velocity = models.FloatField(help_text=_("Average Daily Volume (ADV)"))
    margin = models.FloatField(help_text=_("Estimated profit margin %"))
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Market Opportunity")
        verbose_name_plural = _("Market Opportunities")
        unique_together = (("corporation", "eve_type", "region_id", "target_hub"),)

    def __str__(self):
        return (
            f"{self.eve_type.name} opportunity for {self.corporation.corporation_name}"
        )


class OpportunityScanner(models.Model):
    """Saved configuration for scanning market opportunities."""

    name = models.CharField(max_length=255, help_text=_("Name of the scanner"))
    corporation = models.ForeignKey(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="opportunity_scanners",
    )
    is_active = models.BooleanField(default=True)
    target_region_id = models.BigIntegerField(
        null=True, blank=True, help_text=_("ESI Region ID")
    )
    target_hub = models.ForeignKey(
        IndustryFacility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Specific facility if scanning a hub"),
    )
    min_profit_margin = models.FloatField(default=15.0)
    min_velocity = models.FloatField(default=1.0)
    categories = models.JSONField(
        default=list, help_text=_("List of category IDs to scan")
    )
    auto_add_basket = models.ForeignKey(
        "Basket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Automatically add profitable items to this basket."),
    )
    target_stock_days = models.IntegerField(
        default=7,
        help_text=_(
            "If auto-adding, how many days of stock to maintain based on daily velocity."
        ),
    )
    is_running = models.BooleanField(
        default=False,
        help_text=_("Whether the scanner is currently running in the background."),
    )

    run_interval_hours = models.IntegerField(
        default=24,
        help_text=_("How often (in hours) should this scanner run automatically."),
    )
    last_run = models.DateTimeField(
        null=True, blank=True, help_text=_("The last time this scanner was executed.")
    )
    scan_missing_blueprints = models.BooleanField(
        default=False,
        help_text=_(
            "Also scan for profitable items that the corporation does NOT own blueprints for."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Opportunity Scanner")
        verbose_name_plural = _("Opportunity Scanners")

    def __str__(self):
        return self.name


class OpportunityScannerLog(models.Model):
    """Audit log of scanner executions."""

    scanner = models.ForeignKey(
        OpportunityScanner, on_delete=models.CASCADE, related_name="logs"
    )
    items_scanned = models.PositiveIntegerField(default=0)
    opportunities_found = models.PositiveIntegerField(default=0)
    items_auto_added = models.PositiveIntegerField(default=0)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Log for {self.scanner.name} at {self.timestamp}"


class MissingBlueprintOpportunity(models.Model):
    """Profitable items we don't have blueprints for."""

    scanner = models.ForeignKey(
        OpportunityScanner,
        on_delete=models.CASCADE,
        related_name="missing_opportunities",
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE)
    velocity = models.FloatField()
    margin = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-margin"]

    def __str__(self):
        return f"Missing BPO: {self.eve_type.name} for {self.scanner.name}"
