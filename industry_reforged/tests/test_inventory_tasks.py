# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.models import CorporationSyncConfig, IndustryFacility
from industry_reforged.tasks.inventory import task_sync_corp_inventory
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestInventoryTasks:
    @patch("industry_reforged.tasks.inventory.esi")
    @patch("industry_reforged.tasks.inventory.logger")
    @patch("industry_reforged.tasks.inventory.Token.objects.filter")
    def test_task_sync_corp_inventory_no_tokens(
        self, mock_filter, mock_logger, mock_esi
    ):
        mock_filter.return_value.first.return_value = None
        # Even without tokens, running this task tests the setup queries
        corp = EveCorporationInfoFactory(corporation_id=123)
        char = EveCharacterFactory(corporation_id=123)
        CorporationSyncConfig.objects.create(corporation=corp, sync_character=char)
        IndustryFacility.objects.create(
            facility_id=1, owner_id=corp.corporation_id, sync_inventory=True
        )

        task_sync_corp_inventory()

    @patch("industry_reforged.tasks.inventory.esi")
    @patch("industry_reforged.tasks.inventory.Token.objects.filter")
    def test_task_sync_corp_inventory_with_token(self, mock_filter, mock_esi):
        user = UserFactory()
        corp = EveCorporationInfoFactory(corporation_id=123)
        char = EveCharacterFactory(corporation_id=123)
        CorporationSyncConfig.objects.create(corporation=corp, sync_character=char)
        IndustryFacility.objects.create(
            facility_id=1, owner_id=corp.corporation_id, sync_inventory=True
        )

        token = Token.objects.create(
            character_id=char.character_id, user=user, access_token="test_token"
        )
        mock_filter.return_value.first.return_value = token

        # Mock ESI response
        mock_esi.client.Assets.GetCorporationsCorporationIdAssets.return_value.results.return_value = [
            MagicMock(
                location_id=1,
                type_id=10,
                quantity=100,
                item_id=1001,
                is_singleton=False,
            )
        ]

        task_sync_corp_inventory()
        assert mock_esi.client.Assets.GetCorporationsCorporationIdAssets.called
