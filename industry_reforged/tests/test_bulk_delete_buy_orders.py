"""
Unit tests for bulk-deleting Procurement Buy Orders from the Director Dashboard's
Buy Orders tab (checkbox selection + "Delete Selected").
"""

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import RequestFactory, TestCase

# AA Industry App
from industry_reforged.models import CorpBuyOrder
from industry_reforged.tests.factories import EveTypeFactory, UserFactory
from industry_reforged.views.director import bulk_delete_buy_orders


def _user_with_perms(codenames):
    user = UserFactory()
    perms = Permission.objects.filter(codename__in=codenames)
    user.user_permissions.add(*perms)
    return user.__class__.objects.get(pk=user.pk)


class TestBulkDeleteBuyOrders(TestCase):
    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700003,
            corporation_name="Bulk Delete Corp",
            corporation_ticker="BDC",
        )
        self.item_a = EveTypeFactory(name="Tritanium")
        self.item_b = EveTypeFactory(name="Pyerite")
        self.item_c = EveTypeFactory(name="Mexallon")

        self.order_a = CorpBuyOrder.objects.create(
            corporation=self.corp, item_type=self.item_a, quantity=100, status="OPEN"
        )
        self.order_b = CorpBuyOrder.objects.create(
            corporation=self.corp, item_type=self.item_b, quantity=200, status="OPEN"
        )
        self.order_c = CorpBuyOrder.objects.create(
            corporation=self.corp, item_type=self.item_c, quantity=300, status="OPEN"
        )

    def _post(self, user, ids):
        req = self.rf.post("/", {"buy_order_ids": ids})
        req.user = user
        req.session = {}
        req._messages = FallbackStorage(req)
        return req

    def test_deletes_only_selected_orders(self):
        director = _user_with_perms(["corp_access"])
        req = self._post(director, [self.order_a.id, self.order_b.id])

        bulk_delete_buy_orders(req)

        assert not CorpBuyOrder.objects.filter(id=self.order_a.id).exists()
        assert not CorpBuyOrder.objects.filter(id=self.order_b.id).exists()
        assert CorpBuyOrder.objects.filter(id=self.order_c.id).exists()

    def test_requires_corp_access_permission(self):
        member = _user_with_perms(["basic_access"])
        req = self._post(member, [self.order_a.id])

        bulk_delete_buy_orders(req)

        assert CorpBuyOrder.objects.filter(id=self.order_a.id).exists()

    def test_no_selection_deletes_nothing(self):
        director = _user_with_perms(["corp_access"])
        req = self._post(director, [])

        bulk_delete_buy_orders(req)

        assert CorpBuyOrder.objects.count() == 3

    def test_get_request_is_a_noop(self):
        director = _user_with_perms(["corp_access"])
        req = self.rf.get("/")
        req.user = director
        req.session = {}
        req._messages = FallbackStorage(req)

        bulk_delete_buy_orders(req)

        assert CorpBuyOrder.objects.count() == 3
