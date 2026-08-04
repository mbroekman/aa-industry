# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.models import CorporationSyncConfig
from industry_reforged.tasks.wallets import task_sync_corp_wallets
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestWalletTasks:

    @patch("industry_reforged.tasks.wallets.esi")
    def test_task_sync_corp_wallets_success(self, mock_esi):
        user = UserFactory()
        character = EveCharacterFactory()
        corp = EveCorporationInfoFactory()
        CorporationSyncConfig.objects.create(corporation=corp, sync_character=character)

        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-wallet.read_corporation_wallets.v1")

        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-corporations.read_divisions.v1")

        mock_div_obj = MagicMock()
        mock_div_obj.division = 1
        mock_div_obj.name = "Master Wallet"

        mock_div_obj2 = MagicMock()
        mock_div_obj2.division = 2
        mock_div_obj2.name = "Secondary Wallet"

        mock_divisions = MagicMock()
        mock_divisions.wallet = [mock_div_obj, mock_div_obj2]

        mock_esi.client.Corporation.GetCorporationsCorporationIdDivisions.return_value.result.return_value = (
            mock_divisions
        )

        mock_wallet_obj = MagicMock()
        mock_wallet_obj.division = 1
        mock_wallet_obj.balance = 5000000.0

        mock_wallet_obj2 = MagicMock()
        mock_wallet_obj2.division = 2
        mock_wallet_obj2.balance = 1000000.0

        mock_esi.client.Wallet.GetCorporationsCorporationIdWallets.return_value.result.return_value = [
            mock_wallet_obj,
            mock_wallet_obj2,
        ]
        mock_esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal.return_value.result.return_value = (
            []
        )

        task_sync_corp_wallets()

    @patch("industry_reforged.tasks.wallets.esi")
    def test_task_sync_corp_wallets_no_token(self, mock_esi):
        UserFactory()
        character = EveCharacterFactory()
        corp = EveCorporationInfoFactory()
        CorporationSyncConfig.objects.create(corporation=corp, sync_character=character)
        task_sync_corp_wallets()
