"""App Views"""

# Django
from django.utils.translation import gettext as _

from ...discord_i18n import discord_language, user_language
from ...models import (
    CorporationWebhookConfig,
    MemberOrder,
)
from ...utils.discord import send_discord_webhook, webhook_language


def notify_order_ready(order: MemberOrder):
    # Django
    from django.contrib.auth.models import User
    from django.db.models import Q

    # Alliance Auth
    from allianceauth.notifications.models import Notification

    # 1. Auth Notification to Directors, each in their own language
    directors = User.objects.filter(
        Q(groups__permissions__codename="director_access")
        | Q(user_permissions__codename="director_access")
    ).distinct()

    for director in directors:
        with discord_language(user_language(director)):
            Notification.objects.notify_user(
                user=director,
                title=_("Order #%(id)s Ready") % {"id": order.id},
                message=_(
                    "Order #%(id)s from %(name)s is ready for delivery! Total price: "
                    "%(total)s ISK. Payment Reference: %(reference)s"
                )
                % {
                    "id": order.id,
                    "name": order.character.character_name,
                    "total": order.total_price,
                    "reference": order.payment_reference,
                },
                level="success",
            )

    # 2. Discord Webhook
    webhook_config = CorporationWebhookConfig.objects.filter(
        corporation__corporation_id=order.character.corporation_id
    ).first()
    if webhook_config and webhook_config.directors_webhook:
        language = webhook_language(webhook_config)
        with discord_language(language):
            embed = {
                "title": _("Order #%(id)s Ready") % {"id": order.id},
                "description": _(
                    "**%(name)s**'s order is fully built and ready to be delivered!\n"
                    "Payment Reference: `%(reference)s`\nTotal: `%(total)s ISK`"
                )
                % {
                    "name": order.character.character_name,
                    "reference": order.payment_reference,
                    "total": f"{order.total_price:,.2f}",
                },
                "color": 3066993,  # Green
            }
        send_discord_webhook(webhook_config.directors_webhook, embed, language)
