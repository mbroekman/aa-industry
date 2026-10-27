"""Buyback contract handling & notifications (TASK-275)."""

# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from esi.models import Token

# AA Industry App
from industry_reforged.models import (
    BuybackContract,
    BuybackUntrackedContract,
    BuybackUserSettings,
    BuybackWatchlistItem,
    CorporationSyncConfig,
    CorporationWebhookConfig,
)
from industry_reforged.tasks.buyback import (
    buyback_poll_contracts,
    watchlist_flag_notes,
)
from industry_reforged.utils import buyback_notify
from industry_reforged.views.buyback.director import (
    director_buyback_untracked_dismiss,
)
from industry_reforged.views.buyback.member import (
    buyback_calculator,
    buyback_notification_settings,
    item_comparison,
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

DM = "industry_reforged.tasks.utils.notify_discord_user"
AUTH_NOTIFY = "allianceauth.notifications.notify"
WEBHOOK = "industry_reforged.utils.discord.send_discord_webhook"


def _owned_character(user=None):
    user = user or UserFactory()
    character = EveCharacterFactory()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"h-{character.character_id}"
    )
    return user, character


def _webhook(program):
    CorporationWebhookConfig.objects.create(
        corporation=program.corporation, buyback_webhook="https://example.invalid/h"
    )


@pytest.mark.django_db
class TestSellerNotifications:
    @patch(AUTH_NOTIFY)
    @patch(DM)
    def test_seller_gets_dm_and_auth_notification(self, dm, auth_notify):
        user, character = _owned_character()
        contract = BuybackContractFactory(character=character)

        buyback_notify.notify_seller(contract, "Title", "Hello", "success")

        dm.assert_called_once_with(character, "Hello")
        auth_notify.assert_called_once_with(user, "Title", "Hello", "success")

    @patch(AUTH_NOTIFY)
    @patch(DM)
    def test_seller_who_opted_out_gets_nothing(self, dm, auth_notify):
        user, character = _owned_character()
        BuybackUserSettings.objects.create(user=user, disable_notifications=True)
        contract = BuybackContractFactory(character=character)

        buyback_notify.notify_seller(contract, "Title", "Hello")

        dm.assert_not_called()
        auth_notify.assert_not_called()


@pytest.mark.django_db
class TestNewContractNotifications:
    @patch(WEBHOOK)
    def test_matched_contract_is_posted_when_enabled(self, webhook):
        program = BuybackProgramFactory(notify_new_contracts=True)
        _webhook(program)
        contract = BuybackContractFactory(program=program, status="MATCHED")

        buyback_notify.notify_new_contract(contract)

        embed = webhook.call_args[0][1]
        assert "New buyback contract" in embed["title"]
        assert embed["color"] == buyback_notify.COLOR_GREEN

    @patch(WEBHOOK)
    def test_matched_contract_is_not_posted_when_disabled_but_flagged_is(self, webhook):
        program = BuybackProgramFactory(notify_new_contracts=False)
        _webhook(program)

        buyback_notify.notify_new_contract(
            BuybackContractFactory(program=program, status="MATCHED")
        )
        webhook.assert_not_called()

        buyback_notify.notify_new_contract(
            BuybackContractFactory(program=program, status="FLAGGED")
        )
        assert webhook.call_args[0][1]["color"] == buyback_notify.COLOR_RED

    @patch(WEBHOOK)
    def test_item_list_and_seller_note_in_the_post(self, webhook):
        program = BuybackProgramFactory(notify_show_item_list=True)
        _webhook(program)
        contract = BuybackContractFactory(
            program=program, status="MATCHED", seller_note="Mostly veldspar"
        )
        BuybackContractItemFactory(
            contract=contract, eve_type=EveTypeFactory(name="Veldspar"), quantity=1000
        )

        buyback_notify.notify_new_contract(contract)

        fields = {f["name"]: f["value"] for f in webhook.call_args[0][1]["fields"]}
        assert fields["Items"] == "1,000 x Veldspar"
        assert fields["Note from seller"] == "Mostly veldspar"

    @patch(AUTH_NOTIFY)
    @patch(DM)
    @patch(WEBHOOK)
    def test_manager_character_gets_a_dm(self, _webhook_call, dm, _auth):
        _, manager = _owned_character()
        program = BuybackProgramFactory(notify_manager_character=manager)
        contract = BuybackContractFactory(program=program, status="MATCHED")

        buyback_notify.notify_new_contract(contract)

        assert dm.call_args[0][0] == manager
        assert contract.tracking_number in dm.call_args[0][1]()


