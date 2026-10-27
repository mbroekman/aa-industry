"""Discord messages use a fixed language, not the one of whoever triggered them."""

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Django
from django.test import override_settings
from django.utils import translation

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Industry App
from industry_reforged.discord_i18n import (
    channel_language,
    default_language,
    user_language,
)
from industry_reforged.models import CorporationWebhookConfig
from industry_reforged.tasks.utils import notify_discord_user
from industry_reforged.utils.discord import send_discord_webhook, webhook_language
from industry_reforged.views.orders.notifications import notify_order_ready

from .factories import EveCharacterFactory, EveCorporationInfoFactory, UserFactory


class TestLanguageChoice:
    @override_settings(LANGUAGE_CODE="en-us")
    def test_default_falls_back_to_language_code(self):
        assert default_language() == "en-us"

    @override_settings(DISCORD_MESSAGE_LANGUAGE="nl", LANGUAGE_CODE="en-us")
    def test_default_uses_the_discord_setting(self):
        assert default_language() == "nl"
        assert channel_language("") == "nl"
        assert channel_language("de") == "de"

    @pytest.mark.django_db
    @override_settings(DISCORD_MESSAGE_LANGUAGE="en")
    def test_user_language_or_default(self):
        user = UserFactory()
        assert user_language(user) == "en"
        user.profile.language = "nl"
        assert user_language(user) == "nl"


def _payload(mock_post):
    return mock_post.call_args.kwargs["json"]["embeds"][0]


@pytest.mark.django_db
class TestWebhookLanguage:
    def _order(self, language):
        corp = EveCorporationInfoFactory()
        CorporationWebhookConfig.objects.create(
            corporation=corp,
            directors_webhook="https://discord.test/hook",
            discord_language=language,
        )
        character = EveCharacterFactory(
            corporation_id=corp.corporation_id,
            corporation_name=corp.corporation_name,
            character_name="Builder",
        )
        order = MagicMock(
            id=42,
            character=character,
            total_price=1000,
            payment_reference="ORD-1",
        )
        return order

    @patch("industry_reforged.utils.discord.requests.post")
    def test_english_webhook_while_a_dutch_user_triggers_it(self, post):
        order = self._order("en")
        with translation.override("nl"):
            notify_order_ready(order)
        assert _payload(post)["title"] == "Order #42 Ready"

    @patch("industry_reforged.utils.discord.requests.post")
    def test_dutch_webhook_while_an_english_user_triggers_it(self, post):
        order = self._order("nl")
        with translation.override("en"):
            notify_order_ready(order)
        assert _payload(post)["title"] == "Order #42 klaar"

    @override_settings(DISCORD_MESSAGE_LANGUAGE="nl")
    def test_empty_choice_uses_the_installation_default(self):
        config = CorporationWebhookConfig(discord_language="")
        assert webhook_language(config) == "nl"
        assert webhook_language(None) == "nl"

    @patch("industry_reforged.utils.discord.requests.post")
    def test_lazy_strings_are_resolved_in_the_given_language(self, post):
        # Django
        from django.utils.translation import gettext_lazy

        with translation.override("en"):
            send_discord_webhook(
                "https://discord.test/hook", {"title": gettext_lazy("Seller")}, "nl"
            )
        assert _payload(post)["title"] == "Verkoper"


@pytest.fixture
def discordbot(monkeypatch):
    """aadiscordbot isn't installed in the test environment."""
    # Standard Library
    import sys
    import types

    tasks = types.SimpleNamespace(send_direct_message_by_user_id=MagicMock())
    module = types.ModuleType("aadiscordbot")
    module.tasks = tasks
    monkeypatch.setitem(sys.modules, "aadiscordbot", module)
    monkeypatch.setitem(sys.modules, "aadiscordbot.tasks", tasks)
    return tasks.send_direct_message_by_user_id


@pytest.mark.django_db
class TestDirectMessageLanguage:
    def _character_of(self, language):
        user = UserFactory()
        user.profile.language = language
        user.profile.save()
        character = EveCharacterFactory()
        CharacterOwnership.objects.create(
            user=user, character=character, owner_hash=f"l-{character.character_id}"
        )
        return character

    def test_dm_uses_the_recipients_language(self, discordbot):
        # Django
        from django.utils.translation import gettext

        send = discordbot

        character = self._character_of("nl")
        with translation.override("en"):
            notify_discord_user(
                character,
                lambda: gettext("Your industry job %(id)s has finished.") % {"id": 7},
            )
        assert send.delay.call_args.args[1] == "Je industry-job 7 is klaar."

    @override_settings(DISCORD_MESSAGE_LANGUAGE="en")
    def test_dm_without_preference_uses_the_default(self, discordbot):
        # Django
        from django.utils.translation import gettext

        send = discordbot

        character = self._character_of("")
        with translation.override("nl"):
            notify_discord_user(
                character,
                lambda: gettext("Your industry job %(id)s has finished.") % {"id": 7},
            )
        assert send.delay.call_args.args[1] == "Your industry job 7 has finished."


@pytest.mark.django_db
def test_director_sets_the_language_for_their_corporation():
    # Django
    from django.contrib.auth.models import Permission
    from django.contrib.messages.storage.fallback import FallbackStorage
    from django.test import RequestFactory

    from industry_reforged.views.director import director_config_discord_language

    corp = EveCorporationInfoFactory()
    user = UserFactory()
    character = EveCharacterFactory(
        corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
    )
    user.profile.main_character = character
    user.profile.save()
    for codename in ("basic_access", "corp_access"):
        user.user_permissions.add(Permission.objects.get(codename=codename))
    user = user.__class__.objects.get(pk=user.pk)

    request = RequestFactory().post("/", {"discord_language": "nl-nl"})
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    response = director_config_discord_language(request)

    assert response.status_code == 302
    assert (
        CorporationWebhookConfig.objects.get(corporation=corp).discord_language
        == "nl-nl"
    )
