"""Buyback access & visibility (TASK-273): group/state restrictions, public
programs, director scoping of contract pages, tracking prefixes and the
character-recipient contract source."""

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership, State
from esi.models import Token

# AA Industry App
from industry_reforged import auth_hooks, urls
from industry_reforged.models import BuybackContract, BuybackProgram
from industry_reforged.tasks.buyback import buyback_poll_contracts
from industry_reforged.views.buyback.member import (
    buyback_calculator,
    buyback_contract_detail,
)
from industry_reforged.views.buyback.public import (
    buyback_public_calculator,
    buyback_public_contract,
)

from .factories import (
    BuybackContractFactory,
    BuybackContractItemFactory,
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


def _member(corporation=None, perms=("basic_access",)):
    user = UserFactory()
    corporation = corporation or EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corporation.corporation_id,
        corporation_name=corporation.corporation_name,
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"hash-{character.character_id}"
    )
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user.__class__.objects.get(pk=user.pk)


def _request(rf, user, method="get", data=None):
    request = getattr(rf, method)("/", data or {})
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
class TestProgramVisibility:
    def test_unrestricted_program_is_visible_to_every_member(self):
        program = BuybackProgramFactory()
        assert program.is_visible_to(_member())

    def test_group_restriction(self):
        group = Group.objects.create(name="Buyback Sellers")
        program = BuybackProgramFactory()
        program.restricted_to_groups.add(group)

        outsider = _member()
        insider = _member()
        insider.groups.add(group)

        assert not program.is_visible_to(outsider)
        assert program.is_visible_to(insider)

    def test_state_restriction(self):
        blue = State.objects.create(name="Buyback Test State", priority=777)
        program = BuybackProgramFactory()
        program.restricted_to_states.add(blue)

        member = _member()
        assert not program.is_visible_to(member)

        member.profile.state = blue
        member.profile.save(update_fields=["state"])
        member = member.__class__.objects.get(pk=member.pk)
        assert program.is_visible_to(member)

    def test_director_always_sees_own_corporations_restricted_program(self):
        corp = EveCorporationInfoFactory()
        program = BuybackProgramFactory(corporation=corp)
        program.restricted_to_groups.add(Group.objects.create(name="Nobody"))

        director = _member(corporation=corp, perms=("basic_access", "corp_access"))
        assert program.is_visible_to(director)

    def test_inactive_program_is_never_visible(self):
        program = BuybackProgramFactory(is_active=False, is_public=True)
        assert not program.is_visible_to(_member())
        assert not program.is_visible_to(AnonymousUser())

    def test_anonymous_only_sees_public_programs(self):
        public = BuybackProgramFactory(is_public=True)
        private = BuybackProgramFactory()
        visible = set(BuybackProgram.objects.visible_to(AnonymousUser()))
        assert visible == {public}
        assert private not in visible


@pytest.mark.django_db
class TestCalculatorRespectsRestrictions:
    def test_posting_to_a_restricted_program_is_a_404(self):
        program = BuybackProgramFactory()
        program.restricted_to_groups.add(Group.objects.create(name="Inner Circle"))
        EveTypeFactory(name="Tritanium")

        request = _request(
            RequestFactory(),
            _member(),
            "post",
            {
                "program_id": program.id,
                "inventory_text": "Tritanium\t100",
                "confirm": "1",
            },
        )
        with pytest.raises(Http404):
            buyback_calculator(request)
        assert not BuybackContract.objects.exists()

    def test_non_numeric_program_id_is_a_404(self):
        request = _request(RequestFactory(), _member(), "post", {"program_id": "abc"})
        with pytest.raises(Http404):
            buyback_calculator(request)

    @patch("industry_reforged.views.buyback.member.calculate_buyback_quote")
    def test_tracking_number_uses_the_program_prefix(self, mock_quote):
        program = BuybackProgramFactory(tracking_prefix="GOON")
        eve_type = EveTypeFactory(name="Tritanium")
        mock_quote.return_value = (
            100,
            [
                {
                    "eve_type": eve_type,
                    "quantity": 100,
                    "unit_price": 1,
                    "line_total": 100,
                    "base_unit_price": 1,
                    "base_line_total": 100,
                    "blocked": False,
                    "flagged": False,
                    "value_source": "market",
                    "watchlist_reason": "",
                }
            ],
        )
        request = _request(
            RequestFactory(),
            _member(),
            "post",
            {
                "program_id": program.id,
                "inventory_text": "Tritanium\t100",
                "confirm": "1",
            },
        )
        buyback_calculator(request)

        contract = BuybackContract.objects.get()
        assert contract.tracking_number.startswith("GOON-")
        assert len(contract.tracking_number) == len("GOON-") + 8


