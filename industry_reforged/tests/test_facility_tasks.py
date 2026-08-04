# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.tasks.facilities import update_industry_facilities
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestFacilityTasks:

    @patch("industry_reforged.tasks.facilities.esi")
    @patch("allianceauth.services.hooks.get_extension_logger")
    def test_update_industry_facilities(self, mock_logger, mock_esi):
        user = UserFactory()
        character = EveCharacterFactory()

        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-assets.read_corporation_assets.v1")

        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-corporations.read_structures.v1")

        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        ).scopes.create(name="esi-universe.read_structures.v1")

        mock_asset = MagicMock()
        mock_asset.location_type = "station"
        mock_asset.location_id = 60003760

        mock_esi.client.Assets.GetCorporationsCorporationIdAssets.return_value.results.return_value = [
            mock_asset
        ]

        mock_structure = MagicMock()
        mock_structure.structure_id = 1030000000000

        mock_esi.client.Corporation.GetCorporationsCorporationIdStructures.return_value.results.return_value = [
            mock_structure
        ]

        mock_station_info = MagicMock()
        mock_station_info.name = "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
        mock_station_info.type_id = 1531
        mock_station_info.system_id = 30000142

        mock_esi.client.Universe.GetUniverseStationsStationId.return_value.result.return_value = (
            mock_station_info
        )

        update_industry_facilities()
