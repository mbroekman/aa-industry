"""Fixed language for Discord messages.

A Discord message must not depend on who happened to trigger it. Channel
(webhook) messages use the language chosen on their webhook configuration,
falling back to DISCORD_MESSAGE_LANGUAGE in local.py and then LANGUAGE_CODE.
Direct messages use the recipient's Alliance Auth language preference.

Build *and* send a message inside ``with discord_language(...)``; strings
translated before entering it keep the language that was active then.
"""

# Standard Library
from contextlib import contextmanager

# Django
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _


def default_language() -> str:
    """The installation-wide Discord language."""
    return getattr(settings, "DISCORD_MESSAGE_LANGUAGE", "") or settings.LANGUAGE_CODE


def channel_language(code: str | None = "") -> str:
    """A webhook configuration's language, or the default when it has none."""
    return code or default_language()


def user_language(user) -> str:
    """The recipient's Alliance Auth language, or the default."""
    profile = getattr(user, "profile", None)
    return getattr(profile, "language", "") or default_language()


@contextmanager
def discord_language(code: str):
    with translation.override(code or default_language()):
        yield


def language_choices():
    return [("", _("Default (installation setting)"))] + list(settings.LANGUAGES)
