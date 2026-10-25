"""
Unit tests for ProductionTask Priority Controls and Multiplier Visualization (TASK-254).
"""

# Standard Library
from decimal import Decimal
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

# AA Industry App
from industry_reforged.models import CorpPricingConfig, MemberOrder, ProductionTask
from industry_reforged.tests.factories import (
    EveTypeFactory,
    UserFactory,
)
from industry_reforged.views.director import (
    bulk_set_task_priority,
    set_task_priority,
    spawn_restock_job,
)


@pytest.fixture
def rf():
    return RequestFactory()


class TestProductionTaskPriorityViews(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.user = UserFactory()
        # Add corp_access permission
        perm = Permission.objects.get(codename="corp_access")
        self.user.user_permissions.add(perm)
        self.user = self.user.__class__.objects.get(pk=self.user.pk)

        # Corp & Pricing Config
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98765432,
            corporation_name="Priority Test Corp",
            corporation_ticker="PTC",
        )
        self.character = EveCharacter.objects.create(
            character_id=91234567,
            character_name="Test Director",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user.profile.main_character = self.character
        self.user.profile.save()

        self.pricing_config = CorpPricingConfig.objects.create(
            corporation=self.corp,
            builder_base_fee=Decimal("1000000.00"),
            builder_hourly_rate=Decimal("1000000.00"),
            builder_reward_percent=0.0,
            builder_min_reward=Decimal("1000000.00"),
            builder_max_reward=Decimal("50000000.00"),
            builder_urgent_multiplier=1.5,
            builder_high_multiplier=1.25,
            builder_low_multiplier=0.8,
        )

        self.item_type = EveTypeFactory(id=624, name="Caracal")

        self.order = MemberOrder.objects.create(
            character=self.character,
            total_price=Decimal("10000000.00"),
            amount_paid=Decimal("0.00"),
            status="OPEN",
        )

        self.task = ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=1,
            activity_id=1,
            status="UNCLAIMED",
            origin="MEMBER_ORDER",
            created_from_order=self.order,
            priority="NORMAL",
            gamification_value=15000000.0,
            builder_reward=Decimal("2000000.00"),
            estimated_duration_seconds=3600,
        )

    def _prepare_request(self, post_data=None):
        request = self.rf.post("/", data=post_data or {})
        request.user = self.user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_set_task_priority_urgent(self, mock_details):
        # 3600 base duration -> 2700s TE (0.75h)
        # Base fee 1M + 0.75h * 1M = 1.75M ISK
        # Urgent multiplier 1.5x -> 1.75M * 1.5 = 2.625M ISK
        mock_details.return_value = (3600, 1)

        request = self._prepare_request({"priority": "URGENT"})
        response = set_task_priority(request, self.task.id)

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "URGENT")
        self.assertEqual(self.task.builder_reward, Decimal("2625000.00"))
        self.assertEqual(self.task.estimated_duration_seconds, 2700)

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_set_task_priority_high(self, mock_details):
        # Base fee 1M + 0.75h * 1M = 1.75M ISK
        # High multiplier 1.25x -> 1.75M * 1.25 = 2.1875M ISK
        mock_details.return_value = (3600, 1)

        request = self._prepare_request({"priority": "HIGH"})
        response = set_task_priority(request, self.task.id)

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "HIGH")
        self.assertEqual(self.task.builder_reward, Decimal("2187500.00"))

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_set_task_priority_low(self, mock_details):
        # Base fee 1M + 0.75h * 1M = 1.75M ISK
        # Low multiplier 0.8x -> 1.75M * 0.8 = 1.4M ISK
        mock_details.return_value = (3600, 1)

        request = self._prepare_request({"priority": "LOW"})
        response = set_task_priority(request, self.task.id)

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "LOW")
        self.assertEqual(self.task.builder_reward, Decimal("1400000.00"))

    def test_set_task_priority_invalid(self):
        original_reward = self.task.builder_reward
        request = self._prepare_request({"priority": "INVALID_PRIO"})
        response = set_task_priority(request, self.task.id)

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "NORMAL")
        self.assertEqual(self.task.builder_reward, original_reward)

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_bulk_set_task_priority(self, mock_details):
        mock_details.return_value = (3600, 1)
        task2 = ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=2,
            activity_id=1,
            status="UNCLAIMED",
            origin="MANUAL",
            priority="NORMAL",
            gamification_value=30000000.0,
            builder_reward=Decimal("2000000.00"),
            estimated_duration_seconds=3600,
        )

        request = self._prepare_request(
            {
                "task_ids": [str(self.task.id), str(task2.id)],
                "priority": "URGENT",
            }
        )
        response = bulk_set_task_priority(request)
        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        task2.refresh_from_db()
        self.assertEqual(self.task.priority, "URGENT")
        self.assertEqual(task2.priority, "URGENT")
        self.assertEqual(self.task.builder_reward, Decimal("2625000.00"))

    def test_bulk_set_task_priority_no_tasks(self):
        request = self._prepare_request({"task_ids": [], "priority": "URGENT"})
        response = bulk_set_task_priority(request)
        self.assertEqual(response.status_code, 302)

    def test_unclaimed_tasks_priority_sorting(self):
        # Create tasks with different priorities
        ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=1,
            activity_id=1,
            status="UNCLAIMED",
            origin="MANUAL",
            priority="URGENT",
            builder_reward=Decimal("1000000.00"),
        )
        ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=1,
            activity_id=1,
            status="UNCLAIMED",
            origin="MANUAL",
            priority="HIGH",
            builder_reward=Decimal("1000000.00"),
        )
        ProductionTask.objects.create(
            item_type=self.item_type,
            quantity=1,
            activity_id=1,
            status="UNCLAIMED",
            origin="MANUAL",
            priority="LOW",
            builder_reward=Decimal("1000000.00"),
        )

        # Django
        from django.db.models import Case, IntegerField, Value, When

        priority_order = Case(
            When(priority="URGENT", then=Value(1)),
            When(priority="HIGH", then=Value(2)),
            When(priority="NORMAL", then=Value(3)),
            When(priority="LOW", then=Value(4)),
            default=Value(3),
            output_field=IntegerField(),
        )

        tasks = list(
            ProductionTask.objects.filter(status="UNCLAIMED")
            .annotate(prio_rank=priority_order)
            .order_by("prio_rank", "id")
        )

        priorities = [t.priority for t in tasks]
        self.assertEqual(priorities[0], "URGENT")
        self.assertEqual(priorities[1], "HIGH")
        self.assertEqual(priorities[2], "NORMAL")
        self.assertEqual(priorities[3], "LOW")

    @patch("industry_reforged.utils.pricing_engine.get_prices_with_overrides")
    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_spawn_restock_job_with_priority(self, mock_details, mock_prices):
        mock_details.return_value = (3600, 1)
        mock_prices.return_value = {self.item_type.id: 10000000.0}

        request = self._prepare_request({"quantity": 1, "priority": "URGENT"})
        response = spawn_restock_job(request, self.item_type.id)
        self.assertEqual(response.status_code, 302)

        spawned = ProductionTask.objects.filter(
            origin="MANUAL", status="UNCLAIMED", item_type=self.item_type
        ).latest("id")
        self.assertEqual(spawned.priority, "URGENT")
        self.assertEqual(spawned.builder_reward, Decimal("2625000.00"))
