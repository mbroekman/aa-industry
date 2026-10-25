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
from industry_reforged.models import BuybackContract, CorporationSyncConfig
from industry_reforged.tasks.buyback import (
    buyback_poll_contracts,
    buyback_purge_stale_contracts,
)

from .factories import (
    BuybackContractFactory,
    BuybackContractItemFactory,
    BuybackProgramFactory,
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
            BuybackProgramFactory(facility=facility)
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
                start_location_id=program.facility_id,
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
                start_location_id=program.facility_id,
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

    @patch("industry_reforged.tasks.buyback.notify_discord_user")
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
                start_location_id=program.facility_id,
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
