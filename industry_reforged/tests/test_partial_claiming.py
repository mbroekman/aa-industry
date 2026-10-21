"""
Unit tests for Interactive Slot-Based Partial Claiming and Task Splitting (TASK-255).
"""

# Standard Library
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from esi.models import Scope, Token

# AA Industry App
from industry_reforged.models import (
    CharacterIndustryJob,
    CorpPricingConfig,
    ProductionTask,
)
from industry_reforged.tests.factories import (
    EveTypeFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.utils.slot_service import (
    SKILL_ADV_MASS_PRODUCTION,
    SKILL_ADV_MASS_REACTIONS,
    SKILL_MASS_PRODUCTION,
    SKILL_MASS_REACTIONS,
    get_character_industry_slots,
    get_user_available_slots,
)
from industry_reforged.views.industrialist import (
    claim_task,
    claim_task_preview,
)


class TestPartialClaimingAndSlots(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.user = UserFactory()
        perm = Permission.objects.get(codename="industrialist_access")
        self.user.user_permissions.add(perm)
        self.user = self.user.__class__.objects.get(pk=self.user.pk)

        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98765400,
            corporation_name="Slot Test Corp",
            corporation_ticker="STC",
        )
        self.character = EveCharacter.objects.create(
            character_id=91000001,
            character_name="Test Industrialist",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user.profile.main_character = self.character
        self.user.profile.save()

        CharacterOwnership.objects.create(
            user=self.user,
            character=self.character,
            owner_hash="testhash1",
        )

        # Create token with esi-skills scope
        self.token = Token.objects.create(
            character_id=self.character.character_id,
            character_name=self.character.character_name,
            user=self.user,
            access_token="fake_token",
            refresh_token="fake_refresh",
        )
        scope, _ = Scope.objects.get_or_create(name="esi-skills.read_skills.v1")
        self.token.scopes.add(scope)

        # Pricing config
        self.pricing_config = CorpPricingConfig.objects.create(
            corporation=self.corp,
            builder_base_fee=Decimal("1000000.00"),
            builder_hourly_rate=Decimal("750000.00"),
            builder_min_reward=Decimal("2500000.00"),
            builder_max_reward=Decimal("75000000.00"),
        )

        self.item_type = EveTypeFactory(id=2456, name="Capital Corporate Hangar Bay")

    def _prepare_post_request(self, url, post_data=None):
        req = self.rf.post(url, data=post_data or {})
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    @patch("industry_reforged.utils.slot_service.esi")
    def test_get_character_industry_slots_live_esi_and_caching(self, mock_esi):
        """Test skill parsing from live ESI skills and caching mechanism."""
        mock_skill_mp = MagicMock(skill_id=SKILL_MASS_PRODUCTION, active_skill_level=5)
        mock_skill_amp = MagicMock(
            skill_id=SKILL_ADV_MASS_PRODUCTION, active_skill_level=4
        )
        mock_skill_mr = MagicMock(skill_id=SKILL_MASS_REACTIONS, active_skill_level=4)
        mock_skill_amr = MagicMock(
            skill_id=SKILL_ADV_MASS_REACTIONS, active_skill_level=3
        )

        mock_res = MagicMock()
        mock_res.skills = [
            mock_skill_mp,
            mock_skill_amp,
            mock_skill_mr,
            mock_skill_amr,
        ]

        mock_esi.client.Skills.GetCharactersCharacterIdSkills.return_value.results.return_value = mock_res

        # First call: hits ESI
        slots = get_character_industry_slots(self.character.character_id)
        assert mock_esi.client.Skills.GetCharactersCharacterIdSkills.called
        # 1 base + 5 MP + 4 AMP = 10
        assert slots["mfg_slots"] == 10
        # 1 base + 4 MR + 3 AMR = 8
        assert slots["reaction_slots"] == 8

        # Second call: served from Django cache, no ESI call
        mock_esi.client.Skills.GetCharactersCharacterIdSkills.reset_mock()
        cached_slots = get_character_industry_slots(self.character.character_id)
        assert not mock_esi.client.Skills.GetCharactersCharacterIdSkills.called
        assert cached_slots["mfg_slots"] == 10

    def test_get_user_available_slots_subtracts_active_jobs(self):
        """Test that active CharacterIndustryJob records reduce available slots."""
        # Set cached slots for character: 10 mfg slots, 8 reaction slots
        cache.set(
            f"industry_reforged_char_slots_{self.character.character_id}",
            {"mfg_slots": 10, "reaction_slots": 8, "science_slots": 5},
            timeout=86400,
        )

        # Create 2 active manufacturing jobs and 1 ready manufacturing job
        CharacterIndustryJob.objects.create(
            job_id=2001,
            character=self.character,
            activity_id=1,
            status="active",
        )
        CharacterIndustryJob.objects.create(
            job_id=2002,
            character=self.character,
            activity_id=1,
            status="active",
        )
        CharacterIndustryJob.objects.create(
            job_id=2003,
            character=self.character,
            activity_id=1,
            status="ready",
        )
        # 1 delivered job (does not take slot)
        CharacterIndustryJob.objects.create(
            job_id=2004,
            character=self.character,
            activity_id=1,
            status="delivered",
        )

        res = get_user_available_slots(self.user, activity_id=1)
        assert res["total_slots"] == 10
        assert res["active_slots"] == 3  # 2 active + 1 ready
        assert res["available_slots"] == 7
        assert res["reaction_available"] == 8

    def test_claim_task_full_claim(self):
        """Claiming without claim_quantity claims the entire task."""
        task = ProductionTaskFactory(
            item_type=self.item_type,
            quantity=10,
            status="UNCLAIMED",
            builder_reward=Decimal("5000000.00"),
        )

        req = self._prepare_post_request(f"/industry/industrialist/claim/{task.id}/")
        resp = claim_task(req, task.id)
        assert resp.status_code == 302

        task.refresh_from_db()
        assert task.status == "IN_PRODUCTION"
        assert task.assigned_to == self.character
        assert task.quantity == 10

    @patch(
        "industry_reforged.utils.pricing_engine.get_item_production_details",
        return_value=(3600, 1),
    )
    def test_claim_task_partial_claim_splits_task(self, mock_details):
        """Partial claim creates a new IN_PRODUCTION task and leaves remaining UNCLAIMED."""
        task = ProductionTaskFactory(
            item_type=self.item_type,
            quantity=100,
            status="UNCLAIMED",
            priority="NORMAL",
            builder_reward=Decimal("50000000.00"),
            gamification_value=Decimal("10000000.00"),
            estimated_duration_seconds=360000,
        )

        req = self._prepare_post_request(
            f"/industry/industrialist/claim/{task.id}/",
            post_data={"claim_quantity": 30, "allocated_slots": 5},
        )
        resp = claim_task(req, task.id)
        assert resp.status_code == 302

        # Original task should remain UNCLAIMED with 70 quantity
        task.refresh_from_db()
        assert task.status == "UNCLAIMED"
        assert task.quantity == 70
        assert task.builder_reward > Decimal("0.00")
        assert task.gamification_value == Decimal("7000000.00")

        # New claimed task should be created with 30 quantity
        claimed = ProductionTask.objects.filter(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_to=self.character,
        ).first()

        assert claimed is not None
        assert claimed.quantity == 30
        assert claimed.allocated_slots == 5
        assert claimed.gamification_value == Decimal("3000000.00")
        assert claimed.builder_reward > Decimal("0.00")
        assert claimed.estimated_duration_seconds > 0

    def test_claim_task_preview_api(self):
        """Test claim_task_preview returns accurate real-time metrics."""
        task = ProductionTaskFactory(
            item_type=self.item_type,
            quantity=50,
            status="UNCLAIMED",
            builder_reward=Decimal("30000000.00"),
            gamification_value=Decimal("5000000.00"),
        )

        req = self.rf.get(
            "/industry/industrialist/claim-preview/",
            data={"task_id": task.id, "claim_quantity": 20, "allocated_slots": 4},
        )
        req.user = self.user
        resp = claim_task_preview(req)

        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert data["task_id"] == task.id
        assert data["claim_quantity"] == 20
        assert data["allocated_slots"] == 4
        assert data["rem_quantity"] == 30
        assert "reward_claimed_formatted" in data
        assert "wall_clock_formatted" in data
        assert data["runs_per_slot"] >= 1

    def test_claim_task_boundary_clamping(self):
        """Test boundary clamping for invalid claim quantities."""
        task = ProductionTaskFactory(
            item_type=self.item_type,
            quantity=10,
            status="UNCLAIMED",
        )

        # Quantity over max -> clamped to 10 (full claim)
        req = self._prepare_post_request(
            f"/industry/industrialist/claim/{task.id}/",
            post_data={"claim_quantity": 999, "allocated_slots": 2},
        )
        claim_task(req, task.id)

        task.refresh_from_db()
        assert task.status == "IN_PRODUCTION"
        assert task.quantity == 10
        assert task.allocated_slots == 2
