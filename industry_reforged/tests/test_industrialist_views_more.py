# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.test import RequestFactory

# AA Industry App
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
)
from industry_reforged.views.industrialist import (
    industrialist_dashboard,
    industrialist_leaderboard,
)


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestIndustrialistViewsMore:
    def _get_industrialist_user(self):
        user = UserFactory()
        corp = EveCorporationInfoFactory(corporation_id=1)
        char = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = char
        user.profile.save()

        # Add necessary permissions
        perms = Permission.objects.filter(
            codename__in=["basic_access", "industrialist_access"]
        )
        user.user_permissions.add(*perms)
        user = user.__class__.objects.get(pk=user.pk)
        return user

    @patch("industry_reforged.views.industrialist.render")
    def test_industrialist_dashboard(self, mock_render, rf):
        request = rf.get("/")
        request.user = self._get_industrialist_user()
        industrialist_dashboard(request)
        mock_render.assert_called()

    @patch("industry_reforged.views.industrialist.render")
    def test_industrialist_leaderboard(self, mock_render, rf):
        request = rf.get("/")
        request.user = self._get_industrialist_user()
        industrialist_leaderboard(request)
        mock_render.assert_called()
