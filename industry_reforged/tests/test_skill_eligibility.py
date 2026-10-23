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
from industry_reforged.utils.slot_service import get_user_available_slots
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

    @patch("industry_reforged.utils.slot_service.get_character_skill_levels")
    def test_slot_count_scoped_to_item_excludes_unskilled_characters(self, mock_skills):
        """The generic account-wide slot total must not be confused with the number
        of slots actually usable for a specific skill-gated item (TASK-260 follow-up:
        user reported seeing 69 generic slots for an item only 1 toon can build)."""

        def skills_for(character_id):
            if character_id == self.main_character.character_id:
                return {self.skill_type.id: 5}
            return {}  # alt lacks the skill

        mock_skills.side_effect = skills_for

        cache.set(
            f"industry_reforged_char_slots_{self.main_character.character_id}",
            {"mfg_slots": 3, "reaction_slots": 1, "science_slots": 1},
            timeout=86400,
        )
        cache.set(
            f"industry_reforged_char_slots_{self.alt_character.character_id}",
            {"mfg_slots": 10, "reaction_slots": 1, "science_slots": 1},
            timeout=86400,
        )

        generic = get_user_available_slots(self.user, activity_id=1)
        assert generic["character_count"] == 2
        assert generic["mfg_total"] == 13

        scoped = get_user_available_slots(
            self.user, activity_id=1, item_type_id=self.item_type.id
        )
        assert scoped["character_count"] == 1
        assert scoped["mfg_total"] == 3

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


