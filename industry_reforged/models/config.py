"""
App Models
"""

# Third Party

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo


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
