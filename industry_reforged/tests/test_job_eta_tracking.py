"""
Unit tests for claimed-job ETA tracking, overview and overdue alerting (TASK-262).
"""

# Standard Library
import datetime
from decimal import Decimal
from unittest.mock import patch

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.models import Scope, Token

# AA Industry App
from industry_reforged.models import CorporationWebhookConfig, JobTrackingConfig
from industry_reforged.tasks.job_tracking import check_overdue_production_tasks
from industry_reforged.tests.factories import (
    CharacterIndustryJobFactory,
    EveTypeFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.utils import eta_service
from industry_reforged.views.industrialist import claim_task, unclaim_task


class TestEtaService(TestCase):
    def setUp(self):
        cache.clear()
        self.item_type = EveTypeFactory(name="Widget")

    def test_eta_unknown_when_not_assigned(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="UNCLAIMED",
            estimated_duration_seconds=3600,
        )
        assert eta_service.get_task_eta(task) is None

    def test_eta_unknown_when_duration_zero(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=timezone.now(),
            estimated_duration_seconds=0,
        )
        assert eta_service.get_task_eta(task) is None

    def test_eta_falls_back_to_estimate(self):
        now = timezone.now()
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=now,
            estimated_duration_seconds=7200,
        )
        eta = eta_service.get_task_eta(task)
        assert eta == now + datetime.timedelta(seconds=7200)

    def test_eta_prefers_linked_job_end_date(self):
        now = timezone.now()
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=now,
            estimated_duration_seconds=3600,  # would estimate now+1h
        )
        job = CharacterIndustryJobFactory(
            status="active",
            end_date=now + datetime.timedelta(hours=5),  # real ESI timer says 5h
        )
        # AA Industry App
        from industry_reforged.models import TaskJobLink

        TaskJobLink.objects.create(task=task, character_job=job)

        eta = eta_service.get_task_eta(task)
        assert eta == now + datetime.timedelta(hours=5)

    def test_eta_ignores_non_active_linked_job(self):
        now = timezone.now()
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=now,
            estimated_duration_seconds=3600,
        )
        job = CharacterIndustryJobFactory(
            status="delivered", end_date=now - datetime.timedelta(hours=1)
        )
        # AA Industry App
        from industry_reforged.models import TaskJobLink

        TaskJobLink.objects.create(task=task, character_job=job)

        # Falls back to the estimate since the only linked job isn't active/ready.
        eta = eta_service.get_task_eta(task)
        assert eta == now + datetime.timedelta(seconds=3600)

    def test_is_overdue_false_for_unknown_eta(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            estimated_duration_seconds=0,
        )
        assert eta_service.is_overdue(task, buffer_hours=2) is False

    def test_is_overdue_false_before_buffer_elapses(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=timezone.now() - datetime.timedelta(hours=1),
            estimated_duration_seconds=3600,  # due 1h ago, well within a 2h buffer
        )
        assert eta_service.is_overdue(task, buffer_hours=2) is False

    def test_is_overdue_true_past_buffer(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=timezone.now() - datetime.timedelta(hours=5),
            estimated_duration_seconds=3600,  # due 4h ago, past a 2h buffer
        )
        assert eta_service.is_overdue(task, buffer_hours=2) is True

    def test_is_overdue_respects_custom_buffer(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_at=timezone.now() - datetime.timedelta(hours=5),
            estimated_duration_seconds=3600,  # due 4h ago
        )
        assert eta_service.is_overdue(task, buffer_hours=10) is False

    def test_get_corp_buffer_hours_defaults_without_config(self):
        corp = EveCorporationInfo.objects.create(
            corporation_id=98700001, corporation_name="No Config Corp"
        )
        assert (
            eta_service.get_corp_buffer_hours(corp) == eta_service.DEFAULT_BUFFER_HOURS
        )

    def test_get_corp_buffer_hours_uses_configured_value(self):
        corp = EveCorporationInfo.objects.create(
            corporation_id=98700002, corporation_name="Configured Corp"
        )
        JobTrackingConfig.objects.create(corporation=corp, completion_buffer_hours=6)
        assert eta_service.get_corp_buffer_hours(corp) == 6


