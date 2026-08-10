"""
App Models
"""

# Third Party

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo


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
        default=0.0, help_text=_("Tax percentage applied to industry jobs")
    )
    broker_fee_rate = models.FloatField(
        default=0.0, help_text=_("Broker fee percentage")
    )

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
    warning_threshold = models.BigIntegerField(
        default=500000000,
        help_text=_(
            "Balance below which a warning is sent (default: 500 million ISK)."
        ),
    )

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
        "CorpWalletDivision", on_delete=models.CASCADE, related_name="journal_entries"
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


class LedgerTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("INCOME", _("Income (Member Payment)")),
        ("PAYOUT", _("Payout (Builder Batch)")),
        ("PROCUREMENT", _("Procurement (Buy Order)")),
    )

    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ledger_transactions",
    )
    director = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_transactions",
    )

    reference = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)

    member_order = models.ForeignKey(
        "industry_reforged.MemberOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    payout_batch = models.ForeignKey(
        "industry_reforged.BuilderPayoutBatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    class Meta:
        verbose_name = _("Ledger Transaction")
        verbose_name_plural = _("Ledger Transactions")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} - {self.transaction_type} - {self.amount} ISK"
