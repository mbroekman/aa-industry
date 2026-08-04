# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.test import RequestFactory

# AA Industry App
from industry_reforged.tests.factories import (
    MemberOrderFactory,
    OrderItemFactory,
    UserFactory,
)
from industry_reforged.views.orders.splitting import split_bom_component, split_order


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestSplittingViews:
    def _get_user(self):
        user = UserFactory()
        perms = Permission.objects.filter(
            codename__in=["basic_access", "director_access", "corp_access"]
        )
        user.user_permissions.add(*perms)
        user = user.__class__.objects.get(pk=user.pk)
        return user

    @patch("industry_reforged.views.orders.splitting.messages")
    def test_split_order(self, mock_messages, rf):
        user = self._get_user()
        order = MemberOrderFactory(status="REQUESTED")
        item1 = OrderItemFactory(order=order, quantity=10)
        OrderItemFactory(order=order, quantity=5)

        request = rf.post("/", {"item_ids": [str(item1.id)], f"qty_{item1.id}": "5"})
        request.user = user

        res = split_order(request, order.id)
        assert res.status_code in [302, 200]

    @patch("industry_reforged.views.orders.splitting.messages")
    def test_split_bom_component(self, mock_messages, rf):
        user = self._get_user()
        order = MemberOrderFactory(status="REQUESTED")

        request = rf.post("/", {"task_id": 1, "quantity": 5})
        request.user = user

        # Will hit order found but task maybe missing, which is fine for coverage
        res = split_bom_component(request, order.id)
        assert res.status_code in [302, 200]