class TestSkillGatedBomRelease(TestCase):
    """TASK-261: when a parent task is skill-gated and unbuildable for the viewing
    user, its direct BOM children (already-persisted ProductionTask rows, created
    recursively at order acceptance) become independently visible/claimable, even
    though their bom_parent.is_claimable stays True (the static admin flag, unrelated
    to skills, is untouched by this feature)."""

    def _dashboard_request(self):
        req = self.rf.get("/industry/industrialist/")
        req.user = self.user
        req.session = MagicMock()
        req._messages = FallbackStorage(req)
        return req

    def _patches(self):
        return [
            patch(
                "django.contrib.staticfiles.storage.staticfiles_storage.url",
                side_effect=lambda name: f"/static/{name}",
            ),
            patch(
                "django.contrib.staticfiles.storage.staticfiles_storage.stored_name",
                side_effect=lambda name: name,
            ),
            patch(
                "sri.templatetags.sri.sri_integrity_static",
                side_effect=lambda path, algorithm_type=None: "sha256-dummy",
            ),
        ]

    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()

        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98765600,
            corporation_name="BOM Release Test Corp",
            corporation_ticker="BRTC",
        )
        self.main_character = EveCharacter.objects.create(
            character_id=92100001,
            character_name="BOM Main Toon",
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
            user=self.user, character=self.main_character, owner_hash="bommainhash"
        )

        self.activity = EveIndustryActivity.objects.get_or_create(
            id=1, defaults={"name": "Manufacturing", "description": "Manufacturing"}
        )[0]

        # Parent item: requires skill A (user lacks it).
        self.skill_a = EveTypeFactory(name="Capital Ship Construction")
        self.parent_blueprint = EveTypeFactory(name="Capital Component Blueprint")
        self.parent_item = EveTypeFactory(name="Capital Component")
        EveIndustryActivityProduct.objects.create(
            eve_type=self.parent_blueprint,
            activity=self.activity,
            product_eve_type=self.parent_item,
            quantity=1,
        )
        EveIndustryActivitySkill.objects.create(
            eve_type=self.parent_blueprint,
            activity=self.activity,
            skill_eve_type=self.skill_a,
            level=5,
        )

        # Child item: no skill requirement at all - plain sub-component.
        self.child_item = EveTypeFactory(name="Tritanium Bar")

        # Grandchild-gating child item: requires skill B (user also lacks it).
        self.skill_b = EveTypeFactory(name="Advanced Capital Ship Construction")
        self.gated_child_blueprint = EveTypeFactory(
            name="Gated Sub-Component Blueprint"
        )
        self.gated_child_item = EveTypeFactory(name="Gated Sub-Component")
        EveIndustryActivityProduct.objects.create(
            eve_type=self.gated_child_blueprint,
            activity=self.activity,
            product_eve_type=self.gated_child_item,
            quantity=1,
        )
        EveIndustryActivitySkill.objects.create(
            eve_type=self.gated_child_blueprint,
            activity=self.activity,
            skill_eve_type=self.skill_b,
            level=1,
        )

        # Plain, entirely unrelated item - no gate anywhere in its ancestry.
        self.plain_item = EveTypeFactory(name="Plain Module")

    def _prepare_post_request(self, url, post_data=None):
        req = self.rf.post(url, data=post_data or {})
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_buildable_child_released_when_parent_skill_gated(self, mock_skills):
        mock_skills.return_value = {}  # user has neither skill_a nor skill_b

        parent = ProductionTaskFactory(
            item_type=self.parent_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,
            builder_reward=Decimal("75000000.00"),
        )
        child = ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=10,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
            builder_reward=Decimal("1000000.00"),
        )

        for p in self._patches():
            p.start()
        try:
            resp = industrialist_dashboard(self._dashboard_request())
        finally:
            patch.stopall()

        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert "Tritanium Bar" in content
        assert "Released" in content

        eligible, _ = skill_service.check_user_eligibility(
            self.user, child.item_type_id, child.activity_id
        )
        assert eligible is True

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_cascading_double_gate_releases_grandchild(self, mock_skills):
        """Parent needs skill A (missing), child needs skill B (also missing) -
        child must render disabled too, and ITS child (no gate) must be released."""
        mock_skills.return_value = {}

        parent = ProductionTaskFactory(
            item_type=self.parent_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,
        )
        gated_child = ProductionTaskFactory(
            item_type=self.gated_child_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
        )
        grandchild = ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=gated_child,
        )

        for p in self._patches():
            p.start()
        try:
            resp = industrialist_dashboard(self._dashboard_request())
        finally:
            patch.stopall()

        content = resp.content.decode("utf-8")
        assert "Gated Sub-Component" in content  # released, but itself disabled
        assert "Tritanium Bar" in content  # released through the second gate

        parent_eligible, _ = skill_service.check_user_eligibility(
            self.user, parent.item_type_id, parent.activity_id
        )
        child_eligible, _ = skill_service.check_user_eligibility(
            self.user, gated_child.item_type_id, gated_child.activity_id
        )
        grandchild_eligible, _ = skill_service.check_user_eligibility(
            self.user, grandchild.item_type_id, grandchild.activity_id
        )
        assert parent_eligible is False
        assert child_eligible is False
        assert grandchild_eligible is True

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_child_of_non_gated_parent_not_released(self, mock_skills):
        """Regression guard: this feature must not leak visibility for ordinary,
        non-skill-gated parents - only the pre-existing static is_claimable flag
        should ever expose their children."""
        mock_skills.return_value = {}

        parent = ProductionTaskFactory(
            item_type=self.plain_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,  # default, directly claimable - no reason to release children
        )
        ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
        )

        for p in self._patches():
            p.start()
        try:
            resp = industrialist_dashboard(self._dashboard_request())
        finally:
            patch.stopall()

        content = resp.content.decode("utf-8")
        assert "Plain Module" in content
        assert "Tritanium Bar" not in content

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_static_is_claimable_false_still_releases_child_unchanged(
        self, mock_skills
    ):
        """The pre-existing static release mechanism (admin-flagged is_claimable=False)
        must keep working exactly as before, independent of skills."""
        mock_skills.return_value = {}

        parent = ProductionTaskFactory(
            item_type=self.plain_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=False,
        )
        ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
        )

        for p in self._patches():
            p.start()
        try:
            resp = industrialist_dashboard(self._dashboard_request())
        finally:
            patch.stopall()

        content = resp.content.decode("utf-8")
        assert "Tritanium Bar" in content

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_static_and_skill_gate_combined_no_duplicate_row(self, mock_skills):
        """A child whose parent is both statically is_claimable=False AND
        skill-gated for this user must appear exactly once, not twice."""
        mock_skills.return_value = {}

        parent = ProductionTaskFactory(
            item_type=self.parent_item,  # skill-gated
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=False,  # and statically locked
        )
        child = ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
        )

        for p in self._patches():
            p.start()
        try:
            resp = industrialist_dashboard(self._dashboard_request())
        finally:
            patch.stopall()

        content = resp.content.decode("utf-8")
        # The row itself (its <tr> open tag) must only be rendered once - the item
        # name legitimately repeats within a single row (alt text, data attributes).
        assert content.count(f'<tr data-task-id="{child.id}">') == 1

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_claim_released_child_end_to_end(self, mock_skills):
        mock_skills.return_value = {}  # lacks parent's skill entirely

        parent = ProductionTaskFactory(
            item_type=self.parent_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,
        )
        child = ProductionTaskFactory(
            item_type=self.child_item,  # no skill requirement of its own
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
            builder_reward=Decimal("1000000.00"),
        )

        req = self._prepare_post_request(f"/industry/industrialist/claim/{child.id}/")
        resp = claim_task(req, child.id)
        assert resp.status_code == 302

        child.refresh_from_db()
        parent.refresh_from_db()
        assert child.status == "IN_PRODUCTION"
        assert parent.status == "UNCLAIMED"

    @patch("industry_reforged.utils.skill_service.get_character_skill_levels")
    def test_claim_of_released_child_survives_later_parent_claim_by_skilled_user(
        self, mock_skills
    ):
        """Once an unskilled member has independently claimed a released child, a
        skilled corpmate fully claiming the parent afterward must not steal/reassign
        that already-claimed child (existing claim_recursive UNCLAIMED-only guard)."""
        skilled_character = EveCharacter.objects.create(
            character_id=92100002,
            character_name="Skilled Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        skilled_user = UserFactory()
        skilled_user.user_permissions.add(
            Permission.objects.get(codename="industrialist_access")
        )
        skilled_user = skilled_user.__class__.objects.get(pk=skilled_user.pk)
        skilled_user.profile.main_character = skilled_character
        skilled_user.profile.save()
        CharacterOwnership.objects.create(
            user=skilled_user, character=skilled_character, owner_hash="skilledhash"
        )

        def skills_for(character_id):
            if character_id == skilled_character.character_id:
                return {self.skill_a.id: 5}
            return {}

        mock_skills.side_effect = skills_for

        parent = ProductionTaskFactory(
            item_type=self.parent_item,
            activity_id=1,
            quantity=1,
            status="UNCLAIMED",
            is_claimable=True,
            builder_reward=Decimal("75000000.00"),
        )
        child = ProductionTaskFactory(
            item_type=self.child_item,
            activity_id=1,
            quantity=5,
            status="UNCLAIMED",
            is_claimable=True,
            bom_parent=parent,
            builder_reward=Decimal("1000000.00"),
        )

        # Unskilled user claims the released child first.
        req1 = self._prepare_post_request(f"/industry/industrialist/claim/{child.id}/")
        claim_task(req1, child.id)
        child.refresh_from_db()
        assert child.status == "IN_PRODUCTION"
        assert child.assigned_to == self.main_character

        # Skilled corpmate then claims the parent directly.
        req2 = self.rf.post(f"/industry/industrialist/claim/{parent.id}/")
        req2.user = skilled_user
        req2.session = "session"
        req2._messages = FallbackStorage(req2)
        claim_task(req2, parent.id)

        child.refresh_from_db()
        assert child.status == "IN_PRODUCTION"
        assert child.assigned_to == self.main_character  # untouched by the cascade
