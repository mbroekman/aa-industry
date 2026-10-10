"""Tests for OrderItem bought tracking and MemberOrder progress integration."""

# Standard Library
from decimal import Decimal
from unittest.mock import patch
import json

# Third Party
import pytest

# Django
from django.contrib.auth.models import AnonymousUser, Permission
from django.test import RequestFactory
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# Eve Models
from eveuniverse.models import EveIndustryActivityProduct

# AA Industry App
from industry_reforged.models import CorpItemConfig, OrderItem
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
    MemberOrderFactory,
    OrderItemFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.views.orders.management import toggle_order_item_bought


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestOrderItemBought:
    def test_default_values(self):
        item = OrderItemFactory()
        assert item.is_bought is False
        assert item.bought_at is None
        assert item.bought_by is None

    def test_is_buy_product_property(self):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()

        item = OrderItemFactory(order=order)

        # 1. No blueprint exists in eveuniverse -> should be a buy product
        with patch("eveuniverse.models.EveIndustryActivityProduct.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            assert item.is_buy_product is True

        # 2. Has blueprint, no CorpItemConfig -> not a buy product
        with patch("eveuniverse.models.EveIndustryActivityProduct.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            assert item.is_buy_product is False

            # 3. Has blueprint, but CorpItemConfig is BUY -> is a buy product
            config = CorpItemConfig.objects.create(
                corporation=corp,
                item_type=item.item_type,
                build_or_buy="BUY",
            )
            assert item.is_buy_product is True

            # 4. Has blueprint, CorpItemConfig is BUILD -> not a buy product
            config.build_or_buy = "BUILD"
            config.save()
            assert item.is_buy_product is False

    def test_member_order_progress_percent_with_buy_items(self):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()

        # Order with no tasks and no items
        assert order.progress_percent == 0
        assert order.has_work_items is False

        # Add 2 buy items
        item1 = OrderItemFactory(order=order)
        item2 = OrderItemFactory(order=order)
        CorpItemConfig.objects.create(
            corporation=corp, item_type=item1.item_type, build_or_buy="BUY"
        )
        CorpItemConfig.objects.create(
            corporation=corp, item_type=item2.item_type, build_or_buy="BUY"
        )

        assert order.has_work_items is True
        assert order.progress_percent == 0

        # Mark 1 item as bought
        item1.is_bought = True
        item1.save()
        assert order.progress_percent == 50

        # Mark 2nd item as bought
        item2.is_bought = True
        item2.save()
        assert order.progress_percent == 100

        # Now add a ProductionTask (1 completed, 1 pending)
        t1 = ProductionTaskFactory(created_from_order=order, status="COMPLETED")
        t2 = ProductionTaskFactory(created_from_order=order, status="PENDING")

        # Total work items = 2 buy items + 2 tasks = 4
        # Completed work items = 2 bought + 1 completed = 3
        # 3/4 = 75%
        assert order.progress_percent == 75

    def test_toggle_bought_unauthenticated(self, rf):
        item = OrderItemFactory()
        request = rf.post(f"/orders/items/{item.id}/toggle-bought/")
        request.user = AnonymousUser()

        response = toggle_order_item_bought(request, item.id)
        assert response.status_code == 403

    def test_toggle_bought_get_method_not_allowed(self, rf):
        item = OrderItemFactory()
        user = UserFactory()
        request = rf.get(f"/orders/items/{item.id}/toggle-bought/")
        request.user = user

        response = toggle_order_item_bought(request, item.id)
        assert response.status_code == 405

    def test_toggle_bought_permission_denied_for_non_owner_non_privileged(self, rf):
        item = OrderItemFactory()
        other_user = UserFactory()
        request = rf.post(f"/orders/items/{item.id}/toggle-bought/")
        request.user = other_user

        with patch("industry_reforged.views.orders.management.messages"):
            response = toggle_order_item_bought(request, item.id)
            assert response.status_code == 302
            item.refresh_from_db()
            assert item.is_bought is False

    def test_toggle_bought_authorized_director_toggle(self, rf):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        item = OrderItemFactory(order=order)

        user = UserFactory()
        director_char = EveCharacterFactory(corporation_id=corp.corporation_id)
        user.profile.main_character = director_char
        user.profile.save()
        perm = Permission.objects.get(codename="corp_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)

        request = rf.post(f"/orders/items/{item.id}/toggle-bought/")
        request.user = user

        with patch("industry_reforged.views.orders.management.messages"):
            response = toggle_order_item_bought(request, item.id)
            assert response.status_code == 302
            item.refresh_from_db()
            assert item.is_bought is True
            assert item.bought_by == director_char
            assert item.bought_at is not None

            # Toggle back to False
            response = toggle_order_item_bought(request, item.id)
            assert response.status_code == 302
            item.refresh_from_db()
            assert item.is_bought is False
            assert item.bought_by is None
            assert item.bought_at is None

    def test_toggle_bought_ajax(self, rf):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        item = OrderItemFactory(order=order)

        user = UserFactory()
        user.profile.main_character = order.character
        user.profile.save()
        CharacterOwnership.objects.create(
            user=user,
            character=order.character,
            owner_hash="dummy_hash",
        )

        request = rf.post(
            f"/orders/items/{item.id}/toggle-bought/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        request.user = user

        response = toggle_order_item_bought(request, item.id)
        assert response.status_code == 200
        data = json.loads(response.content.decode("utf-8"))
        assert data["success"] is True
        assert data["is_bought"] is True
        assert data["bought_by"] == order.character.character_name
        assert data["bought_at"] is not None

        item.refresh_from_db()
        assert item.is_bought is True

    def test_build_status_to_build_when_no_tasks(self):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        item = OrderItemFactory(order=order)

        with patch.object(OrderItem, "is_buy_product", False):
            status_info = item.build_status_info
            assert status_info is not None
            assert status_info["status"] == "TO_BUILD"
            assert status_info["badge_class"] == "bg-secondary"
            assert status_info["icon"] == "fa-hammer"

    def test_build_status_unclaimed_and_in_production_and_completed(self):
        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory()
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        item = OrderItemFactory(order=order)

        with patch.object(OrderItem, "is_buy_product", False):
            # 1. Unclaimed task
            t = ProductionTaskFactory(
                created_from_order=order,
                item_type=item.item_type,
                status="UNCLAIMED",
                quantity=1,
            )
            # Clear cached property
            if hasattr(item, "_cached_build_status_info"):
                delattr(item, "_cached_build_status_info")
            info = item.get_build_status()
            assert info["status"] == "UNCLAIMED"
            assert info["badge_class"] == "bg-warning text-dark"
            assert info["icon"] == "fa-clock"

            # 2. In Production task
            t.status = "IN_PRODUCTION"
            t.save()
            info = item.get_build_status()
            assert info["status"] == "IN_PRODUCTION"
            assert info["badge_class"] == "bg-info text-dark"
            assert info["icon"] == "fa-cogs"

            # 3. Completed task
            t.status = "COMPLETED"
            t.completed_at = timezone.now()
            t.save()
            info = item.get_build_status()
            assert info["status"] == "COMPLETED"
            assert info["badge_class"] == "bg-success"
            assert info["icon"] == "fa-check"

    def test_build_status_buy_product_returns_none(self):
        item = OrderItemFactory()
        with patch.object(OrderItem, "is_buy_product", True):
            assert item.get_build_status() is None

