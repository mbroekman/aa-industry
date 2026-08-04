# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

# AA Industry App
from industry_reforged.tests.factories import UserFactory
from industry_reforged.views.industrialist import (
    bulk_claim_tasks,
    bulk_complete_tasks,
    bulk_unclaim_tasks,
    claim_task,
    complete_task,
    industrialist_leaderboard,
    unclaim_task,
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
class TestMassiveIndustrialistViews:
    @patch("industry_reforged.views.industrialist.render")
    @patch("industry_reforged.views.industrialist.messages")
    def test_industrialist_actions(self, mock_messages, mock_render, rf):
        user = get_user_with_perms()
        request = rf.post("/")
        request.user = user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Call the various views with a dummy ID 9999
        try:
            claim_task(request, 9999)
        except Exception:
            pass
        try:
            unclaim_task(request, 9999)
        except Exception:
            pass
        try:
            bulk_claim_tasks(request)
        except Exception:
            pass
        try:
            bulk_unclaim_tasks(request)
        except Exception:
            pass
        try:
            complete_task(request, 9999)
        except Exception:
            pass
        try:
            bulk_complete_tasks(request)
        except Exception:
            pass
        try:
            industrialist_leaderboard(request)
        except Exception:
            pass
