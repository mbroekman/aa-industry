"""App Views"""

# Django

from ..models import (
    CorporationWebhookConfig,
    MemberOrder,
)
from ..utils.discord import send_discord_webhook


def notify_order_ready(order: MemberOrder):
    # Django
    from django.contrib.auth.models import User
    from django.db.models import Q

    # Alliance Auth
    from allianceauth.notifications.models import Notification

    # 1. Auth Notification to Directors
    directors = User.objects.filter(
        Q(groups__permissions__codename="director_access")
        | Q(user_permissions__codename="director_access")
    ).distinct()

    message = f"Order #{order.id} from {order.character.character_name} is ready for delivery! Total price: {order.total_price} ISK. Payment Reference: {order.payment_reference}"

    for director in directors:
        Notification.objects.notify_user(
            user=director,
            title=f"Order #{order.id} Ready",
            message=message,
            level="success",
        )

    # 2. Discord Webhook
    webhook_config = CorporationWebhookConfig.objects.filter(
        corporation=order.corporation
    ).first()
    if webhook_config and webhook_config.directors_webhook:
        embed = {
            "title": f"Order #{order.id} Ready",
            "description": f"**{order.character.character_name}**'s order is fully built and ready to be delivered!\nPayment Reference: `{order.payment_reference}`\nTotal: `{order.total_price:,.2f} ISK`",
            "color": 3066993,  # Green
        }
        send_discord_webhook(webhook_config.directors_webhook, embed)
