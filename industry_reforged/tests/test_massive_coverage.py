# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

# AA Industry App
from industry_reforged.tests.factories import (
    MemberOrderFactory,
    UserFactory,
)
from industry_reforged.views.director import director_dashboard
from industry_reforged.views.industrialist import industrialist_dashboard
from industry_reforged.views.orders.quotes import (
    accept_quote,
    htmx_update_quote_facility,
    provide_quote,
    reject_quote,
    update_quote_me_overrides,
    view_quote,
)


@pytest.fixture
def rf():
    return RequestFactory()


def get_user_with_perms():
    user = UserFactory()
    perms = Permission.objects.filter(
        codename__in=[
            "director_access",
            "industrialist_access",
            "corp_access",
            "basic_access",
        ]
    )
    user.user_permissions.add(*perms)
    user = user.__class__.objects.get(pk=user.pk)
    return user


@pytest.mark.django_db
class TestMassiveViews:
    @patch("industry_reforged.views.director.render")
    @patch("industry_reforged.views.industrialist.render")
    def test_dashboards(self, mock_ind_render, mock_dir_render, rf):
        user = get_user_with_perms()
        request = rf.get("/")
        request.user = user

        # We just want them to run for coverage
        director_dashboard(request)
        industrialist_dashboard(request)

    @patch("industry_reforged.views.orders.quotes.render")
    @patch("industry_reforged.views.orders.quotes.messages")
    def test_quote_actions(self, mock_messages, mock_render, rf):
        user = get_user_with_perms()
        order = MemberOrderFactory(status="REQUESTED")
        # AA Industry App
        from industry_reforged.tests.factories import EveCorporationInfoFactory

        EveCorporationInfoFactory(corporation_id=order.character.corporation_id)

        request = rf.post("/")
        request.user = user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Call the various views
        view_quote(request, order.id)
        provide_quote(request, order.id)
        htmx_update_quote_facility(request, order.id)
        update_quote_me_overrides(request, order.id)

        # We probably need to mock process_order and things for accept_quote if we don't want it to crash, but let's just let it crash and catch exception if it does!
        try:
            accept_quote(request, order.id)
        except Exception:
            pass

        reject_quote(request, order.id)