def _esi_contract(**fields):
    defaults = {
        "type": "item_exchange",
        "title": "BB-ABCD1234",
        "price": 1000.0,
        "start_location_id": None,
        "acceptor_id": None,
        "assignee_id": None,
        "issuer_id": 90000001,
        "contract_id": 555,
        "status": "outstanding",
        "date_expired": None,
    }
    defaults.update(fields)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


@pytest.mark.django_db
class TestUntrackedContracts:
    def setup_method(self):
        cache.clear()

    def _program_with_token(self):
        program = BuybackProgramFactory()
        character = EveCharacterFactory()
        CorporationSyncConfig.objects.create(
            corporation=program.corporation, sync_character=character
        )
        Token.objects.create(
            character_id=character.character_id,
            user=UserFactory(),
            character_name=character.character_name,
            character_owner_hash="sync",
        ).scopes.create(name="esi-contracts.read_corporation_contracts.v1")
        _webhook(program)
        return program

    def _poll(self, mock_esi, contracts):
        cache.clear()
        api = mock_esi.client.Contracts
        api.GetCorporationsCorporationIdContracts.return_value.results.return_value = (
            contracts
        )
        buyback_poll_contracts()

    @patch(WEBHOOK)
    @patch("industry_reforged.tasks.buyback.esi")
    def test_unknown_tracking_number_is_recorded_once(self, mock_esi, webhook):
        program = self._program_with_token()
        contract = _esi_contract(
            title="BB-NEVER123", assignee_id=program.corporation.corporation_id
        )

        self._poll(mock_esi, [contract])
        self._poll(mock_esi, [contract])

        untracked = BuybackUntrackedContract.objects.get()
        assert untracked.program == program
        assert untracked.title == "BB-NEVER123"
        assert webhook.call_count == 1

    @patch(WEBHOOK)
    @patch("industry_reforged.tasks.buyback.esi")
    def test_contracts_to_someone_else_or_finished_are_ignored(self, mock_esi, _w):
        program = self._program_with_token()
        self._poll(
            mock_esi,
            [
                _esi_contract(title="BB-OTHER123", assignee_id=1, contract_id=1),
                _esi_contract(
                    title="BB-DONE1234",
                    assignee_id=program.corporation.corporation_id,
                    status="finished",
                    contract_id=2,
                ),
            ],
        )
        assert not BuybackUntrackedContract.objects.exists()

    @patch(WEBHOOK)
    @patch("industry_reforged.tasks.buyback.esi")
    def test_issued_tracking_number_is_not_untracked(self, mock_esi, _w):
        program = self._program_with_token()
        BuybackContractFactory(
            program=program, tracking_number="BB-PAID1234", status="PAID"
        )
        self._poll(
            mock_esi,
            [
                _esi_contract(
                    title="BB-PAID1234", assignee_id=program.corporation.corporation_id
                )
            ],
        )
        assert not BuybackUntrackedContract.objects.exists()


