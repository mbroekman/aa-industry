# Standard Library

# Third Party
import pytest

# Django
from django.urls import reverse

from .factories import EveCharacterFactory, EveCorporationInfoFactory, UserFactory


@pytest.fixture(autouse=True)
def mock_static(monkeypatch):
    # Django
    from django.contrib.staticfiles.storage import staticfiles_storage

    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}")
    try:
        # Third Party
        from sri.templatetags import sri

        monkeypatch.setattr(
            sri,
            "sri_integrity_static",
            lambda path, algorithm_type=None: "sha256-dummy",
        )
    except ImportError:
        pass


@pytest.mark.django_db
class TestViews:
    def test_dashboard_view_unauthenticated(self, client):
        url = reverse("industry_reforged:index")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_dashboard_view_authenticated_no_character(self, client):
        # Django
        from django.contrib.auth.models import Permission

        user = UserFactory()
        perm = Permission.objects.get(codename="basic_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        assert user.has_perm("industry_reforged.basic_access")
        url = reverse("industry_reforged:index")
        response = client.get(url)
        # Alliance Auth intercepts users with no main character and redirects to dashboard
        assert response.status_code == 302
        assert "/dashboard" in response.url

    def test_industrialist_dashboard_view(self, client):
        # Django
        from django.contrib.auth.models import Permission

        user = UserFactory()
        corp = EveCorporationInfoFactory()
        character = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = character
        user.profile.save()
        perm = Permission.objects.get(codename="industrialist_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        assert user.has_perm("industry_reforged.industrialist_access")
        url = reverse("industry_reforged:industrialist_dashboard")
        # Ensure that it doesn't crash
        response = client.get(url)
        assert response.status_code == 200

    def test_quotes_view(self, client):
        # Django
        from django.contrib.auth.models import Permission

        user = UserFactory()
        corp = EveCorporationInfoFactory()
        character = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = character
        user.profile.save()
        perm = Permission.objects.get(codename="basic_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        assert user.has_perm("industry_reforged.basic_access")
        url = reverse("industry_reforged:orders_dashboard")
        response = client.get(url)
        assert response.status_code == 200

    def test_api_endpoints(self, client):
        pass

    def test_orders_views(self, client):
        # Django
        from django.contrib.auth.models import Permission

        user = UserFactory()
        corp = EveCorporationInfoFactory()
        character = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = character
        user.profile.save()
        perm = Permission.objects.get(codename="basic_access")
        user.user_permissions.add(perm)
        user = user.__class__.objects.get(pk=user.pk)
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")

        # Test create order
        url = reverse("industry_reforged:create_order")
        response = client.get(url)
        assert response.status_code in [200, 302]

        # Test shopping list
        url = reverse("industry_reforged:shopping_list")
        response = client.get(url)
        assert response.status_code in [200, 302]
