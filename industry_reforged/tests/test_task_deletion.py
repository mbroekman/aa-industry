# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.urls import reverse

# Eve Models
from eveuniverse.models import EveType

# AA Industry App
from industry_reforged.models import ProductionTask
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
    ProductionTaskFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def mock_static(monkeypatch):
    from django.contrib.staticfiles.storage import staticfiles_storage

    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}")
    try:
        from sri.templatetags import sri

        monkeypatch.setattr(
            sri,
            "sri_integrity_static",
            lambda path, algorithm_type=None: "sha256-dummy",
        )
    except ImportError:
        pass


@pytest.mark.django_db
class TestTaskDeletion:
    @pytest.fixture
    def cp_user(self):
        user = UserFactory()
        corp = EveCorporationInfoFactory()
        char = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = char
        user.profile.save()
        perms = Permission.objects.filter(
            codename__in=["corp_access", "industrialist_access", "basic_access"]
        )
        user.user_permissions.add(*perms)
        return user.__class__.objects.get(pk=user.pk)

    @pytest.fixture
    def non_cp_user(self):
        user = UserFactory()
        corp = EveCorporationInfoFactory()
        char = EveCharacterFactory(
            corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
        )
        user.profile.main_character = char
        user.profile.save()
        perms = Permission.objects.filter(
            codename__in=["industrialist_access", "basic_access"]
        )
        user.user_permissions.add(*perms)
        return user.__class__.objects.get(pk=user.pk)

    def test_cp_user_can_delete_basket_production_task(self, client, cp_user):
        client.force_login(cp_user, backend="django.contrib.auth.backends.ModelBackend")
        item_type = EveTypeFactory()
        # Basket-generated task has no created_from_order
        task = ProductionTask.objects.create(
            item_type=item_type,
            quantity=10,
            status="UNCLAIMED",
        )
        assert ProductionTask.objects.filter(id=task.id).exists()

        url = reverse("industry_reforged:delete_production_task", kwargs={"task_id": task.id})
        response = client.post(url)
        assert response.status_code == 302
        assert not ProductionTask.objects.filter(id=task.id).exists()

    def test_cp_user_delete_task_with_subtasks(self, client, cp_user):
        client.force_login(cp_user, backend="django.contrib.auth.backends.ModelBackend")
        item_type = EveTypeFactory()
        parent_task = ProductionTask.objects.create(
            item_type=item_type, quantity=1, status="UNCLAIMED"
        )
        child_task = ProductionTask.objects.create(
            item_type=item_type, quantity=5, status="UNCLAIMED", bom_parent=parent_task
        )
        assert ProductionTask.objects.filter(id=parent_task.id).exists()
        assert ProductionTask.objects.filter(id=child_task.id).exists()

        url = reverse("industry_reforged:delete_production_task", kwargs={"task_id": parent_task.id})
        response = client.post(url)
        assert response.status_code == 302
        assert not ProductionTask.objects.filter(id=parent_task.id).exists()
        assert not ProductionTask.objects.filter(id=child_task.id).exists()

    def test_cp_user_bulk_delete_tasks(self, client, cp_user):
        client.force_login(cp_user, backend="django.contrib.auth.backends.ModelBackend")
        item_type = EveTypeFactory()
        task1 = ProductionTask.objects.create(item_type=item_type, quantity=2, status="UNCLAIMED")
        task2 = ProductionTask.objects.create(item_type=item_type, quantity=4, status="UNCLAIMED")
        task3 = ProductionTask.objects.create(item_type=item_type, quantity=6, status="IN_PRODUCTION")

        url = reverse("industry_reforged:bulk_delete_tasks")
        response = client.post(url, {"task_ids": [task1.id, task2.id, task3.id]})
        assert response.status_code == 302
        assert not ProductionTask.objects.filter(id__in=[task1.id, task2.id, task3.id]).exists()

    def test_non_cp_user_cannot_delete_task(self, client, non_cp_user):
        client.force_login(non_cp_user, backend="django.contrib.auth.backends.ModelBackend")
        item_type = EveTypeFactory()
        task = ProductionTask.objects.create(item_type=item_type, quantity=1, status="UNCLAIMED")

        url = reverse("industry_reforged:delete_production_task", kwargs={"task_id": task.id})
        response = client.post(url)
        assert response.status_code == 302  # redirected due to permission_required
        assert ProductionTask.objects.filter(id=task.id).exists()

        bulk_url = reverse("industry_reforged:bulk_delete_tasks")
        bulk_response = client.post(bulk_url, {"task_ids": [task.id]})
        assert bulk_response.status_code == 302
        assert ProductionTask.objects.filter(id=task.id).exists()