@pytest.mark.django_db
class TestMatchedItems:
    def setup_method(self):
        cache.clear()

    @patch(DM)
    @patch("industry_reforged.tasks.buyback.esi")
    def test_esi_items_are_stored_and_compared(self, mock_esi, _dm):
        program = TestUntrackedContracts()._program_with_token()
        trit, pye = EveTypeFactory(name="Tritanium"), EveTypeFactory(name="Pyerite")
        contract = BuybackContractFactory(
            program=program, tracking_number="BB-ABCD1234", quoted_price=1000.0
        )
        BuybackContractItemFactory(contract=contract, eve_type=trit, quantity=100)
        BuybackContractItemFactory(contract=contract, eve_type=pye, quantity=50)

        api = mock_esi.client.Contracts
        api.GetCorporationsCorporationIdContracts.return_value.results.return_value = [
            _esi_contract(
                start_location_id=program.facilities.first().facility_id,
                assignee_id=program.corporation.corporation_id,
            )
        ]
        api.GetCorporationsCorporationIdContractsContractIdItems.return_value.result.return_value = [
            MagicMock(type_id=trit.id, quantity=100),
            MagicMock(type_id=pye.id, quantity=40),
        ]
        with patch(WEBHOOK):
            buyback_poll_contracts()

        contract.refresh_from_db()
        assert contract.esi_items == [
            {"type_id": trit.id, "quantity": 100},
            {"type_id": pye.id, "quantity": 40},
        ]
        rows = {row["name"]: row for row in item_comparison(contract)}
        assert rows["Tritanium"]["matches"] is True
        assert rows["Pyerite"] == {
            "name": "Pyerite",
            "quoted": 50,
            "actual": 40,
            "matches": False,
        }

    def test_no_comparison_before_matching(self):
        assert item_comparison(BuybackContractFactory()) == []


@pytest.mark.django_db
class TestWatchlistGroupFlag:
    def test_group_entry_in_flag_mode_produces_a_note(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory()
        BuybackWatchlistItem.objects.create(
            program=program, eve_group=item.eve_group, reason="audit group"
        )
        notes = watchlist_flag_notes(program, [item.id])
        assert len(notes) == 1 and "audit group" in notes[0]


def _member():
    user = UserFactory()
    corp = EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"m-{character.character_id}"
    )
    user.user_permissions.add(Permission.objects.get(codename="basic_access"))
    return user.__class__.objects.get(pk=user.pk), corp


def _post(user, data=None):
    request = RequestFactory().post("/", data or {})
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
class TestMemberViews:
    @patch("industry_reforged.views.buyback.member.calculate_buyback_quote")
    def test_seller_note_is_stored(self, mock_quote):
        user, _ = _member()
        program = BuybackProgramFactory()
        trit = EveTypeFactory(name="Tritanium")
        mock_quote.return_value = (
            Decimal("100"),
            [
                {
                    "eve_type": trit,
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
        buyback_calculator(
            _post(
                user,
                {
                    "program_id": program.id,
                    "inventory_text": "Tritanium\t100",
                    "seller_note": "  From the Jita run  ",
                    "confirm": "1",
                },
            )
        )
        assert BuybackContract.objects.get().seller_note == "From the Jita run"

    def test_notification_toggle(self):
        user, _ = _member()
        buyback_notification_settings(_post(user, {"notifications": "off"}))
        assert BuybackUserSettings.objects.get(user=user).disable_notifications
        buyback_notification_settings(_post(user, {"notifications": "on"}))
        assert not BuybackUserSettings.objects.get(user=user).disable_notifications


@pytest.mark.django_db
class TestDismissUntracked:
    def _director(self, corp):
        user = UserFactory()
        user.profile.main_character = EveCharacterFactory(
            corporation_id=corp.corporation_id
        )
        user.profile.save()
        user.user_permissions.add(Permission.objects.get(codename="corp_access"))
        return user.__class__.objects.get(pk=user.pk)

    def test_dismiss_own_corporations_contract(self):
        corp = EveCorporationInfoFactory()
        untracked = BuybackUntrackedContract.objects.create(
            program=BuybackProgramFactory(corporation=corp), esi_contract_id=1
        )
        director_buyback_untracked_dismiss(_post(self._director(corp)), untracked.id)
        untracked.refresh_from_db()
        assert untracked.dismissed is True

    def test_cannot_dismiss_another_corporations_contract(self):
        untracked = BuybackUntrackedContract.objects.create(
            program=BuybackProgramFactory(), esi_contract_id=2
        )
        with pytest.raises(Http404):
            director_buyback_untracked_dismiss(
                _post(self._director(EveCorporationInfoFactory())), untracked.id
            )
