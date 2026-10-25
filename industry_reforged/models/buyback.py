"""
App Models
"""

# Standard Library
from datetime import timedelta
from decimal import Decimal

# Third Party
from eveuniverse.models import EveCategory, EveGroup, EveMarketGroup, EveType

# Django
from django.contrib.auth.models import Group
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
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
            "Refining efficiency (%) used to value ore, ice and moon ore by their "
            "refined minerals. No real reprocessing setup hits 100%%."
        ),
    )
    allow_all_items = models.BooleanField(
        default=True,
        help_text=_(
            "Accept every item that no rule disallows. When off, only items and "
            "market groups that have a rule are accepted."
        ),
    )
    use_raw_ore_value = models.BooleanField(
        default=True,
        help_text=_("Ore, ice and moon ore: value at the ore's own market price."),
    )
    use_compressed_value = models.BooleanField(
        default=False,
        help_text=_(
            "Ore, ice and moon ore: value at the compressed variant's market price."
        ),
    )
    use_refined_value = models.BooleanField(
        default=True,
        help_text=_(
            "Ore, ice and moon ore: value by the refined minerals, at the refining rate."
        ),
    )
    use_reprocessed_value_for_t1 = models.BooleanField(
        default=False,
        help_text=_(
            "Ships, modules, charges, drones and subsystems up to meta level 4: also "
            "value them as scrap minerals and pay the higher of market and scrap."
        ),
    )
    t1_refining_rate = models.FloatField(
        default=50.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Scrap reprocessing yield (%) for that T1 valuation."),
    )
    npc_price_blue_loot = models.BooleanField(
        default=False,
        help_text=_("Value Sleeper Components at their NPC (average) price."),
    )
    npc_price_red_loot = models.BooleanField(
        default=False,
        help_text=_("Value Triglavian Survey Databases at their NPC (average) price."),
    )
    npc_price_ope = models.BooleanField(
        default=False,
        help_text=_("Value Overseer's Personal Effects at their NPC (average) price."),
    )
    npc_price_bonds = models.BooleanField(
        default=False,
        help_text=_("Value SCC Encrypted Bonds at their NPC (average) price."),
    )
    hauling_fuel_cost = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text=_(
            "ISK per m3 deducted for hauling (0 = none). Don't combine with the "
            "density tax; both penalise bulky items."
        ),
    )
    compression_density_modifier = models.BooleanField(
        default=False,
        help_text=_(
            "Use the compressed volume of ore, ice and moon ore for hauling and the "
            "density tax."
        ),
    )
    allow_unpacked_items = models.BooleanField(
        default=False,
        help_text=_(
            "Accept assembled items (inventory lines pasted without a quantity)."
        ),
    )
    notify_new_contracts = models.BooleanField(
        default=True,
        help_text=_(
            "Post every newly matched contract to the corporation's buyback Discord "
            "webhook. Flagged contracts are always posted."
        ),
    )
    notify_show_item_list = models.BooleanField(
        default=False,
        help_text=_("Include the item list in Discord posts."),
    )
    notify_manager_character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_(
            "Also send this character a Discord DM and an Auth notification for "
            "every new contract."
        ),
    )
    wallet_division = models.ForeignKey(
        "industry_reforged.CorpWalletDivision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyback_programs",
        help_text=_(
            "Corporation wallet division that funds this program; its balance is "
            "shown on the program's performance page."
        ),
    )
    reject_appraisal_on_disallowed = models.BooleanField(
        default=False,
        help_text=_(
            "Refuse the whole appraisal when any pasted item isn't accepted, instead "
            "of leaving that item out."
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
    Per-program manual-review flag for one item type or a whole item group.
    `blocks_submission` True rejects the item at calculator time; False allows
    it but flags the resulting contract for director review.
    """

    program = models.ForeignKey(
        BuybackProgram, on_delete=models.CASCADE, related_name="watchlist_items"
    )
    eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, related_name="+", null=True, blank=True
    )
    eve_group = models.ForeignKey(
        EveGroup, on_delete=models.CASCADE, related_name="+", null=True, blank=True
    )
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
        # No condition needed: unique indexes treat NULLs as distinct, and
        # MariaDB/MySQL can't create conditional unique constraints at all.
        constraints = [
            models.UniqueConstraint(
                fields=["program", "eve_group"],
                name="buyback_watchlist_unique_group",
            ),
            models.CheckConstraint(
                condition=(
                    Q(eve_type__isnull=False, eve_group__isnull=True)
                    | Q(eve_type__isnull=True, eve_group__isnull=False)
                ),
                name="buyback_watchlist_type_xor_group",
            ),
        ]

    @property
    def target_name(self) -> str:
        if self.eve_type_id:
            return self.eve_type.name
        return f"{self.eve_group.name} ({_('group')})"

    def __str__(self):
        return f"{self.target_name} - {self.program.name}"


class BuybackItemRule(models.Model):
    """A per-program price adjustment or ban for one item or a market group.

    A market-group rule also covers every group below it; the most specific
    rule wins (the item itself, then the nearest market group).
    """

    program = models.ForeignKey(
        BuybackProgram, on_delete=models.CASCADE, related_name="item_rules"
    )
    eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, related_name="+", null=True, blank=True
    )
    eve_market_group = models.ForeignKey(
        EveMarketGroup,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    price_modifier_percent = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-100.0), MaxValueValidator(100.0)],
        help_text=_(
            "Added to the program's price modifier for this item or group, e.g. -10 "
            "pays 10% less, +5 pays 5% more."
        ),
    )
    disallow = models.BooleanField(
        default=False, help_text=_("Don't accept this item or group at all.")
    )

    class Meta:
        verbose_name = _("Buyback Item Rule")
        verbose_name_plural = _("Buyback Item Rules")
        # No condition needed: unique indexes treat NULLs as distinct, and
        # MariaDB/MySQL can't create conditional unique constraints at all.
        constraints = [
            models.UniqueConstraint(
                fields=["program", "eve_type"],
                name="buyback_rule_unique_type",
            ),
            models.UniqueConstraint(
                fields=["program", "eve_market_group"],
                name="buyback_rule_unique_market_group",
            ),
            models.CheckConstraint(
                condition=(
                    Q(eve_type__isnull=False, eve_market_group__isnull=True)
                    | Q(eve_type__isnull=True, eve_market_group__isnull=False)
                ),
                name="buyback_rule_type_xor_market_group",
            ),
        ]

    @property
    def target_name(self) -> str:
        if self.eve_type_id:
            return self.eve_type.name
        return f"{self.eve_market_group.name} ({_('market group')})"

    def __str__(self):
        return f"{self.target_name} - {self.program.name}"


class BuybackStaticPrice(models.Model):
    """A fixed ISK price for one item in a program. It replaces the market
    valuation; no price modifier, rule or density tax applies to it."""

    program = models.ForeignKey(
        BuybackProgram, on_delete=models.CASCADE, related_name="static_prices"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("ISK paid per unit."),
    )

    class Meta:
        verbose_name = _("Buyback Static Price")
        verbose_name_plural = _("Buyback Static Prices")
        unique_together = (("program", "eve_type"),)

    def __str__(self):
        return f"{self.eve_type.name}: {self.price} - {self.program.name}"


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
    hauling_cost = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text=_(
            "ISK deducted for hauling (program's ISK/m3 x volume). Already deducted "
            "from quoted_price."
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
    seller_note = models.TextField(
        blank=True,
        max_length=500,
        help_text=_("Optional note from the seller to the buyer."),
    )
    esi_items = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Items of the matched in-game contract, as [{type_id, quantity}]."),
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
    def deadline(self):
        """When a PENDING tracking number expires if no in-game contract shows up."""
        return self.created_at + timedelta(days=self.program.contract_expiry_days)

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
        """ISK difference the price modifiers, item rules and bulk-item tax made
        to this contract: the items' appraised total (before hauling and
        donation) minus base_appraisal_total. Negative means they reduced the
        payout (e.g. a -5% modifier)."""
        hauling = Decimal(str(self.hauling_cost or 0))
        return self.gross_appraisal + hauling - self.base_appraisal_total

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


class BuybackUntrackedContract(models.Model):
    """An in-game contract to a program's recipient whose title uses the
    program's tracking prefix, but whose tracking number was never issued.
    Usually a typo, sometimes an attempt to get paid for an unappraised load."""

    program = models.ForeignKey(
        BuybackProgram, on_delete=models.CASCADE, related_name="untracked_contracts"
    )
    esi_contract_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255, blank=True)
    issuer_id = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    start_location_id = models.BigIntegerField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Buyback Untracked Contract")
        verbose_name_plural = _("Buyback Untracked Contracts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.esi_contract_id})"

    @property
    def issuer_name(self) -> str:
        character = EveCharacter.objects.filter(character_id=self.issuer_id).first()
        return character.character_name if character else str(self.issuer_id or "-")


class BuybackUserSettings(models.Model):
    """A member's buyback preferences."""

    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="buyback_settings"
    )
    disable_notifications = models.BooleanField(
        default=False,
        help_text=_(
            "Don't send me Discord DMs or Auth notifications about my contracts."
        ),
    )

    class Meta:
        verbose_name = _("Buyback User Settings")
        verbose_name_plural = _("Buyback User Settings")

    def __str__(self):
        return f"{self.user} buyback settings"


