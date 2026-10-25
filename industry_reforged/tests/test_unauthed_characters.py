"""
Unit tests for blocking claims and warning members whose characters are missing the
esi-skills.read_skills.v1 scope - without it, skill_service/slot_service silently treat
that character as 0 skills / base 1-slot, giving members and directors a wrong picture.
"""

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.models import Scope, Token

# AA Industry App
from industry_reforged.models import ProductionTask
from industry_reforged.tests.factories import EveTypeFactory, UserFactory
from industry_reforged.utils import skill_service
from industry_reforged.views.industrialist import bulk_claim_tasks, claim_task


class TestGetUnauthedCharacters(TestCase):
    def setUp(self):
        cache.clear()
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700010,
            corporation_name="Unauthed Test Corp",
            corporation_ticker="UTC",
        )
        self.other_corp = EveCorporationInfo.objects.create(
            corporation_id=98700011,
            corporation_name="Other Corp",
            corporation_ticker="OTC",
        )
        self.user = UserFactory()
        self.main = EveCharacter.objects.create(
            character_id=91100001,
            character_name="Main Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user.profile.main_character = self.main
        self.user.profile.save()
        CharacterOwnership.objects.create(
            user=self.user, character=self.main, owner_hash="mainhash"
        )

    def _add_token(self, character, with_skills_scope):
        token = Token.objects.create(
            character_id=character.character_id,
            character_name=character.character_name,
            user=self.user,
            access_token="fake_token",
            refresh_token="fake_refresh",
        )
        if with_skills_scope:
            scope, _ = Scope.objects.get_or_create(name="esi-skills.read_skills.v1")
            token.scopes.add(scope)
        return token

    def test_character_without_skills_scope_is_flagged(self):
        self._add_token(self.main, with_skills_scope=False)

        unauthed = skill_service.get_unauthed_characters(self.user)

        assert unauthed == [self.main]

    def test_fully_authed_user_returns_empty(self):
        self._add_token(self.main, with_skills_scope=True)

        unauthed = skill_service.get_unauthed_characters(self.user)

        assert unauthed == []

    def test_alt_in_different_corp_is_ignored(self):
        alt = EveCharacter.objects.create(
            character_id=91100002,
            character_name="Unrelated Alt",
            corporation_id=self.other_corp.corporation_id,
            corporation_name=self.other_corp.corporation_name,
        )
        CharacterOwnership.objects.create(
            user=self.user, character=alt, owner_hash="althash"
        )
        self._add_token(self.main, with_skills_scope=True)
        # Alt has no token at all - but it's in a different corp, so it must not count.

        unauthed = skill_service.get_unauthed_characters(self.user)

        assert unauthed == []

    def test_multiple_unauthed_alts_all_reported(self):
        alt = EveCharacter.objects.create(
            character_id=91100003,
            character_name="Same Corp Alt",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        CharacterOwnership.objects.create(
            user=self.user, character=alt, owner_hash="althash2"
        )
        # Neither character has any token at all.

        unauthed = skill_service.get_unauthed_characters(self.user)

        assert set(unauthed) == {self.main, alt}


class TestClaimBlockedWhenUnauthed(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700012,
            corporation_name="Claim Block Corp",
            corporation_ticker="CBC",
        )
        self.user = UserFactory()
        perm = Permission.objects.get(codename="industrialist_access")
        self.user.user_permissions.add(perm)
        self.user = self.user.__class__.objects.get(pk=self.user.pk)

        self.character = EveCharacter.objects.create(
            character_id=91200001,
            character_name="Claimer Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user.profile.main_character = self.character
        self.user.profile.save()
        CharacterOwnership.objects.create(
            user=self.user, character=self.character, owner_hash="claimerhash"
        )

        self.item_type = EveTypeFactory(name="Rifter")
        self.task = ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=1,
            activity_id=1,
            status="UNCLAIMED",
        )

    def _authed_token(self):
        token = Token.objects.create(
            character_id=self.character.character_id,
            character_name=self.character.character_name,
            user=self.user,
            access_token="fake_token",
            refresh_token="fake_refresh",
        )
        scope, _ = Scope.objects.get_or_create(name="esi-skills.read_skills.v1")
        token.scopes.add(scope)

    def _post(self, url, data=None):
        req = self.rf.post(url, data=data or {})
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    def test_claim_task_blocked_when_main_character_unauthed(self):
        # No esi-skills token at all for self.character.
        req = self._post(f"/industry/industrialist/claim/{self.task.id}/")

        resp = claim_task(req, self.task.id)

        assert resp.status_code == 302
        self.task.refresh_from_db()
        assert self.task.status == "UNCLAIMED"

    def test_claim_task_succeeds_when_authed(self):
        self._authed_token()
        req = self._post(f"/industry/industrialist/claim/{self.task.id}/")

        resp = claim_task(req, self.task.id)

        assert resp.status_code == 302
        self.task.refresh_from_db()
        assert self.task.status == "IN_PRODUCTION"

    def test_bulk_claim_blocked_when_unauthed(self):
        req = self._post(
            "/industry/industrialist/bulk-claim/", {"task_ids": [self.task.id]}
        )

        resp = bulk_claim_tasks(req)

        assert resp.status_code == 302
        self.task.refresh_from_db()
        assert self.task.status == "UNCLAIMED"

    def test_bulk_claim_succeeds_when_authed(self):
        self._authed_token()
        req = self._post(
            "/industry/industrialist/bulk-claim/", {"task_ids": [self.task.id]}
        )

        resp = bulk_claim_tasks(req)

        assert resp.status_code == 302
        self.task.refresh_from_db()
        assert self.task.status == "IN_PRODUCTION"
