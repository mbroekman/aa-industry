"""Buyback member pages (TASK-276): rules & prices, FAQ, manual contract refresh."""

# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Group, Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.test import RequestFactory

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Industry App
from industry_reforged.models import (
    BuybackFaq,
    BuybackItemRule,
    BuybackStaticPrice,
    BuybackWatchlistItem,
)
from industry_reforged.views.buyback.director import (
    director_buyback_refresh_contracts,
    director_config_buyback_faq_delete,
    director_config_buyback_faq_edit,
)
from industry_reforged.views.buyback.member import buyback_faq, buyback_program_rules

from .factories import (
    BuybackProgramFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def mock_static(monkeypatch):
    # Django
    from django.contrib.staticfiles.storage import staticfiles_storage

    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}")
    try:
        # Third Party
        from sri.templatetags import sri

        monkeypatch.setattr(
            sri,
            "sri_integrity_static",
            lambda path, algorithm_type=None: "sha256-dummy",
        )
    except ImportError:
        pass


def _user(corporation=None, perms=("basic_access",)):
    user = UserFactory()
    corporation = corporation or EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corporation.corporation_id,
        corporation_name=corporation.corporation_name,
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"p-{character.character_id}"
    )
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user.__class__.objects.get(pk=user.pk)


def _request(user, method="get", data=None):
    request = getattr(RequestFactory(), method)("/", data or {})
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
class TestProgramRulesPage:
    def test_shows_rules_and_fixed_prices(self):
        program = BuybackProgramFactory(hauling_fuel_cost=250.0)
        BuybackItemRule.objects.create(
            program=program,
            eve_type=EveTypeFactory(name="Zydrine"),
            price_modifier_percent=-15.0,
        )
        BuybackStaticPrice.objects.create(
            program=program,
            eve_type=EveTypeFactory(name="PLEX"),
            price=Decimal("5000000"),
        )

        html = buyback_program_rules(_request(_user()), program.id).content.decode()

        assert "Zydrine" in html and "-15.0%" in html
        assert "PLEX" in html
        assert "250 ISK/m³" in html

    def test_restricted_program_is_a_404(self):
        program = BuybackProgramFactory()
        program.restricted_to_groups.add(Group.objects.create(name="Insiders"))
        with pytest.raises(Http404):
            buyback_program_rules(_request(_user()), program.id)

    def test_watchlist_only_for_the_programs_directors(self):
        corp = EveCorporationInfoFactory()
        program = BuybackProgramFactory(corporation=corp)
        BuybackWatchlistItem.objects.create(
            program=program, eve_type=EveTypeFactory(name="Secret Item"), reason="x"
        )

        member_html = buyback_program_rules(_request(_user()), program.id).content
        director = _user(corporation=corp, perms=("basic_access", "corp_access"))
        director_html = buyback_program_rules(_request(director), program.id).content

        assert b"Secret Item" not in member_html
        assert b"Secret Item" in director_html


@pytest.mark.django_db
class TestFaqPage:
    def test_shows_faq_of_corporations_whose_programs_are_visible(self):
        visible_corp, hidden_corp = (
            EveCorporationInfoFactory(),
            EveCorporationInfoFactory(),
        )
        BuybackProgramFactory(corporation=visible_corp)
        hidden = BuybackProgramFactory(corporation=hidden_corp)
        hidden.restricted_to_groups.add(Group.objects.create(name="Closed"))
        BuybackFaq.objects.create(
            corporation=visible_corp, question="When am I paid?", answer="Daily."
        )
        BuybackFaq.objects.create(
            corporation=hidden_corp, question="Hidden question?", answer="No."
        )

        html = buyback_faq(_request(_user())).content.decode()

        assert "When am I paid?" in html
        assert "Hidden question?" not in html
        assert "How it works" in html


@pytest.mark.django_db
class TestFaqManagement:
    def test_add_entry_for_own_corporation(self):
        corp = EveCorporationInfoFactory()
        director = _user(corporation=corp, perms=("corp_access",))
        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_faq_edit(
                _request(
                    director,
                    "post",
                    {"question": "Fees?", "answer": "None.", "order": "1"},
                )
            )
        faq = BuybackFaq.objects.get()
        assert faq.corporation == corp and faq.question == "Fees?"

    def test_other_corporations_entry_cannot_be_edited_or_deleted(self):
        foreign = BuybackFaq.objects.create(
            corporation=EveCorporationInfoFactory(), question="Q", answer="A"
        )
        director = _user(perms=("corp_access",))
        with pytest.raises(Http404):
            director_config_buyback_faq_edit(_request(director), foreign.id)
        with pytest.raises(Http404):
            director_config_buyback_faq_delete(_request(director, "post"), foreign.id)
        assert BuybackFaq.objects.filter(pk=foreign.pk).exists()


@pytest.mark.django_db
class TestRefreshContracts:
    @patch("industry_reforged.tasks.buyback.buyback_poll_contracts.delay")
    def test_queues_a_poll(self, delay):
        director = _user(perms=("corp_access",))
        response = director_buyback_refresh_contracts(_request(director, "post"))
        delay.assert_called_once()
        assert response.status_code == 302

    def test_requires_post(self):
        director = _user(perms=("corp_access",))
        assert director_buyback_refresh_contracts(_request(director)).status_code == 405
