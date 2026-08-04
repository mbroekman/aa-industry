# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Alliance Auth
from esi.models import Token

# AA Industry App
from industry_reforged.models import CharacterIndustryJob
from industry_reforged.tasks.jobs import update_character_jobs

from .factories import EveCharacterFactory, EveTypeFactory


@pytest.mark.django_db
class TestJobsTasks:
    @patch("industry_reforged.tasks.jobs.esi")
    @patch("industry_reforged.tasks.jobs.Token.objects.filter")
    @patch("industry_reforged.tasks.jobs.ensure_eve_type")
    def test_update_character_jobs(self, mock_ensure_type, mock_token_filter, mock_esi):
        # Create a character
        character = EveCharacterFactory(character_id=999)

        # Create EveTypes for the job
        EveTypeFactory(id=101)
        EveTypeFactory(id=102)

        # Mock token
        mock_token = MagicMock(spec=Token)
        mock_token.character_id = character.character_id
        mock_token_filter.return_value = [mock_token]

        # Mock ESI Response
        mock_job = MagicMock()
        mock_job.job_id = 12345
        mock_job.activity_id = 1
        mock_job.blueprint_type_id = 101
        mock_job.product_type_id = 102
        mock_job.status = "active"
        mock_job.start_date = None
        mock_job.end_date = None
        mock_job.runs = 1
        mock_job.probability = 1.0
        mock_job.successful_runs = 0
        mock_job.cost = 1000.0
        mock_job.facility_id = 111
        mock_job.station_id = 222
        mock_job.location_id = 333

        # Setup the chained method calls for swagger bravado client
        mock_endpoint = mock_esi.client.Industry.GetCharactersCharacterIdIndustryJobs
        mock_endpoint.return_value.results.return_value = [mock_job]

        # Run the task
        update_character_jobs()

        # Verify DB updates
        assert CharacterIndustryJob.objects.count() == 1
        saved_job = CharacterIndustryJob.objects.first()
        assert saved_job.job_id == 12345
        assert saved_job.status == "active"
        assert saved_job.cost == 1000.0
        assert mock_ensure_type.call_count == 2