class TestOverdueAlertingTask(TestCase):
    def setUp(self):
        cache.clear()
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700010, corporation_name="Overdue Test Corp"
        )
        self.character = EveCharacter.objects.create(
            character_id=92200001,
            character_name="Overdue Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        JobTrackingConfig.objects.create(
            corporation=self.corp, completion_buffer_hours=2
        )
        self.item_type = EveTypeFactory(name="Overdue Widget")

    def _overdue_task(self, hours_overdue=5, estimated_hours=1):
        return ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_to=self.character,
            assigned_at=timezone.now()
            - datetime.timedelta(hours=hours_overdue + estimated_hours),
            estimated_duration_seconds=estimated_hours * 3600,
            quantity=5,
        )

    @patch("industry_reforged.tasks.job_tracking.send_discord_webhook")
    @patch("industry_reforged.tasks.job_tracking.send_pi_notification")
    def test_flags_overdue_task_and_notifies_claimant(self, mock_notify, mock_webhook):
        task = self._overdue_task()
        check_overdue_production_tasks()

        task.refresh_from_db()
        assert task.last_overdue_notified_at is not None
        assert mock_notify.called
        assert mock_notify.call_args[0][0] == self.character

    @patch("industry_reforged.tasks.job_tracking.send_discord_webhook")
    @patch("industry_reforged.tasks.job_tracking.send_pi_notification")
    def test_does_not_renotify_before_cooldown_elapses(self, mock_notify, mock_webhook):
        task = self._overdue_task()
        check_overdue_production_tasks()
        mock_notify.reset_mock()

        check_overdue_production_tasks()  # same run cycle, well within the 2h buffer
        task.refresh_from_db()
        assert not mock_notify.called

    @patch("industry_reforged.tasks.job_tracking.send_discord_webhook")
    @patch("industry_reforged.tasks.job_tracking.send_pi_notification")
    def test_renotifies_after_cooldown_elapses(self, mock_notify, mock_webhook):
        task = self._overdue_task()
        task.last_overdue_notified_at = timezone.now() - datetime.timedelta(hours=3)
        task.save(update_fields=["last_overdue_notified_at"])

        check_overdue_production_tasks()
        assert mock_notify.called

    @patch("industry_reforged.tasks.job_tracking.send_discord_webhook")
    @patch("industry_reforged.tasks.job_tracking.send_pi_notification")
    def test_one_batched_embed_per_corp_not_per_task(self, mock_notify, mock_webhook):
        CorporationWebhookConfig.objects.create(
            corporation=self.corp, directors_webhook="https://discord.example/webhook"
        )
        self._overdue_task()
        self._overdue_task()
        self._overdue_task()

        check_overdue_production_tasks()

        assert mock_webhook.call_count == 1
        embed = mock_webhook.call_args[0][1]
        assert "3 claimed job(s)" in embed["description"]

    @patch("industry_reforged.tasks.job_tracking.send_discord_webhook")
    @patch("industry_reforged.tasks.job_tracking.send_pi_notification")
    def test_not_yet_overdue_task_is_skipped(self, mock_notify, mock_webhook):
        ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_to=self.character,
            assigned_at=timezone.now() - datetime.timedelta(minutes=10),
            estimated_duration_seconds=3600,
        )
        check_overdue_production_tasks()
        assert not mock_notify.called


class TestResetOnReclaim(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700020, corporation_name="Reset Test Corp"
        )
        self.character = EveCharacter.objects.create(
            character_id=92200010,
            character_name="Reset Toon",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user = UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="industrialist_access")
        )
        self.user = self.user.__class__.objects.get(pk=self.user.pk)
        self.user.profile.main_character = self.character
        self.user.profile.save()
        CharacterOwnership.objects.create(
            user=self.user, character=self.character, owner_hash="resethash"
        )
        token = Token.objects.create(
            character_id=self.character.character_id,
            character_name=self.character.character_name,
            user=self.user,
            access_token="fake_token",
            refresh_token="fake_refresh",
        )
        scope, _ = Scope.objects.get_or_create(name="esi-skills.read_skills.v1")
        token.scopes.add(scope)
        self.item_type = EveTypeFactory(name="Reset Widget")

    def _prepare_post_request(self, url):
        req = self.rf.post(url)
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    def test_unclaim_resets_last_overdue_notified_at(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="IN_PRODUCTION",
            assigned_to=self.character,
            assigned_at=timezone.now() - datetime.timedelta(hours=10),
            estimated_duration_seconds=3600,
            last_overdue_notified_at=timezone.now(),
            builder_reward=Decimal("1000000.00"),
        )

        req = self._prepare_post_request(f"/industry/industrialist/unclaim/{task.id}/")
        unclaim_task(req, task.id)

        task.refresh_from_db()
        assert task.status == "UNCLAIMED"
        assert task.last_overdue_notified_at is None

    def test_reclaim_starts_fresh_after_reset(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            status="UNCLAIMED",
            quantity=1,
            builder_reward=Decimal("1000000.00"),
        )
        req = self._prepare_post_request(f"/industry/industrialist/claim/{task.id}/")
        claim_task(req, task.id)

        task.refresh_from_db()
        assert task.status == "IN_PRODUCTION"
        assert task.last_overdue_notified_at is None
