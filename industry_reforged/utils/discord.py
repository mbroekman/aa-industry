# Standard Library
import logging

# Third Party
import requests

logger = logging.getLogger(__name__)


def send_discord_webhook(webhook_url, embed_data):
    """
    Send an embedded message to a Discord Webhook.

    :param webhook_url: str URL of the Discord webhook
    :param embed_data: dict containing the embed payload (title, description, color, etc.)
    """
    if not webhook_url:
        return

    payload = {"embeds": [embed_data]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord Webhook: {e}")
