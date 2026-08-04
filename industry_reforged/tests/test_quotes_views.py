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

        with patch("industry_reforged.views.orders.quotes.render") as mock_render:
            with patch("industry_reforged.views.orders.quotes.messages"):
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

        with patch("industry_reforged.views.orders.quotes.messages"):
            res = provide_quote(request, 1)
            assert res.status_code == 302

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
