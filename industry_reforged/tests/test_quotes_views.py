# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.test import RequestFactory

# AA Industry App
from industry_reforged.tests.factories import MemberOrderFactory, UserFactory
from industry_reforged.views.orders.quotes import (
    accept_quote,
    provide_quote,
    reject_quote,
    view_quote,
)


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestQuotesViews:
    def test_view_quote(self, rf):
        # AA Industry App
        from industry_reforged.tests.factories import EveCorporationInfoFactory

        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory(id=1, status="REQUESTED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.get("/")
        user = UserFactory()
        user.profile.main_character = order.character
        # Django
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(codename="industrialist_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        request.user = user

        with (
            patch("industry_reforged.views.orders.quotes.render") as mock_render,
            patch("industry_reforged.views.orders.quotes.messages"),
        ):
            view_quote(request, 1)
            mock_render.assert_called()

    def test_provide_quote(self, rf):
        # AA Industry App
        from industry_reforged.tests.factories import EveCorporationInfoFactory

        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory(id=1, status="REQUESTED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.post(
            "/",
            {
                "pricing_override": "1.0",
                "profit_margin": "0.1",
                "me_override": "0",
                "te_override": "0",
            },
        )
        user = UserFactory()
        user.profile.main_character = order.character
        request.user = user

        from decimal import Decimal

        with (
            patch("industry_reforged.views.orders.quotes.messages"),
            patch(
                "industry_reforged.views.orders.quotes.calculate_bom_cost",
                return_value=Decimal("12345.67"),
            ),
        ):
            res = provide_quote(request, 1)
            assert res.status_code == 302
            order.refresh_from_db()
            assert order.true_cost == Decimal("12345.67")

    def test_view_quote_excludes_blueprints_from_total_bom_price(self, rf):
        # Django
        from django.contrib.auth.models import Permission

        # AA Industry App
        from industry_reforged.tests.factories import (
            EveCategoryFactory,
            EveCorporationInfoFactory,
            EveGroupFactory,
            EveTypeFactory,
        )

        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory(id=2, status="REQUESTED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.get("/")
        user = UserFactory()
        user.profile.main_character = order.character
        perm = Permission.objects.get(codename="industrialist_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        request.user = user

        cat_bp = EveCategoryFactory(id=9, name="Blueprint")
        grp_bp = EveGroupFactory(id=900, name="Ship Blueprints", eve_category=cat_bp)
        bp_type = EveTypeFactory(id=99001, name="Erebus Blueprint", eve_group=grp_bp)

        cat_mat = EveCategoryFactory(id=4, name="Material")
        grp_mat = EveGroupFactory(id=18, name="Mineral", eve_category=cat_mat)
        mat_type = EveTypeFactory(id=99002, name="Tritanium", eve_group=grp_mat)

        # Corp owns the blueprint
        from industry_reforged.models import CorpBlueprint

        CorpBlueprint.objects.create(
            corporation=corp, eve_type=bp_type, item_id=123, location_id=456, runs=-1
        )

        mock_bom = {
            bp_type.id: {"type_id": bp_type.id, "name": bp_type.name, "quantity": 1},
            mat_type.id: {
                "type_id": mat_type.id,
                "name": mat_type.name,
                "quantity": 100,
            },
        }

        with (
            patch(
                "industry_reforged.views.orders.quotes.calculate_order_bom",
                return_value=mock_bom,
            ),
            patch(
                "industry_reforged.views.orders.quotes.get_detailed_prices",
                return_value={
                    bp_type.id: {
                        "original_jita_price": 5_000_000_000.0,
                        "final_price": 5_000_000_000.0,
                    },
                    mat_type.id: {"original_jita_price": 5.0, "final_price": 5.0},
                },
            ),
            patch("industry_reforged.views.orders.quotes.render") as mock_render,
            patch("industry_reforged.views.orders.quotes.messages"),
        ):
            view_quote(request, 2)
            mock_render.assert_called()
            context = mock_render.call_args[0][2]
            # Corp-owned blueprint cost (5 Billion) must NOT be included in total_bom_price
            # Only material cost (100 * 5.0 = 500.0)
            assert context["total_bom_price"] == 500.0
            assert context["bom_blueprints"][0]["is_corp_owned"] is True
            assert context["bom_blueprints"][0]["price_per_unit"] == 0.0
            assert context["bom_blueprints"][0]["total_price"] == 0.0
            assert "profit_margin_percent" in context
            assert "structure_job_costs" in context

    def test_view_quote_includes_unowned_blueprints_in_total_bom_price(self, rf):
        from django.contrib.auth.models import Permission

        from industry_reforged.tests.factories import (
            EveCategoryFactory,
            EveCorporationInfoFactory,
            EveGroupFactory,
            EveTypeFactory,
        )

        corp = EveCorporationInfoFactory(corporation_id=10)
        order = MemberOrderFactory(id=3, status="REQUESTED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.get("/")
        user = UserFactory()
        user.profile.main_character = order.character
        perm = Permission.objects.get(codename="industrialist_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        request.user = user

        cat_bp = EveCategoryFactory(id=9, name="Blueprint")
        grp_bp = EveGroupFactory(id=901, name="Module Blueprints", eve_category=cat_bp)
        bp_type = EveTypeFactory(id=99010, name="Unowned Blueprint", eve_group=grp_bp)

        cat_mat = EveCategoryFactory(id=4, name="Material")
        grp_mat = EveGroupFactory(id=18, name="Mineral", eve_category=cat_mat)
        mat_type = EveTypeFactory(id=99011, name="Tritanium", eve_group=grp_mat)

        mock_bom = {
            bp_type.id: {"type_id": bp_type.id, "name": bp_type.name, "quantity": 1},
            mat_type.id: {
                "type_id": mat_type.id,
                "name": mat_type.name,
                "quantity": 100,
            },
        }

        with (
            patch(
                "industry_reforged.views.orders.quotes.calculate_order_bom",
                return_value=mock_bom,
            ),
            patch(
                "industry_reforged.views.orders.quotes.get_detailed_prices",
                return_value={
                    bp_type.id: {
                        "original_jita_price": 50_000_000.0,
                        "final_price": 50_000_000.0,
                    },
                    mat_type.id: {"original_jita_price": 5.0, "final_price": 5.0},
                },
            ),
            patch("industry_reforged.views.orders.quotes.render") as mock_render,
            patch("industry_reforged.views.orders.quotes.messages"),
        ):
            view_quote(request, 3)
            mock_render.assert_called()
            context = mock_render.call_args[0][2]
            # Unowned blueprint cost (50M) MUST be included in total_bom_price
            assert context["bom_blueprints"][0]["is_corp_owned"] is False
            assert context["total_bom_price"] == 50_000_500.0

    def test_accept_quote(self, rf):
        # AA Industry App
        from industry_reforged.tests.factories import EveCorporationInfoFactory

        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory(id=1, status="PROVIDED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.post("/")
        user = UserFactory()
        user.profile.main_character = order.character
        request.user = user

        with patch("industry_reforged.views.orders.quotes.messages"):
            res = accept_quote(request, 1)
            assert res.status_code == 302

    def test_reject_quote(self, rf):
        # AA Industry App
        from industry_reforged.tests.factories import EveCorporationInfoFactory

        corp = EveCorporationInfoFactory(corporation_id=1)
        order = MemberOrderFactory(id=1, status="PROVIDED")
        order.character.corporation_id = corp.corporation_id
        order.character.save()
        request = rf.post("/")
        user = UserFactory()
        user.profile.main_character = order.character
        request.user = user

        with patch("industry_reforged.views.orders.quotes.messages"):
            res = reject_quote(request, 1)
            assert res.status_code == 302