@pytest.mark.django_db
class TestPublicCalculator:
    @patch("industry_reforged.views.buyback.member.calculate_buyback_quote")
    def test_anonymous_submission_on_a_public_program(self, mock_quote):
        program = BuybackProgramFactory(is_public=True)
        eve_type = EveTypeFactory(name="Tritanium")
        mock_quote.return_value = (
            100,
            [
                {
                    "eve_type": eve_type,
                    "quantity": 100,
                    "unit_price": 1,
                    "line_total": 100,
                    "base_unit_price": 1,
                    "base_line_total": 100,
                    "blocked": False,
                    "flagged": False,
                    "value_source": "market",
                    "watchlist_reason": "",
                }
            ],
        )
        request = _request(
            RequestFactory(),
            AnonymousUser(),
            "post",
            {
                "program_id": program.id,
                "inventory_text": "Tritanium\t100",
                "confirm": "1",
            },
        )
        response = buyback_public_calculator(request, program.id)

        contract = BuybackContract.objects.get()
        assert contract.character is None
        assert contract.is_public_submission is True
        assert response.status_code == 302
        assert contract.tracking_number in response.url
        assert "/public/contract/" in response.url

    def test_public_calculator_page_renders_for_anonymous(self):
        program = BuybackProgramFactory(is_public=True, name="Open Buyback")
        response = buyback_public_calculator(
            _request(RequestFactory(), AnonymousUser()), program.id
        )
        assert response.status_code == 200
        assert "Open Buyback" in response.content.decode()

    def test_non_public_program_is_a_404(self):
        program = BuybackProgramFactory(is_public=False)
        with pytest.raises(Http404):
            buyback_public_calculator(
                _request(RequestFactory(), AnonymousUser()), program.id
            )

    def test_public_contract_page_hides_review_notes_and_cancel(self):
        program = BuybackProgramFactory(is_public=True)
        contract = BuybackContractFactory(
            program=program,
            character=None,
            flag_watchlist=True,
            flag_notes="internal reviewer note",
        )
        BuybackContractItemFactory(contract=contract)

        response = buyback_public_contract(
            _request(RequestFactory(), AnonymousUser()), contract.tracking_number
        )
        html = response.content.decode()
        assert response.status_code == 200
        assert contract.tracking_number in html
        assert "internal reviewer note" not in html
        assert "/cancel/" not in html

    def test_public_contract_page_is_404_for_private_programs(self):
        contract = BuybackContractFactory()
        with pytest.raises(Http404):
            buyback_public_contract(
                _request(RequestFactory(), AnonymousUser()), contract.tracking_number
            )


class TestPublicViewRegistration:
    def test_excluded_views_are_the_last_url_patterns(self):
        """Alliance Auth stops decorating at the first excluded view, so they
        must come last or later routes would lose their login requirement."""
        hook = auth_hooks.register_urls()
        last = [p.lookup_str for p in urls.urlpatterns[-len(hook.excluded_views) :]]
        assert sorted(last) == sorted(hook.excluded_views)


@pytest.mark.django_db
class TestContractDetailScoping:
    def test_director_of_another_corporation_is_denied(self):
        contract = BuybackContractFactory()
        director = _member(perms=("basic_access", "corp_access"))

        response = buyback_contract_detail(
            _request(RequestFactory(), director), contract.tracking_number
        )
        assert response.status_code == 302  # redirected with "Access denied."

    @patch("industry_reforged.views.buyback.member.render")
    def test_director_of_the_programs_corporation_is_allowed(self, mock_render):
        corp = EveCorporationInfoFactory()
        contract = BuybackContractFactory(
            program=BuybackProgramFactory(corporation=corp)
        )
        director = _member(corporation=corp, perms=("basic_access", "corp_access"))

        buyback_contract_detail(
            _request(RequestFactory(), director), contract.tracking_number
        )
        mock_render.assert_called_once()


@pytest.mark.django_db
class TestCharacterRecipientPolling:
    def setup_method(self):
        cache.clear()

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_character_recipient_reads_that_characters_contracts(
        self, mock_esi, _notify
    ):
        receiver = EveCharacterFactory()
        program = BuybackProgramFactory(
            recipient_type="CHARACTER", recipient_character=receiver
        )
        Token.objects.create(
            character_id=receiver.character_id,
            user=UserFactory(),
            character_name=receiver.character_name,
            character_owner_hash="receiver",
        ).scopes.create(name="esi-contracts.read_character_contracts.v1")

        eve_type = EveTypeFactory()
        contract = BuybackContractFactory(
            program=program, tracking_number="BB-ABCD1234", quoted_price=1000.0
        )
        BuybackContractItemFactory(contract=contract, eve_type=eve_type, quantity=5)

        esi_contract = MagicMock(
            type="item_exchange",
            title="BB-ABCD1234",
            price=1000.0,
            start_location_id=program.facilities.first().facility_id,
            acceptor_id=None,
            assignee_id=receiver.character_id,
            issuer_id=None,
            contract_id=777,
            status="outstanding",
            date_expired=None,
        )
        item = MagicMock(type_id=eve_type.id, quantity=5)
        api = mock_esi.client.Contracts
        api.GetCharactersCharacterIdContracts.return_value.results.return_value = [
            esi_contract
        ]
        api.GetCharactersCharacterIdContractsContractIdItems.return_value.result.return_value = [
            item
        ]

        buyback_poll_contracts()

        api.GetCorporationsCorporationIdContracts.assert_not_called()
        contract.refresh_from_db()
        assert contract.status == "MATCHED"
        assert contract.flag_receiver_mismatch is False

    @patch("industry_reforged.tasks.buyback.esi")
    def test_character_recipient_without_token_is_skipped(self, mock_esi):
        BuybackProgramFactory(
            recipient_type="CHARACTER", recipient_character=EveCharacterFactory()
        )
        buyback_poll_contracts()
        mock_esi.client.Contracts.GetCharactersCharacterIdContracts.assert_not_called()
