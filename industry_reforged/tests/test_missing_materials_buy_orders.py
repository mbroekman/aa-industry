"""
Unit tests for TASK-265: a "Missing Materials" overview of what's still short to
finish a member's own claimed jobs (industrialist dashboard), and director-only
creation of CorpBuyOrder rows for the shortfall of selected materials on an
order's Required Raw Materials table.
"""

# Standard Library
from unittest.mock import MagicMock, patch

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import RequestFactory, TestCase

# AA Industry App
from industry_reforged.models import CorpBuyOrder
from industry_reforged.tests.factories import (
    EveTypeFactory,
    MemberOrderFactory,
    ProductionTaskFactory,
    UserFactory,
)
from industry_reforged.views.industrialist import industrialist_dashboard
from industry_reforged.views.orders.quotes import create_buy_orders_from_order


class TestMissingMaterialsOverview(TestCase):
    """Industrialist-side: my_missing_materials on industrialist_dashboard."""

    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()

        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700001,
            corporation_name="Missing Mats Corp",
            corporation_ticker="MMC",
        )
        self.character = EveCharacter.objects.create(
            character_id=93000001,
            character_name="Materials Tester",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.user = UserFactory()
        perm = Permission.objects.get(codename="industrialist_access")
        self.user.user_permissions.add(perm)
        self.user = self.user.__class__.objects.get(pk=self.user.pk)
        self.user.profile.main_character = self.character
        self.user.profile.save()
        CharacterOwnership.objects.create(
            user=self.user, character=self.character, owner_hash="mmhash1"
        )

    def _request(self):
        req = self.rf.get("/industry/industrialist/")
        req.user = self.user
        req.session = MagicMock()
        req._messages = FallbackStorage(req)
        return req

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
    def test_no_claimed_tasks_means_no_missing_materials(
        self, mock_sri, mock_stored, mock_url
    ):
        resp = industrialist_dashboard(self._request())
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert "You have no claimed jobs right now." in content

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
    @patch("industry_reforged.views.industrialist.calculate_tasks_bom")
    def test_only_short_materials_are_listed(
        self, mock_bom, mock_sri, mock_stored, mock_url
    ):
        item_type = EveTypeFactory(name="Rifter")
        ProductionTaskFactory(
            item_type=item_type,
            quantity=1,
            status="IN_PRODUCTION",
            assigned_to=self.character,
        )
        mock_bom.return_value = {
            34: {
                "type_id": 34,
                "name": "Tritanium",
                "group_name": "Minerals",
                "quantity": 1000,
                "corp_stock": 200,
            },
            35: {
                "type_id": 35,
                "name": "Pyerite",
                "group_name": "Minerals",
                "quantity": 500,
                "corp_stock": 900,
            },
        }

        resp = industrialist_dashboard(self._request())
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        # Tritanium (1000 required vs 200 in stock) is short and listed.
        assert "Tritanium" in content
        # Pyerite has sufficient stock (900 >= 500) - it must NOT be listed,
        # this tab is "what's missing," not a full BOM breakdown.
        assert "Pyerite" not in content
        assert '<span class="badge bg-danger ms-1">1</span>' in content


def _user_with_perms(codenames):
    user = UserFactory()
    perms = Permission.objects.filter(codename__in=codenames)
    user.user_permissions.add(*perms)
    return user.__class__.objects.get(pk=user.pk)


class TestCreateBuyOrdersFromOrder(TestCase):
    """Director/CP-side: create_buy_orders_from_order."""

    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()

        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98700002,
            corporation_name="Buy Order Corp",
            corporation_ticker="BOC",
        )
        self.order_owner = EveCharacter.objects.create(
            character_id=93000002,
            character_name="Order Owner",
            corporation_id=self.corp.corporation_id,
            corporation_name=self.corp.corporation_name,
        )
        self.order = MemberOrderFactory(character=self.order_owner)

        self.tritanium = EveTypeFactory(id=10034, name="Tritanium")
        self.pyerite = EveTypeFactory(id=10035, name="Pyerite")

        self.bom_patch = patch(
            "industry_reforged.views.orders.quotes.calculate_order_bom"
        )
        mock_bom = self.bom_patch.start()
        mock_bom.return_value = {
            self.tritanium.id: {
                "type_id": self.tritanium.id,
                "name": "Tritanium",
                "quantity": 1000,
                "corp_stock": 200,
            },
            self.pyerite.id: {
                "type_id": self.pyerite.id,
                "name": "Pyerite",
                "quantity": 500,
                "corp_stock": 900,
            },
        }
        self.addCleanup(self.bom_patch.stop)

    def _post(self, user, type_ids):
        req = self.rf.post("/", {"type_ids": type_ids})
        req.user = user
        req.session = MagicMock()
        req._messages = FallbackStorage(req)
        return req

    def test_creates_buy_order_for_shortfall_only(self):
        director = _user_with_perms(["corp_access"])
        req = self._post(director, [self.tritanium.id, self.pyerite.id])

        create_buy_orders_from_order(req, self.order.id)

        orders = list(CorpBuyOrder.objects.all())
        assert len(orders) == 1
        order = orders[0]
        assert order.item_type_id == self.tritanium.id
        assert order.quantity == 800  # 1000 required - 200 in stock
        assert order.status == "OPEN"
        # Pyerite has sufficient stock (900 >= 500) - no buy order for it.
        assert not CorpBuyOrder.objects.filter(item_type_id=self.pyerite.id).exists()

    def test_merges_into_existing_open_buy_order(self):
        director = _user_with_perms(["corp_access"])
        existing = CorpBuyOrder.objects.create(
            corporation=self.corp,
            item_type=self.tritanium,
            quantity=50,
            status="OPEN",
        )

        req = self._post(director, [self.tritanium.id])
        create_buy_orders_from_order(req, self.order.id)

        existing.refresh_from_db()
        assert existing.quantity == 850  # 50 existing + 800 shortfall
        assert CorpBuyOrder.objects.filter(item_type_id=self.tritanium.id).count() == 1

    def test_requires_corp_access_permission(self):
        member = _user_with_perms(["basic_access"])
        req = self._post(member, [self.tritanium.id])

        create_buy_orders_from_order(req, self.order.id)

        assert CorpBuyOrder.objects.count() == 0

    def test_no_selection_creates_nothing(self):
        director = _user_with_perms(["corp_access"])
        req = self._post(director, [])

        create_buy_orders_from_order(req, self.order.id)

        assert CorpBuyOrder.objects.count() == 0

    def test_get_request_is_a_noop(self):
        director = _user_with_perms(["corp_access"])
        req = self.rf.get("/")
        req.user = director
        req.session = MagicMock()
        req._messages = FallbackStorage(req)

        create_buy_orders_from_order(req, self.order.id)

        assert CorpBuyOrder.objects.count() == 0
