"""Buyback notifications: the seller, the program's manager and the corp channel.

Sellers get a Discord DM and an Alliance Auth notification, unless they turned
buyback notifications off. A program can post every new contract (flagged ones
always) to the corporation's buyback webhook, optionally with the item list,
and DM a manager character.

Messages to a person are built in that person's Alliance Auth language; posts
to the webhook in the language of the corporation's webhook configuration.
"""

# Standard Library
import logging

# Django
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext

from ..discord_i18n import discord_language, user_language

logger = logging.getLogger(__name__)

COLOR_GREEN = 3066993
COLOR_RED = 15158332
COLOR_ORANGE = 15105570
EMBED_FIELD_LIMIT = 1024


def _user_of(character):
    try:
        return character.character_ownership.user
    except Exception:
        return None


def _notifications_disabled(user) -> bool:
    from ..models import BuybackUserSettings

    return BuybackUserSettings.objects.filter(
        user=user, disable_notifications=True
    ).exists()


def _text(value) -> str:
    return str(value() if callable(value) else value)


def _auth_notify(user, title, message, level: str = "info"):
    try:
        # Alliance Auth
        from allianceauth.notifications import notify

        with discord_language(user_language(user)):
            notify(user, _text(title), _text(message), level)
    except Exception as e:
        logger.warning(f"Could not create Auth notification for {user}: {e}")


def _dm(character, message):
    from ..tasks.utils import notify_discord_user

    notify_discord_user(character, message)


def notify_seller(contract, title, message, level: str = "info"):
    """DM + Auth notification to the seller, unless they opted out. `title`
    and `message` may be callables; they are built in the seller's language."""
    if not contract.character:
        return
    user = _user_of(contract.character)
    if user is not None and _notifications_disabled(user):
        return
    _dm(contract.character, message)
    if user is not None:
        _auth_notify(user, title, message, level)


def contract_url(contract) -> str:
    site = getattr(settings, "SITE_URL", "").rstrip("/")
    path = reverse(
        "industry_reforged:buyback_contract_detail",
        kwargs={"tracking_number": contract.tracking_number},
    )
    return f"{site}{path}" if site else path


def _item_list(contract) -> str:
    lines = [
        f"{item.quantity:,} x {item.eve_type.name}"
        for item in contract.items.select_related("eve_type")
    ]
    text = "\n".join(lines)
    if len(text) > EMBED_FIELD_LIMIT:
        text = (
            text[: EMBED_FIELD_LIMIT - 30].rsplit("\n", 1)[0]
            + "\n... "
            + gettext("(see the link)")
        )
    return text


def _webhook_config(program):
    from ..models import CorporationWebhookConfig

    config = CorporationWebhookConfig.objects.filter(
        corporation=program.corporation
    ).first()
    return config if config and config.buyback_webhook else None


def notify_new_contract(contract):
    """Fired once, when an in-game contract is first matched to the appraisal."""
    from .discord import send_discord_webhook, webhook_language

    program = contract.program
    flagged = contract.status == "FLAGGED"

    config = _webhook_config(program)
    if config and (flagged or program.notify_new_contracts):
        language = webhook_language(config)
        with discord_language(language):
            seller = contract.character.character_name if contract.character else "-"
            fields = [
                {"name": gettext("Seller"), "value": seller, "inline": True},
                {
                    "name": gettext("Status"),
                    "value": str(contract.get_status_display()),
                    "inline": True,
                },
                {
                    "name": gettext("Price"),
                    "value": f"{contract.quoted_price:,.2f} ISK",
                    "inline": True,
                },
            ]
            if contract.flag_notes:
                fields.append(
                    {
                        "name": gettext("Review notes"),
                        "value": contract.flag_notes[:EMBED_FIELD_LIMIT],
                    }
                )
            if contract.seller_note:
                fields.append(
                    {
                        "name": gettext("Note from seller"),
                        "value": contract.seller_note[:EMBED_FIELD_LIMIT],
                    }
                )
            if program.notify_show_item_list:
                fields.append(
                    {"name": gettext("Items"), "value": _item_list(contract) or "-"}
                )
            title = (
                gettext("Buyback contract flagged: %(tracking)s")
                if flagged
                else gettext("New buyback contract: %(tracking)s")
            ) % {"tracking": contract.tracking_number}
            embed = {
                "title": title,
                "description": f"{program.name} - [{gettext('open')}]({contract_url(contract)})",
                "color": COLOR_RED if flagged else COLOR_GREEN,
                "fields": fields,
            }
        send_discord_webhook(config.buyback_webhook, embed, language)

    manager = program.notify_manager_character
    if manager:

        def message():
            text = (
                gettext(
                    "New buyback contract %(tracking)s in %(program)s (needs review): %(url)s"
                )
                if flagged
                else gettext(
                    "New buyback contract %(tracking)s in %(program)s: %(url)s"
                )
            )
            return text % {
                "tracking": contract.tracking_number,
                "program": program.name,
                "url": contract_url(contract),
            }

        _dm(manager, message)
        user = _user_of(manager)
        if user is not None:
            _auth_notify(
                user,
                lambda: gettext("Buyback contract %(tracking)s")
                % {"tracking": contract.tracking_number},
                message,
                "warning" if flagged else "info",
            )


def notify_untracked_contract(untracked):
    """An in-game contract uses the program's prefix but no issued tracking number."""
    from .discord import send_discord_webhook, webhook_language

    program = untracked.program

    def message():
        return gettext(
            "Untracked buyback contract in %(program)s: '%(title)s' from %(issuer)s "
            "for %(price)s ISK. Its tracking number was never issued - check it "
            "before accepting."
        ) % {
            "program": program.name,
            "title": untracked.title,
            "issuer": untracked.issuer_name,
            "price": f"{untracked.price:,.2f}",
        }

    config = _webhook_config(program)
    if config:
        language = webhook_language(config)
        with discord_language(language):
            embed = {
                "title": gettext("Suspicious buyback contract"),
                "description": message(),
                "color": COLOR_ORANGE,
            }
        send_discord_webhook(config.buyback_webhook, embed, language)
    if program.notify_manager_character:
        _dm(program.notify_manager_character, message)
