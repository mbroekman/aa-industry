# Standard Library
from datetime import timedelta
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Django
from django.core.cache import cache
from django.utils import timezone

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.models import (
    BuybackContract,
    CorporationSyncConfig,
    CorporationWebhookConfig,
    LedgerTransaction,
)
from industry_reforged.tasks.buyback import (
    buyback_poll_contracts,
    buyback_purge_stale_contracts,
)

from .factories import (
    BuybackContractFactory,
    BuybackContractItemFactory,
    BuybackProgramFactory,
    BuybackWatchlistItemFactory,
    EveCharacterFactory,
    EveTypeFactory,
    UserFactory,
)


def _esi_contract(**overrides):
    defaults = {
        "type": "item_exchange",
        "title": "BB-ABCD1234",
        "price": 1000.0,
        "start_location_id": None,
        "acceptor_id": None,
        "assignee_id": None,
        "issuer_id": None,
        "contract_id": 555,
        "status": "outstanding",
        "date_expired": None,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _esi_item(type_id, quantity):
    mock = MagicMock()
    mock.type_id = type_id
    mock.quantity = quantity
    return mock


@pytest.mark.django_db
class TestBuybackPollContracts:
    def setup_method(self):
        cache.clear()

    def _setup_program_with_token(self, facility=None):
        user = UserFactory()
        character = EveCharacterFactory()
        program = (
            BuybackProgramFactory(facilities=[facility])
            if facility
            else BuybackProgramFactory()
        )
        CorporationSyncConfig.objects.create(
            corporation=program.corporation, sync_character=character
        )
        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-contracts.read_corporation_contracts.v1")
        return program

    @patch("industry_reforged.tasks.buyback.esi")
    def test_happy_path_match(self, mock_esi):
        program = self._setup_program_with_token()
        eve_type = EveTypeFactory()
        contract = BuybackContractFactory(
            program=program, tracking_number="BB-ABCD1234", quoted_price=1000.0
        )
        BuybackContractItemFactory(contract=contract, eve_type=eve_type, quantity=10)

        mock_esi.client.Contracts.GetCorporationsCorporationIdContracts.return_value.results.return_value = [
            _esi_contract(
                title="BB-ABCD1234",
                price=1000.0,
                start_location_id=program.facilities.first().facility_id,
                acceptor_id=program.corporation.corporation_id,
            )
        ]
        mock_esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems.return_value.result.return_value = [
            _esi_item(eve_type.id, 10)
        ]

        buyback_poll_contracts()

        contract.refresh_from_db()
        assert contract.status == "MATCHED"
        assert contract.esi_contract_id == 555

    @patch("industry_reforged.tasks.buyback.esi")
    def test_mismatch_sets_correct_flag(self, mock_esi):
        program = self._setup_program_with_token()
        eve_type = EveTypeFactory()
        contract = BuybackContractFactory(
            program=program, tracking_number="BB-ABCD1234", quoted_price=1000.0
        )
        BuybackContractItemFactory(contract=contract, eve_type=eve_type, quantity=10)

        mock_esi.client.Contracts.GetCorporationsCorporationIdContracts.return_value.results.return_value = [
            _esi_contract(
                title="BB-ABCD1234",
                price=5000.0,  # wrong price
                start_location_id=program.facilities.first().facility_id,
                acceptor_id=program.corporation.corporation_id,
            )
        ]
        mock_esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems.return_value.result.return_value = [
            _esi_item(eve_type.id, 10)
        ]

        buyback_poll_contracts()

        contract.refresh_from_db()
        assert contract.status == "FLAGGED"
        assert contract.flag_price_mismatch is True
        assert contract.flag_item_mismatch is False

    @patch("industry_reforged.tasks.buyback.esi")
    def test_no_active_program_is_noop(self, mock_esi):
        buyback_poll_contracts()
        mock_esi.client.Contracts.GetCorporationsCorporationIdContracts.assert_not_called()

    @patch("industry_reforged.tasks.buyback.esi")
    def test_no_scoped_token_skips_without_raising(self, mock_esi):
        program = BuybackProgramFactory()
        character = EveCharacterFactory()
        CorporationSyncConfig.objects.create(
            corporation=program.corporation, sync_character=character
        )
        # No Token created at all.
        buyback_poll_contracts()
        mock_esi.client.Contracts.GetCorporationsCorporationIdContracts.assert_not_called()

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_rerun_on_unchanged_data_is_idempotent(self, mock_esi, mock_notify):
        program = self._setup_program_with_token()
        eve_type = EveTypeFactory()
        contract = BuybackContractFactory(
            program=program, tracking_number="BB-ABCD1234", quoted_price=1000.0
        )
        BuybackContractItemFactory(contract=contract, eve_type=eve_type, quantity=10)

        mock_esi.client.Contracts.GetCorporationsCorporationIdContracts.return_value.results.return_value = [
            _esi_contract(
                title="BB-ABCD1234",
                price=1000.0,
                start_location_id=program.facilities.first().facility_id,
                acceptor_id=program.corporation.corporation_id,
            )
        ]
        mock_esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems.return_value.result.return_value = [
            _esi_item(eve_type.id, 10)
        ]

        buyback_poll_contracts()
        cache.clear()  # simulate the lock having expired before the second run
        buyback_poll_contracts()

        assert (
            BuybackContract.objects.filter(tracking_number="BB-ABCD1234").count() == 1
        )
        assert (
            mock_notify.call_count == 1
        )  # only notified once, not on the second match


@pytest.mark.django_db
class TestBuybackPollFollowsInGameStatus:
    """Fase 0 (TASK-272): match once, then follow the in-game contract status."""

    def setup_method(self):
        cache.clear()

    def _setup(self, quantity=10, **contract_kwargs):
        program = TestBuybackPollContracts()._setup_program_with_token()
        eve_type = EveTypeFactory()
        contract = BuybackContractFactory(
            program=program,
            tracking_number="BB-ABCD1234",
            quoted_price=1000.0,
            **contract_kwargs,
        )
        item = BuybackContractItemFactory(
            contract=contract, eve_type=eve_type, quantity=quantity
        )
        return program, eve_type, contract, item

    def _esi(self, mock_esi, program, eve_type, quantity=10, **overrides):
        fields = {
            "title": "BB-ABCD1234",
            "price": 1000.0,
            "start_location_id": program.facilities.first().facility_id,
            "acceptor_id": program.corporation.corporation_id,
        }
        fields.update(overrides)
        contracts_call = mock_esi.client.Contracts.GetCorporationsCorporationIdContracts
        contracts_call.return_value.results.return_value = [_esi_contract(**fields)]
        items_call = (
            mock_esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems
        )
        items_call.return_value.result.return_value = [_esi_item(eve_type.id, quantity)]
        return items_call

    def _poll(self):
        cache.clear()
        buyback_poll_contracts()

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_items_are_only_fetched_on_first_match(self, mock_esi, _notify):
        program, eve_type, contract, _ = self._setup()
        items_call = self._esi(mock_esi, program, eve_type)

        self._poll()
        self._poll()

        assert items_call.call_count == 1

    @patch("industry_reforged.utils.discord.send_discord_webhook")
    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_flagged_webhook_is_sent_once(self, mock_esi, _notify, mock_webhook):
        program, eve_type, _, _ = self._setup()
        CorporationWebhookConfig.objects.create(
            corporation=program.corporation, buyback_webhook="https://example.invalid/h"
        )
        self._esi(mock_esi, program, eve_type, price=5000.0)

        self._poll()
        self._poll()
        self._poll()

        assert mock_webhook.call_count == 1

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_finished_in_game_marks_paid_once(self, mock_esi, mock_notify):
        program, eve_type, contract, _ = self._setup()
        self._esi(mock_esi, program, eve_type, status="finished")

        self._poll()
        self._poll()

        contract.refresh_from_db()
        assert contract.status == "PAID"
        payouts = LedgerTransaction.objects.filter(
            buyback_contract=contract, transaction_type="BUYBACK_PAYOUT"
        )
        assert payouts.count() == 1
        assert payouts.first().director is None
        messages = [
            c.args[1]() if callable(c.args[1]) else c.args[1]
            for c in mock_notify.call_args_list
        ]
        assert any("accepted and paid" in m for m in messages)

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_director_pay_then_finished_does_not_pay_twice(self, mock_esi, _notify):
        program, eve_type, contract, _ = self._setup()
        self._esi(mock_esi, program, eve_type)
        self._poll()
        contract.refresh_from_db()
        assert contract.mark_paid(director=UserFactory()) is True

        self._esi(mock_esi, program, eve_type, status="finished")
        self._poll()

        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 1

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_rejected_in_game(self, mock_esi, _notify):
        program, eve_type, contract, _ = self._setup()
        self._esi(mock_esi, program, eve_type, status="rejected")

        self._poll()

        contract.refresh_from_db()
        assert contract.status == "REJECTED"
        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 0

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_withdrawn_contract_can_be_replaced_by_a_corrected_one(
        self, mock_esi, _notify
    ):
        program, eve_type, contract, _ = self._setup()
        self._esi(mock_esi, program, eve_type, price=5000.0)  # wrong price
        self._poll()
        contract.refresh_from_db()
        assert contract.status == "FLAGGED"

        self._esi(mock_esi, program, eve_type, price=5000.0, status="deleted")
        self._poll()
        contract.refresh_from_db()
        assert contract.status == "PENDING"
        assert contract.esi_contract_id is None

        self._esi(mock_esi, program, eve_type, contract_id=556)  # corrected
        self._poll()
        contract.refresh_from_db()
        assert contract.status == "MATCHED"
        assert contract.esi_contract_id == 556

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_outstanding_past_in_game_expiry_expires(self, mock_esi, _notify):
        program, eve_type, contract, _ = self._setup()
        self._esi(
            mock_esi,
            program,
            eve_type,
            date_expired=timezone.now() - timedelta(hours=1),
        )

        self._poll()

        contract.refresh_from_db()
        assert contract.status == "EXPIRED"

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_watchlist_flag_item_flags_an_otherwise_clean_contract(
        self, mock_esi, _notify
    ):
        program, eve_type, contract, _ = self._setup()
        BuybackWatchlistItemFactory(
            program=program, eve_type=eve_type, blocks_submission=False, reason="audit"
        )
        self._esi(mock_esi, program, eve_type)

        self._poll()

        contract.refresh_from_db()
        assert contract.status == "FLAGGED"
        assert contract.flag_watchlist is True
        assert "audit" in contract.flag_notes

    @patch("industry_reforged.tasks.utils.notify_discord_user")
    @patch("industry_reforged.tasks.buyback.esi")
    def test_matching_items_are_marked_esi_verified(self, mock_esi, _notify):
        program, eve_type, contract, item = self._setup(quantity=10)
        self._esi(mock_esi, program, eve_type, quantity=10)

        self._poll()

        item.refresh_from_db()
        assert item.is_esi_verified is True


@pytest.mark.django_db
class TestBuybackPurgeStaleContracts:
    def test_expires_stale_pending_contract(self):
        program = BuybackProgramFactory(contract_expiry_days=7)
        contract = BuybackContractFactory(program=program, status="PENDING")
        BuybackContract.objects.filter(pk=contract.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        buyback_purge_stale_contracts()

        contract.refresh_from_db()
        assert contract.status == "EXPIRED"

    def test_leaves_recent_pending_contract_untouched(self):
        program = BuybackProgramFactory(contract_expiry_days=7)
        contract = BuybackContractFactory(program=program, status="PENDING")

        buyback_purge_stale_contracts()

        contract.refresh_from_db()
        assert contract.status == "PENDING"

    def test_leaves_matched_contract_untouched(self):
        program = BuybackProgramFactory(contract_expiry_days=7)
        contract = BuybackContractFactory(program=program, status="MATCHED")
        BuybackContract.objects.filter(pk=contract.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        buyback_purge_stale_contracts()

        contract.refresh_from_db()
        assert contract.status == "MATCHED"
