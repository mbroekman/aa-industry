"""
Unit tests for skill-gated job eligibility (TASK-260).

Covers: character with/without the required skill, user-level eligibility via an alt
when the main character lacks it, and the claim-time hard-stop blocking a claim even
when an alt on the account would qualify.
"""

# Standard Library
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
from eveuniverse.models import (
    EveIndustryActivity,
    EveIndustryActivityProduct,
    EveIndustryActivitySkill,
)

# AA Industry App
from industry_reforged.tests.factories import (
    EveTypeFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.utils import skill_service
from industry_reforged.views.industrialist import claim_task, industrialist_dashboard


class TestSkillEligibility(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()

        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98765500,
            corporation_name="Skill Test Corp",
            corporation_ticker="SKT",
        )

        self.main_character = EveCharacter.objects.create(
            character_id=92000001,
            character_name="Main Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.alt_character = EveCharacter.objects.create(
            character_id=92000002,
            character_name="Alt Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )

        self.user = UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="industrialist_access")
        )
        self.user = self.user.__class__.objects.get(pk=self.user.pk)
        self.user.profile.main_character = self.main_character
        self.user.profile.save()

        CharacterOwnership.objects.create(
            user=self.user, character=self.main_character, owner_hash="mainhash"
        )
        CharacterOwnership.objects.create(
            user=self.user, character=self.alt_character, owner_hash="althash"
        )

        # A fake "capital component" blueprint requiring Capital Ship Construction V.
        self.activity = EveIndustryActivity.objects.get_or_create(
            id=1, defaults={"name": "Manufacturing", "description": "Manufacturing"}
        )[0]
        self.skill_type = EveTypeFactory(name="Capital Ship Construction")
        self.blueprint_type = EveTypeFactory(name="Capital Component Blueprint")
        self.item_type = EveTypeFactory(name="Capital Component")

        EveIndustryActivityProduct.objects.create(
            eve_type=self.blueprint_type,
            activity=self.activity,
            product_eve_type=self.item_type,
            quantity=1,
        )
        EveIndustryActivitySkill.objects.create(
            eve_type=self.blueprint_type,
            activity=self.activity,
            skill_eve_type=self.skill_type,
            level=5,
        )

    def _prepare_post_request(self, url, post_data=None):
        req = self.rf.post(url, data=post_data or {})
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_character_without_skill_is_ineligible(self, mock_skills):
        mock_skills.return_value = {}
        eligible, missing = skill_service.check_character_eligibility(
            self.main_character.character_id, self.item_type.id, 1
        )
        assert eligible is False
        assert missing[0]["skill_name"] == "Capital Ship Construction"
        assert missing[0]["required_level"] == 5

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_character_with_skill_is_eligible(self, mock_skills):
        mock_skills.return_value = {self.skill_type.id: 5}
        eligible, missing = skill_service.check_character_eligibility(
            self.main_character.character_id, self.item_type.id, 1
        )
        assert eligible is True
        assert missing == []

    def test_item_with_no_requirements_is_always_eligible(self):
        plain_item = EveTypeFactory(name="T1 Frigate")
        eligible, missing = skill_service.check_character_eligibility(
            self.main_character.character_id, plain_item.id, 1
        )
        assert eligible is True
        assert missing == []

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_alt_in_different_corp_is_excluded_from_user_eligibility(self, mock_skills):
        """An alt with the skill but sitting in an unrelated corp has no access to
        this corp's hangars/facilities and must not make the job look buildable."""
        other_corp = EveCorporationInfo.objects.create(
            corporation_id=98765501,
            corporation_name="Unrelated Corp",
            corporation_ticker="UNRL",
        )
        self.alt_character.corporation_id = other_corp.corporation_id
        self.alt_character.corporation_name = other_corp.corporation_name
        self.alt_character.save()

        def skills_for(character_id):
            if character_id == self.alt_character.character_id:
                return {self.skill_type.id: 5}
            return {}

        mock_skills.side_effect = skills_for

        eligible, missing = skill_service.check_user_eligibility(
            self.user, self.item_type.id, 1
        )
        assert eligible is False
        assert missing[0]["skill_name"] == "Capital Ship Construction"

    def test_alt_in_different_corp_excluded_from_slot_count(self):
        other_corp = EveCorporationInfo.objects.create(
            corporation_id=98765502,
            corporation_name="Unrelated Corp 2",
            corporation_ticker="UNRL2",
        )
        self.alt_character.corporation_id = other_corp.corporation_id
        self.alt_character.corporation_name = other_corp.corporation_name
        self.alt_character.save()

        # AA Industry App
        from industry_reforged.utils.slot_service import get_user_available_slots

        cache.set(
            f"industry_reforged_char_slots_{self.main_character.character_id}",
            {"mfg_slots": 5, "reaction_slots": 3, "science_slots": 2},
            timeout=86400,
        )
        cache.set(
            f"industry_reforged_char_slots_{self.alt_character.character_id}",
            {"mfg_slots": 10, "reaction_slots": 8, "science_slots": 5},
            timeout=86400,
        )

        result = get_user_available_slots(self.user, activity_id=1)
        assert result["character_count"] == 1
        assert result["mfg_total"] == 5

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_user_eligible_via_alt_even_when_main_lacks_skill(self, mock_skills):
        def skills_for(character_id):
            if character_id == self.alt_character.character_id:
                return {self.skill_type.id: 5}
            return {}

        mock_skills.side_effect = skills_for

        eligible, missing = skill_service.check_user_eligibility(
            self.user, self.item_type.id, 1
        )
        assert eligible is True
        assert missing == []

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_claim_blocked_when_main_lacks_skill_despite_qualifying_alt(
        self, mock_skills
    ):
        """The Job Market filter is account-wide, but the claim hard-stop checks the
        specific (main) character the claim is attributed to."""

        def skills_for(character_id):
            if character_id == self.alt_character.character_id:
                return {self.skill_type.id: 5}
            return {}

        mock_skills.side_effect = skills_for

        task = ProductionTaskFactory(
            item_type=self.item_type,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            builder_reward=Decimal("75000000.00"),
        )

        req = self._prepare_post_request(f"/industry/industrialist/claim/{task.id}/")
        resp = claim_task(req, task.id)
        assert resp.status_code == 302

        task.refresh_from_db()
        assert task.status == "UNCLAIMED"

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_claim_succeeds_when_main_has_skill(self, mock_skills):
        mock_skills.return_value = {self.skill_type.id: 5}

        task = ProductionTaskFactory(
            item_type=self.item_type,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            builder_reward=Decimal("75000000.00"),
        )

        req = self._prepare_post_request(f"/industry/industrialist/claim/{task.id}/")
        resp = claim_task(req, task.id)
        assert resp.status_code == 302

        task.refresh_from_db()
        assert task.status == "IN_PRODUCTION"

    @patch(
        "django.contrib.staticfiles.storage.staticfiles_storage.url",
        side_effect=lambda name: f"/static/{name}",
    )
    @patch(
        "django.contrib.staticfiles.storage.staticfiles_storage.stored_name",
        side_effect=lambda name: name,
    )
    @patch(
        "sri.templatetags.sri.sri_integrity_static",
        side_effect=lambda path, algorithm_type=None: "sha256-dummy",
    )
    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_dashboard_marks_task_unbuildable_without_skill(
        self, mock_skills, mock_sri, mock_stored, mock_url
    ):
        mock_skills.return_value = {}

        ProductionTaskFactory(
            item_type=self.item_type,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            builder_reward=Decimal("75000000.00"),
        )

        req = self.rf.get("/industry/industrialist/")
        req.user = self.user
        req.session = MagicMock()
        req._messages = FallbackStorage(req)

        resp = industrialist_dashboard(req)
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert "Capital Ship Construction" in content
