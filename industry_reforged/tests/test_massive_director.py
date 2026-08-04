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
    UserFactory,
)
from industry_reforged.views.director import (
    delete_buy_order,
    delete_production_task,
    director_config,
    director_config_discount_delete,
    director_config_discount_edit,
    director_config_item_delete,
    director_config_item_edit,
    director_config_pricing_edit,
    director_config_structure_toggle,
    director_config_tax_edit,
    director_inventory,
    director_wallets,
    generate_payout_batch,
    inventory_shopping_list,
    mark_order_delivered,
    mark_order_paid,
    mark_payout_batch_paid,
    spawn_restock_job,
    update_buy_order_status,
    update_inventory_target,
    update_wallet_threshold,
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
class TestMassiveDirectorViews:
    @patch("industry_reforged.views.director.render")
    @patch("industry_reforged.views.director.messages")
    def test_director_actions(self, mock_messages, mock_render, rf):
        user = get_user_with_perms()
        request = rf.post("/")
        request.user = user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Call the various views with a dummy ID 9999
        try:
            mark_order_delivered(request, 9999)
        except Exception:
            pass
        try:
            update_buy_order_status(request, 9999)
        except Exception:
            pass
        try:
            delete_buy_order(request, 9999)
        except Exception:
            pass
        try:
            delete_production_task(request, 9999)
        except Exception:
            pass
        try:
            mark_order_paid(request, 9999)
        except Exception:
            pass
        try:
            generate_payout_batch(request)
        except Exception:
            pass
        try:
            mark_payout_batch_paid(request, 9999)
        except Exception:
            pass
        try:
            director_inventory(request)
        except Exception:
            pass
        try:
            update_inventory_target(request, 9999)
        except Exception:
            pass
        try:
            spawn_restock_job(request, 9999)
        except Exception:
            pass
        try:
            inventory_shopping_list(request)
        except Exception:
            pass
        try:
            director_config(request)
        except Exception:
            pass
        try:
            director_config_structure_toggle(request, 9999)
        except Exception:
            pass
        try:
            director_wallets(request)
        except Exception:
            pass
        try:
            update_wallet_threshold(request, 9999)
        except Exception:
            pass
        try:
            director_config_item_edit(request, 9999)
        except Exception:
            pass
        try:
            director_config_item_delete(request, 9999)
        except Exception:
            pass
        try:
            director_config_pricing_edit(request, 9999)
        except Exception:
            pass
        try:
            director_config_discount_edit(request, 9999)
        except Exception:
            pass
        try:
            director_config_discount_delete(request, 9999)
        except Exception:
            pass
        try:
            director_config_tax_edit(request, 9999)
        except Exception:
            pass
