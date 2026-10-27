# Standard Library
import logging

# Third Party
import requests

# Django
from django.utils.functional import Promise

from ..discord_i18n import channel_language, default_language, discord_language

logger = logging.getLogger(__name__)


def webhook_language(config) -> str:
    """The language for messages to a CorporationWebhookConfig's webhooks."""
    return channel_language(getattr(config, "discord_language", "") if config else "")


def _resolve(value):
    """Turn lazy translations into text (inside the active language)."""
    if isinstance(value, Promise):
        return str(value)
    if isinstance(value, dict):
        return {key: _resolve(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_resolve(item) for item in value]
    return value


def send_discord_webhook(webhook_url, embed_data, language=None):
    """
    Send an embedded message to a Discord Webhook.

    Build the embed inside ``discord_language(language)`` as well: text that
    was translated before stays in the language that was active then.

    :param webhook_url: str URL of the Discord webhook
    :param embed_data: dict containing the embed payload (title, description, color, etc.)
    :param language: language code for lazy strings in the embed; defaults to
        the installation's Discord language
    """
    if not webhook_url:
        return

    with discord_language(language or default_language()):
        payload = {"embeds": [_resolve(embed_data)]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord Webhook: {e}")
