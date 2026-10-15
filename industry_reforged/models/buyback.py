"""
App Models
"""

# Third Party
from eveuniverse.models import EveCategory, EveType

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from .facilities import IndustryFacility, KnownLocation


class BuybackProgram(models.Model):
    """
    A director-configured buyback offer: where members drop off items, at what
    price modifier, and which categories are in scope by default.
    """

    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="buyback_programs"
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    facility = models.ForeignKey(
        IndustryFacility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyback_programs",
        help_text=_("Configured drop-off structure, if it is an IndustryFacility."),
    )
    known_location = models.ForeignKey(
        KnownLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyback_programs",
        help_text=_("Drop-off location outside configured IndustryFacilities."),
    )
    price_modifier_percent = models.FloatField(
        default=0.0,
        help_text=_(
            "Percentage adjustment applied to the market appraisal (e.g. -5.0 to pay 95%)."
        ),
    )
    accepted_categories = models.ManyToManyField(
        EveCategory,
        blank=True,
        related_name="buyback_programs",
        help_text=_("If empty, every category not on the watchlist is accepted."),
    )
    price_density_threshold = models.FloatField(
        default=0.0,
        help_text=_(
            "ISK/m3 below which the price density tax applies to a bulky, low-value item (0 disables it)."
        ),
    )
    price_density_tax_percent = models.FloatField(
        default=0.0,
        help_text=_("Percentage deducted from items below the price density threshold."),
    )
    contract_expiry_days = models.IntegerField(
        default=7,
        help_text=_(
            "Days a member has to create the matching ESI contract before it expires."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Buyback Program")
        verbose_name_plural = _("Buyback Programs")

    def __str__(self):
        return f"{self.name} ({self.corporation.corporation_ticker})"

    def save(self, *args, **kwargs):
        if not self.facility_id and not self.known_location_id:
            raise ValueError(
                "A BuybackProgram must have either a facility or a known_location set."
            )
        super().save(*args, **kwargs)

    @property
    def drop_off_name(self):
        if self.facility:
            return self.facility.name
        if self.known_location:
            return self.known_location.name
        return "-"


class BuybackWatchlistItem(models.Model):
    """
    Per-program manual-review flag for a specific item type. `blocks_submission`
    True rejects the item at calculator time; False allows it but flags the
    resulting contract for director review.
    """

    program = models.ForeignKey(
        BuybackProgram, on_delete=models.CASCADE, related_name="watchlist_items"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    reason = models.CharField(max_length=255, blank=True)
    blocks_submission = models.BooleanField(
        default=False,
        help_text=_("If True, this item cannot be submitted at all; if False, it is flagged for review."),
    )

    class Meta:
        verbose_name = _("Buyback Watchlist Item")
        verbose_name_plural = _("Buyback Watchlist Items")
        unique_together = (("program", "eve_type"),)

    def __str__(self):
        return f"{self.eve_type.name} - {self.program.name}"


class BuybackContract(models.Model):
    """
    One member's tracked buyback attempt, from the calculator's "got a tracking
    number" step through the director's payout decision. Matched against a real
    ESI item-exchange contract by `tracking_number`.
    """

    STATUS_CHOICES = (
        ("PENDING", _("Pending - awaiting ESI contract")),
        ("MATCHED", _("Matched - no issues found")),
        ("FLAGGED", _("Flagged - needs director review")),
        ("ACCEPTED", _("Accepted in-game")),
        ("REJECTED", _("Rejected")),
        ("PAID", _("Paid")),
        ("EXPIRED", _("Expired - no contract seen in time")),
        ("CANCELLED", _("Cancelled by member")),
    )

    tracking_number = models.CharField(max_length=20, unique=True, db_index=True)
    program = models.ForeignKey(
        BuybackProgram, on_delete=models.PROTECT, related_name="contracts"
    )
    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="buyback_contracts",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    esi_contract_id = models.BigIntegerField(unique=True, null=True, blank=True)
    esi_issuer_character_id = models.IntegerField(null=True, blank=True)
    esi_acceptor_character_id = models.IntegerField(null=True, blank=True)

    quoted_price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text=_("Net amount after any donation - this is what the member should put on the in-game contract."),
    )
    donation_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text=_("ISK voluntarily donated to the corp from this contract's appraisal, chosen by the member at submission time. Already deducted from quoted_price."),
    )
    contract_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    contract_title = models.CharField(max_length=255, blank=True)

    flag_item_mismatch = models.BooleanField(default=False)
    flag_price_mismatch = models.BooleanField(default=False)
    flag_structure_mismatch = models.BooleanField(default=False)
    flag_receiver_mismatch = models.BooleanField(default=False)
    flag_title_tampered = models.BooleanField(default=False)
    flag_no_tracking = models.BooleanField(default=False)
    flag_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Buyback Contract")
        verbose_name_plural = _("Buyback Contracts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_number} ({self.status})"

    @property
    def gross_appraisal(self):
        """The full appraisal before any donation - quoted_price + donation_amount."""
        return self.quoted_price + self.donation_amount

    @property
    def has_flags(self):
        return any(
            [
                self.flag_item_mismatch,
                self.flag_price_mismatch,
                self.flag_structure_mismatch,
                self.flag_receiver_mismatch,
                self.flag_title_tampered,
                self.flag_no_tracking,
            ]
        )

    @property
    def payout_transaction(self):
        return self.ledger_transactions.first()


class BuybackContractItem(models.Model):
    """Line item of a BuybackContract, as quoted by the calculator."""

    contract = models.ForeignKey(
        BuybackContract, on_delete=models.CASCADE, related_name="items"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=2)
    is_esi_verified = models.BooleanField(
        default=False,
        help_text=_("Set True once the matching task confirms this exact type/qty in the real ESI contract."),
    )

    class Meta:
        verbose_name = _("Buyback Contract Item")
        verbose_name_plural = _("Buyback Contract Items")

    def __str__(self):
        return f"{self.quantity}x {self.eve_type.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
