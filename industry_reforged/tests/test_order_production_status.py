"""Order status follows its work (TASK-284) and the Orders tab filter/badges."""

# Standard Library
import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

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
from industry_reforged.models import MemberOrder
from industry_reforged.tests.factories import (
    EveTypeFactory,
    MemberOrderFactory,
    OrderItemFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.utils.order_status import sync_order_production_status
from industry_reforged.views.datatables import dt_director_orders, dt_director_tasks
from industry_reforged.views.director import director_dashboard
from industry_reforged.views.industrialist import (
    bulk_unclaim_tasks,
    claim_task,
    complete_task,
    unclaim_task,
)


class TestSyncOrderProductionStatus(TestCase):
    def test_accepted_without_work_stays_accepted(self):
        order = MemberOrderFactory(status="ACCEPTED")
        ProductionTaskFactory(created_from_order=order, status="UNCLAIMED")
        assert sync_order_production_status(order) is False
        order.refresh_from_db()
        assert order.status == "ACCEPTED"

    def test_claimed_task_moves_order_and_sub_orders_to_in_production(self):
        root = MemberOrderFactory(status="ACCEPTED")
        child = MemberOrderFactory(status="ACCEPTED", parent_order=root)
        ProductionTaskFactory(created_from_order=child, status="IN_PRODUCTION")

        assert sync_order_production_status(child) is True
        root.refresh_from_db()
        child.refresh_from_db()
        assert root.status == "IN_PRODUCTION"
        assert child.status == "IN_PRODUCTION"

    def test_bought_item_counts_as_started(self):
        order = MemberOrderFactory(status="ACCEPTED")
        OrderItemFactory(order=order, is_bought=True)
        sync_order_production_status(order)
        order.refresh_from_db()
        assert order.status == "IN_PRODUCTION"

    def test_released_work_moves_back_to_accepted(self):
        order = MemberOrderFactory(status="IN_PRODUCTION")
        ProductionTaskFactory(created_from_order=order, status="UNCLAIMED")
        sync_order_production_status(order)
        order.refresh_from_db()
        assert order.status == "ACCEPTED"

    def test_other_statuses_are_left_alone(self):
        for status in ("QUOTED", "READY", "DELIVERED", "REJECTED"):
            order = MemberOrderFactory(status=status)
            ProductionTaskFactory(created_from_order=order, status="IN_PRODUCTION")
            assert sync_order_production_status(order) is False
            order.refresh_from_db()
            assert order.status == status

    def test_none_is_ignored(self):
        assert sync_order_production_status(None) is False


class TestClaimFlowUpdatesOrder(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(codename="industrialist_access")
        )
        self.user = user.__class__.objects.get(pk=user.pk)
        corp = EveCorporationInfo.objects.create(
            corporation_id=98765401,
            corporation_name="Order Status Corp",
            corporation_ticker="OSC",
        )
        self.character = EveCharacter.objects.create(
            character_id=91000011,
            character_name="Order Status Builder",
            corporation_id=corp.corporation_id,
            corporation_name=corp.corporation_name,
        )
        self.user.profile.main_character = self.character
        self.user.profile.save()
        CharacterOwnership.objects.create(
            user=self.user, character=self.character, owner_hash="oshash1"
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

        self.order = MemberOrderFactory(status="ACCEPTED", character=self.character)
        self.item_type = EveTypeFactory(id=2457, name="Status Test Item")

    def _post(self, data=None):
        req = self.rf.post("/", data=data or {})
        req.user = self.user
        req.session = "session"
        req._messages = FallbackStorage(req)
        return req

    def _status(self):
        self.order.refresh_from_db()
        return self.order.status

    def test_claim_then_unclaim(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            created_from_order=self.order,
            status="UNCLAIMED",
            builder_reward=Decimal("1000000.00"),
        )
        claim_task(self._post(), task.id)
        assert self._status() == "IN_PRODUCTION"

        unclaim_task(self._post(), task.id)
        assert self._status() == "ACCEPTED"

    def test_bulk_unclaim_moves_back(self):
        task = ProductionTaskFactory(
            item_type=self.item_type,
            created_from_order=self.order,
            status="IN_PRODUCTION",
            assigned_to=self.character,
        )
        MemberOrder.objects.filter(pk=self.order.pk).update(status="IN_PRODUCTION")
        bulk_unclaim_tasks(self._post({"task_ids": [task.id]}))
        assert self._status() == "ACCEPTED"

    def test_completing_one_of_two_tasks_keeps_in_production(self):
        done = ProductionTaskFactory(
            item_type=self.item_type,
            created_from_order=self.order,
            status="IN_PRODUCTION",
            assigned_to=self.character,
        )
        ProductionTaskFactory(
            item_type=self.item_type, created_from_order=self.order, status="UNCLAIMED"
        )
        complete_task(self._post(), done.id)
        assert self._status() == "IN_PRODUCTION"


class TestOrdersTabFilterAndBadges(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        user = UserFactory()
        user.user_permissions.add(Permission.objects.get(codename="corp_access"))
        self.user = user.__class__.objects.get(pk=user.pk)

        self.requested = MemberOrderFactory(status="REQUESTED")
        self.quoted = MemberOrderFactory(status="QUOTED")
        self.in_prod = MemberOrderFactory(status="IN_PRODUCTION", is_paid=False)
        self.ready_paid = MemberOrderFactory(status="READY", is_paid=True)
        self.delivered_unpaid = MemberOrderFactory(status="DELIVERED", is_paid=False)
        MemberOrderFactory(status="REJECTED")

    def _ids(self, query=""):
        req = self.rf.get("/" + query)
        req.user = self.user
        data = json.loads(dt_director_orders(req).content)
        return {int(row[0].split()[0].lstrip("#")) for row in data["data"]}

    def test_default_filter_is_in_production(self):
        assert self._ids() == {self.in_prod.id}

    def test_all_shows_everything(self):
        assert len(self._ids("?status=ALL")) == 6

    def test_unpaid_only_counts_ready_or_delivered(self):
        # An unpaid order still in production owes nothing yet.
        assert self._ids("?status=UNPAID") == {self.delivered_unpaid.id}

    @patch("industry_reforged.views.director.render")
    def test_dashboard_badge_counts_and_default_filter(self, mock_render):
        req = self.rf.get("/")
        req.user = self.user
        director_dashboard(req)
        context = mock_render.call_args[0][2]
        assert context["order_attention"] == {
            "new": 1,
            "quoted": 1,
            "in_production": 1,
            "unpaid": 1,
        }
        assert [b["filter"] for b in context["order_badges"]] == [
            "REQUESTED",
            "QUOTED",
            "IN_PRODUCTION",
            "UNPAID",
        ]
        assert context["order_status_filter"] == "IN_PRODUCTION"
        assert context["task_status_filter"] == "IN_PRODUCTION"
        assert [b["filter"] for b in context["task_badges"]] == [
            "UNCLAIMED",
            "IN_PRODUCTION",
            "COMPLETED",
        ]

    def test_template_tab_name_and_badges(self):
        source = (
            Path(__file__).resolve().parent.parent
            / "templates/industry_reforged/director_dashboard.html"
        ).read_text(encoding="utf-8")
        assert "Active Member Orders" not in source
        # Badges sit in the filter bar, not in the tab button.
        tab = source.split('id="orders-tab"')[1].split("</button>")[0]
        assert "filter-badge" not in tab
        assert "badges=order_badges" in source
        assert "badges=task_badges" in source


class TestProductionTasksFilter(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        user = UserFactory()
        user.user_permissions.add(Permission.objects.get(codename="corp_access"))
        self.user = user.__class__.objects.get(pk=user.pk)
        self.unclaimed = ProductionTaskFactory(status="UNCLAIMED")
        self.in_prod = ProductionTaskFactory(status="IN_PRODUCTION")
        self.done = ProductionTaskFactory(status="COMPLETED")

    def _count(self, query=""):
        req = self.rf.get("/?type=all" + query)
        req.user = self.user
        return json.loads(dt_director_tasks(req).content)["recordsTotal"]

    def test_default_is_in_production(self):
        assert self._count() == 1

    def test_all_and_specific_status(self):
        assert self._count("&task_status=ALL") == 3
        assert self._count("&task_status=COMPLETED") == 1
