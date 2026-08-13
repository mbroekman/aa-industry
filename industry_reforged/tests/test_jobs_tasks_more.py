# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.models import CorporationSyncConfig
from industry_reforged.tasks.jobs import update_character_jobs, update_corporation_jobs
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestJobsTasks:
    @patch("industry_reforged.tasks.jobs.esi")
    @patch("industry_reforged.tasks.jobs.Token.objects.filter")
    @patch("industry_reforged.tasks.jobs.ensure_eve_type")
    @patch("industry_reforged.tasks.jobs.CharacterIndustryJob.objects.update_or_create")
    def test_update_character_jobs(
        self, mock_update, mock_ensure_eve_type, mock_filter, mock_esi
    ):
        mock_update.return_value = (MagicMock(), True)
        user = UserFactory()
        char = EveCharacterFactory()
        token = Token.objects.create(
            character_id=char.character_id, user=user, access_token="test_token"
        )
        mock_filter.return_value = [token]
        # For update_character_jobs, it iterates over tokens, so list is fine, but if it uses first we must mock it.
        # Actually update_character_jobs iterates: `for token in tokens:`
        # Wait, if it iterates, then `mock_filter.return_value = [token]` works!
        # Let's leave it as is.
        mock_esi.client.Industry.GetCharactersCharacterIdIndustryJobs.return_value.results.return_value = [
            MagicMock(
                job_id=1,
                activity_id=1,
                blueprint_type_id=2,
                product_type_id=3,
                status="active",
                duration=100,
            )
        ]

        # Test character jobs
        update_character_jobs()
        assert mock_esi.client.Industry.GetCharactersCharacterIdIndustryJobs.called

    @patch("industry_reforged.tasks.jobs.esi")
    @patch("industry_reforged.tasks.jobs.Token.objects.filter")
    @patch("industry_reforged.tasks.jobs.ensure_eve_type")
    @patch(
        "industry_reforged.tasks.jobs.CorporationIndustryJob.objects.update_or_create"
    )
    def test_update_corporation_jobs(
        self, mock_update, mock_ensure_eve_type, mock_filter, mock_esi
    ):
        mock_update.return_value = (MagicMock(status="active"), True)
        user = UserFactory()
        corp = EveCorporationInfoFactory(corporation_id=123)
        char = EveCharacterFactory(corporation_id=123)
        CorporationSyncConfig.objects.create(corporation=corp, sync_character=char)
        token = Token.objects.create(
            character_id=char.character_id, user=user, access_token="test_token"
        )
        mock_filter.return_value.first.return_value = token
        mock_esi.client.Industry.GetCorporationsCorporationIdIndustryJobs.return_value.results.return_value = [
            MagicMock(
                job_id=2,
                activity_id=1,
                blueprint_type_id=2,
                product_type_id=3,
                installer_id=char.character_id,
                status="active",
                duration=100,
            )
        ]

        update_corporation_jobs()
        assert mock_esi.client.Industry.GetCorporationsCorporationIdIndustryJobs.called
