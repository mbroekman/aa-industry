"""Buyback notifications: the seller, the program's manager and the corp channel.

Sellers get a Discord DM and an Alliance Auth notification, unless they turned
buyback notifications off. A program can post every new contract (flagged ones
always) to the corporation's buyback webhook, optionally with the item list,
and DM a manager character.
"""

# Standard Library
import logging

# Django
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

COLOR_GREEN = 3066993
COLOR_RED = 15158332
COLOR_ORANGE = 15105570
EMBED_FIELD_LIMIT = 1024


def _user_of(character):
    try:
        return character.character_ownership.user
    except Exception:  # noqa: BLE001
        return None


def _notifications_disabled(user) -> bool:
    from ..models import BuybackUserSettings

    return BuybackUserSettings.objects.filter(
        user=user, disable_notifications=True
    ).exists()


def _auth_notify(user, title: str, message: str, level: str = "info"):
    try:
        from allianceauth.notifications import notify

        notify(user, title, message, level)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not create Auth notification for {user}: {e}")


def _dm(character, message: str):
    from ..tasks.utils import notify_discord_user

    notify_discord_user(character, message)


def notify_seller(contract, title: str, message: str, level: str = "info"):
    """DM + Auth notification to the seller, unless they opted out."""
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
        text = text[: EMBED_FIELD_LIMIT - 30].rsplit("\n", 1)[0] + "\n... (see the link)"
    return text


def _webhook_url(program):
    from ..models import CorporationWebhookConfig

    config = CorporationWebhookConfig.objects.filter(
        corporation=program.corporation
    ).first()
    return config.buyback_webhook if config and config.buyback_webhook else None


def notify_new_contract(contract):
    """Fired once, when an in-game contract is first matched to the appraisal."""
    program = contract.program
    flagged = contract.status == "FLAGGED"

    webhook = _webhook_url(program)
    if webhook and (flagged or program.notify_new_contracts):
        from .discord import send_discord_webhook

        seller = contract.character.character_name if contract.character else "-"
        fields = [
            {"name": "Seller", "value": seller, "inline": True},
            {"name": "Status", "value": contract.get_status_display(), "inline": True},
            {
                "name": "Price",
                "value": f"{contract.quoted_price:,.2f} ISK",
                "inline": True,
            },
        ]
        if contract.flag_notes:
            fields.append(
                {"name": "Review notes", "value": contract.flag_notes[:EMBED_FIELD_LIMIT]}
            )
        if contract.seller_note:
            fields.append(
                {
                    "name": "Note from seller",
                    "value": contract.seller_note[:EMBED_FIELD_LIMIT],
                }
            )
        if program.notify_show_item_list:
            fields.append({"name": "Items", "value": _item_list(contract) or "-"})
        send_discord_webhook(
            webhook,
            {
                "title": (
                    f"Buyback contract flagged: {contract.tracking_number}"
                    if flagged
                    else f"New buyback contract: {contract.tracking_number}"
                ),
                "description": f"{program.name} - [open]({contract_url(contract)})",
                "color": COLOR_RED if flagged else COLOR_GREEN,
                "fields": fields,
            },
        )

    manager = program.notify_manager_character
    if manager:
        message = (
            f"New buyback contract {contract.tracking_number} in {program.name}"
            f"{' (needs review)' if flagged else ''}: {contract_url(contract)}"
        )
        _dm(manager, message)
        user = _user_of(manager)
        if user is not None:
            _auth_notify(
                user,
                f"Buyback contract {contract.tracking_number}",
                message,
                "warning" if flagged else "info",
            )


def notify_untracked_contract(untracked):
    """An in-game contract uses the program's prefix but no issued tracking number."""
    program = untracked.program
    message = (
        f"Untracked buyback contract in {program.name}: '{untracked.title}' "
        f"from {untracked.issuer_name} for {untracked.price:,.2f} ISK. Its tracking "
        "number was never issued - check it before accepting."
    )
    webhook = _webhook_url(program)
    if webhook:
        from .discord import send_discord_webhook

        send_discord_webhook(
            webhook,
            {
                "title": "Suspicious buyback contract",
                "description": message,
                "color": COLOR_ORANGE,
            },
        )
    if program.notify_manager_character:
        _dm(program.notify_manager_character, message)
