# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

# AA Industry App
from industry_reforged.tasks.pi import update_character_pi
from industry_reforged.tests.factories import EveCharacterFactory, UserFactory


@pytest.mark.django_db
class TestPITasks:

    @patch("industry_reforged.tasks.pi.esi")
    @patch("eveuniverse.models.EvePlanet.objects.get_or_create_esi")
    @patch("eveuniverse.models.EveSolarSystem.objects.get_or_create_esi")
    @patch("industry_reforged.tasks.pi.ensure_eve_type")
    def test_update_character_pi_success(
        self, mock_ensure_type, mock_system, mock_planet, mock_esi
    ):
        user = UserFactory()
        character = EveCharacterFactory()
        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        )
        Token.objects.filter(character_id=character.character_id).first().scopes.create(
            name="esi-planets.manage_planets.v1"
        )

        mock_system.return_value = (MagicMock(id=30000142), False)
        mock_planet.return_value = (MagicMock(id=40000001), False)

        mock_planet_obj = MagicMock()
        mock_planet_obj.planet_id = 40000001
        mock_planet_obj.planet_type = "barren"
        mock_planet_obj.solar_system_id = 30000142
        mock_planet_obj.upgrade_level = 5
        mock_planet_obj.num_pins = 2

        mock_esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanets.return_value.result.return_value = [
            mock_planet_obj
        ]
        mock_esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanetsPlanetId.return_value.result.return_value = MagicMock(
            pins=[]
        )

        update_character_pi()

    @patch("industry_reforged.tasks.pi.esi")
    def test_update_character_pi_not_modified(self, mock_esi):
        user = UserFactory()
        character = EveCharacterFactory()
        Token.objects.create(
            character_id=character.character_id,
            user=user,
            character_name=character.character_name,
            character_owner_hash="dummy",
        )
        Token.objects.filter(character_id=character.character_id).first().scopes.create(
            name="esi-planets.manage_planets.v1"
        )

        mock_esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanets.side_effect = HTTPNotModified(
            None, None
        )

        update_character_pi()