class BuybackFaq(models.Model):
    """A question and answer on a corporation's Buyback FAQ page."""

    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="buyback_faqs"
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(
        default=0, help_text=_("Lower numbers are shown first.")
    )

    class Meta:
        verbose_name = _("Buyback FAQ")
        verbose_name_plural = _("Buyback FAQs")
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class CorpReprocessingConfig(models.Model):
    """How a corporation reprocesses and sells, for the "sell or reprocess"
    advice on buyback contracts. Without a row the field defaults apply."""

    ROUTE_INSTANT = "INSTANT"
    ROUTE_LISTED = "LISTED"
    SELL_ROUTE_CHOICES = (
        (ROUTE_INSTANT, _("Sell straight to Jita buy orders")),
        (ROUTE_LISTED, _("List a sell order at the Jita sell price")),
    )

    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="reprocessing_config",
    )
    ore_yield_percent = models.FloatField(
        default=90.6,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Reprocessing yield (%) for ore, ice and moon ore."),
    )
    scrap_yield_percent = models.FloatField(
        default=55.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Reprocessing yield (%) for everything else (modules, ships...)."),
    )
    reprocessing_tax_percent = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Structure reprocessing tax, as % of the materials' value."),
    )
    sales_tax_percent = models.FloatField(
        default=3.37,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Sales tax (%) when selling through a sell order."),
    )
    sell_route = models.CharField(
        max_length=8,
        choices=SELL_ROUTE_CHOICES,
        default=ROUTE_INSTANT,
        help_text=_("The selling route the advice is based on."),
    )
    margin_percent = models.FloatField(
        default=2.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Below this difference (%) the advice is \"either way\"."),
    )
    use_stock_needs = models.BooleanField(
        default=True,
        help_text=_(
            "Count materials the corporation is short of (low-stock targets) as "
            "used in-house, valued at what buying them would cost."
        ),
    )

    class Meta:
        verbose_name = _("Reprocessing Config")
        verbose_name_plural = _("Reprocessing Configs")

    def __str__(self):
        return f"{self.corporation} reprocessing"

    @classmethod
    def for_corporation(cls, corporation) -> "CorpReprocessingConfig":
        """The saved config, or an unsaved one with the defaults."""
        return cls.objects.filter(corporation=corporation).first() or cls(
            corporation=corporation
        )
