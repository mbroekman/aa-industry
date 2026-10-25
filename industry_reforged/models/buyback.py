"""
App Models
"""

# Standard Library
from decimal import Decimal

# Third Party
from eveuniverse.models import EveCategory, EveType

# Django
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import State
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from .facilities import IndustryFacility, KnownLocation


class BuybackProgramQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Active programs this user may see and use.

        Anonymous visitors only see public programs. A logged-in user sees a
        program when they pass both its group and its state restriction (an
        empty restriction lets everyone through). Directors always see their
        own corporation's programs.
        """
        programs = self.filter(is_active=True)
        if user is None or not user.is_authenticated:
            return programs.filter(is_public=True)

        state = getattr(getattr(user, "profile", None), "state", None)
        group_ok = Q(restricted_to_groups__isnull=True) | Q(
            restricted_to_groups__in=user.groups.all()
        )
        state_ok = Q(restricted_to_states__isnull=True)
        if state is not None:
            state_ok |= Q(restricted_to_states=state)
        allowed = group_ok & state_ok

        main = getattr(getattr(user, "profile", None), "main_character", None)
        if main and user.has_perm("industry_reforged.corp_access"):
            allowed |= Q(corporation__corporation_id=main.corporation_id)

        return programs.filter(allowed).distinct()


class BuybackProgram(models.Model):
    """
    A director-configured buyback offer: where members drop off items, at what
    price modifier, and which categories are in scope by default.
    """

    PRICE_TYPE_CHOICES = (
        ("BUY", _("Buy - pay based on the Jita buy price")),
        ("SELL", _("Sell - pay based on the Jita sell price")),
        ("SPLIT", _("Split - pay based on the midpoint of buy and sell price")),
    )

    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="buyback_programs"
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    facilities = models.ManyToManyField(
        IndustryFacility,
        blank=True,
        related_name="buyback_dropoff_programs",
        help_text=_("Structures where members may hand in their contract."),
    )
    known_locations = models.ManyToManyField(
        KnownLocation,
        blank=True,
        related_name="buyback_dropoff_programs",
        help_text=_("Other locations where members may hand in their contract."),
    )
    RECIPIENT_CHOICES = (
        ("CORPORATION", _("The program's corporation")),
        ("CHARACTER", _("A specific character")),
    )
    recipient_type = models.CharField(
        max_length=12,
        choices=RECIPIENT_CHOICES,
        default="CORPORATION",
        help_text=_("Who members must make the in-game contract out to."),
    )
    recipient_character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_(
            "Receiving character when contracts go to a character. It needs the "
            "character contracts permission via Add Personal Token."
        ),
    )
    tracking_prefix = models.CharField(
        max_length=10,
        default="BB",
        validators=[
            RegexValidator(
                r"^[A-Z0-9]{1,10}$",
                _("Use 1-10 capital letters or digits."),
            )
        ],
        help_text=_("Start of every tracking number, e.g. BB gives BB-1A2B3C4D."),
    )
    restricted_to_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="+",
        help_text=_("Only these groups may use the program. Empty means everyone."),
    )
    restricted_to_states = models.ManyToManyField(
        State,
        blank=True,
        related_name="+",
        help_text=_("Only these states may use the program. Empty means everyone."),
    )
    is_public = models.BooleanField(
        default=False,
        help_text=_(
            "Let anyone use the calculator without logging in. Requires "
            'APPS_WITH_PUBLIC_VIEWS = ["industry_reforged"] in local.py.'
        ),
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
        help_text=_(
            "Percentage deducted from items below the price density threshold."
        ),
    )
    contract_expiry_days = models.IntegerField(
        default=7,
        help_text=_(
            "Days a member has to create the matching ESI contract before it expires."
        ),
    )
    price_type = models.CharField(
        max_length=5,
        choices=PRICE_TYPE_CHOICES,
        default="SELL",
        help_text=_("Which Jita price to base the appraisal on."),
    )
    refining_rate = models.FloatField(
        default=90.0,
        help_text=_(
            "Refining efficiency (%) used to value reprocessable items (ore, loot) "
            "that have no direct market price. No real reprocessing setup hits 100%%."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BuybackProgramQuerySet.as_manager()

    class Meta:
        verbose_name = _("Buyback Program")
        verbose_name_plural = _("Buyback Programs")

    def __str__(self):
        return f"{self.name} ({self.corporation.corporation_ticker})"

    @property
    def drop_off_names(self) -> list[str]:
        names = [f.name for f in self.facilities.all()]
        names += [loc.name for loc in self.known_locations.all()]
        return names

    @property
    def drop_off_name(self) -> str:
        return ", ".join(self.drop_off_names) or "-"

    @property
    def drop_off_location_ids(self) -> set[int]:
        ids = {f.facility_id for f in self.facilities.all()}
        ids |= {loc.location_id for loc in self.known_locations.all()}
        return ids

    @property
    def recipient_id(self) -> int:
        """EVE id the in-game contract must be made out to."""
        if self.recipient_type == "CHARACTER" and self.recipient_character_id:
            return self.recipient_character.character_id
        return self.corporation.corporation_id

    @property
    def recipient_name(self) -> str:
        if self.recipient_type == "CHARACTER" and self.recipient_character_id:
            return self.recipient_character.character_name
        return self.corporation.corporation_name

    def is_visible_to(self, user) -> bool:
        return BuybackProgram.objects.visible_to(user).filter(pk=self.pk).exists()


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
        help_text=_(
            "If True, this item cannot be submitted at all; if False, it is flagged for review."
        ),
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
        help_text=_(
            "Net amount after any donation - this is what the member should put on the in-game contract."
        ),
    )
    donation_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text=_(
            "ISK voluntarily donated to the corp from this contract's appraisal, chosen by the member at submission time. Already deducted from quoted_price."
        ),
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
    flag_watchlist = models.BooleanField(
        default=False,
        help_text=_("Contains an item on the program's watchlist (flag mode)."),
    )
    flag_notes = models.TextField(blank=True)
    is_public_submission = models.BooleanField(
        default=False,
        help_text=_("Created through a program's public calculator, without login."),
    )

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
    def base_appraisal_total(self):
        """Sum of items' base_line_total - what the items were worth before the
        program's price modifier and bulk-item tax were applied."""
        total = self.items.aggregate(
            total=Sum(models.F("base_unit_price") * models.F("quantity"))
        )["total"]
        return total or Decimal("0.00")

    @property
    def modifier_impact(self):
        """ISK difference the program's price modifier + bulk-item tax made to
        this contract: gross_appraisal (pre-donation) minus base_appraisal_total.
        Negative means the modifier reduced the payout (e.g. a -5% modifier)."""
        return self.gross_appraisal - self.base_appraisal_total

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
                self.flag_watchlist,
            ]
        )

    @property
    def payout_transaction(self):
        return self.ledger_transactions.first()

    def mark_paid(self, director=None, notes="Buyback payout") -> bool:
        """Record the payout once. Shared by the director's Pay button and the
        poller seeing the contract finished in-game, so whichever comes first
        wins and the other is a no-op. Returns True if this call paid it."""
        # Django
        from django.db import transaction

        from .wallet import LedgerTransaction

        with transaction.atomic():
            locked = BuybackContract.objects.select_for_update().get(pk=self.pk)
            if locked.status == "PAID":
                return False
            if not locked.ledger_transactions.filter(
                transaction_type="BUYBACK_PAYOUT"
            ).exists():
                LedgerTransaction.objects.create(
                    transaction_type="BUYBACK_PAYOUT",
                    amount=locked.quoted_price,
                    character=locked.character,
                    director=director,
                    reference=locked.tracking_number,
                    notes=notes,
                    buyback_contract=locked,
                )
            locked.status = "PAID"
            locked.save(update_fields=["status", "updated_at"])
        self.status = "PAID"
        return True


class BuybackContractItem(models.Model):
    """Line item of a BuybackContract, as quoted by the calculator."""

    contract = models.ForeignKey(
        BuybackContract, on_delete=models.CASCADE, related_name="items"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=2)
    base_unit_price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text=_(
            "Appraised unit price before the program's price modifier and bulk-item tax were applied."
        ),
    )
    is_esi_verified = models.BooleanField(
        default=False,
        help_text=_(
            "Set True once the matching task confirms this exact type/qty in the real ESI contract."
        ),
    )

    class Meta:
        verbose_name = _("Buyback Contract Item")
        verbose_name_plural = _("Buyback Contract Items")

    def __str__(self):
        return f"{self.quantity}x {self.eve_type.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def base_line_total(self):
        return self.base_unit_price * self.quantity
