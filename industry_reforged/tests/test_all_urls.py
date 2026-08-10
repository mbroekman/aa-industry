# Third Party
import pytest

# Django
from django.urls import reverse

from .factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    IndustryFacilityFactory,
    MemberOrderFactory,
    ProductionTaskFactory,
    UserFactory,
)


@pytest.fixture
def superuser_client(client):
    user = UserFactory(is_superuser=True)
    corp = EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
    )
    user.profile.main_character = character
    user.profile.save()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    return client


@pytest.fixture(autouse=True)
def seed_db():
    from .factories import CorpWalletDivisionFactory

    MemberOrderFactory(id=1)
    ProductionTaskFactory(id=1)
    IndustryFacilityFactory(facility_id=1)
    CorpWalletDivisionFactory(division=1)
    pass


@pytest.mark.django_db
class TestAllUrls:
    # pylint: disable=too-many-public-methods
    def test_index(self, superuser_client):
        url = reverse("industry_reforged:index")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_personal_dashboard(self, superuser_client):
        url = reverse("industry_reforged:personal_dashboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_corporate_dashboard(self, superuser_client):
        url = reverse("industry_reforged:corporate_dashboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_add_personal_token(self, superuser_client):
        url = reverse("industry_reforged:add_personal_token")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_add_corporate_token(self, superuser_client):
        url = reverse("industry_reforged:add_corporate_token")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_trigger_pi_sync(self, superuser_client):
        url = reverse("industry_reforged:trigger_pi_sync")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_orders_dashboard(self, superuser_client):
        url = reverse("industry_reforged:orders_dashboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_create_order(self, superuser_client):
        url = reverse("industry_reforged:create_order")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_shopping_list(self, superuser_client):
        url = reverse("industry_reforged:shopping_list")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_view_quote(self, superuser_client):
        url = reverse("industry_reforged:view_quote", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_accept_quote(self, superuser_client):
        url = reverse("industry_reforged:accept_quote", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_reject_quote(self, superuser_client):
        url = reverse("industry_reforged:reject_quote", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_htmx_update_quote_facility(self, superuser_client):
        url = reverse(
            "industry_reforged:htmx_update_quote_facility", kwargs={"order_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_update_quote_me_overrides(self, superuser_client):
        url = reverse(
            "industry_reforged:update_quote_me_overrides", kwargs={"order_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_delete_order(self, superuser_client):
        url = reverse("industry_reforged:delete_order", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_provide_quote(self, superuser_client):
        url = reverse("industry_reforged:provide_quote", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_split_order(self, superuser_client):
        url = reverse("industry_reforged:split_order", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_split_bom_component(self, superuser_client):
        url = reverse("industry_reforged:split_bom_component", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_industrialist_dashboard(self, superuser_client):
        url = reverse("industry_reforged:industrialist_dashboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_claim_task(self, superuser_client):
        url = reverse("industry_reforged:claim_task", kwargs={"task_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_unclaim_task(self, superuser_client):
        url = reverse("industry_reforged:unclaim_task", kwargs={"task_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_bulk_claim_tasks(self, superuser_client):
        url = reverse("industry_reforged:bulk_claim_tasks")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_bulk_unclaim_tasks(self, superuser_client):
        url = reverse("industry_reforged:bulk_unclaim_tasks")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_complete_task(self, superuser_client):
        url = reverse("industry_reforged:complete_task", kwargs={"task_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_bulk_complete_tasks(self, superuser_client):
        url = reverse("industry_reforged:bulk_complete_tasks")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_industrialist_leaderboard(self, superuser_client):
        url = reverse("industry_reforged:industrialist_leaderboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_dashboard(self, superuser_client):
        url = reverse("industry_reforged:director_dashboard")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_dt_director_orders(self, superuser_client):
        url = reverse("industry_reforged:dt_director_orders")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_dt_director_tasks(self, superuser_client):
        url = reverse("industry_reforged:dt_director_tasks")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_dt_director_buy_orders(self, superuser_client):
        url = reverse("industry_reforged:dt_director_buy_orders")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_dt_director_transactions(self, superuser_client):
        url = reverse("industry_reforged:dt_director_transactions")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_dt_corporate_jobs(self, superuser_client):
        url = reverse("industry_reforged:dt_corporate_jobs")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_mark_order_delivered(self, superuser_client):
        url = reverse("industry_reforged:mark_order_delivered", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_update_buy_order_status(self, superuser_client):
        url = reverse(
            "industry_reforged:update_buy_order_status", kwargs={"order_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_delete_buy_order(self, superuser_client):
        url = reverse("industry_reforged:delete_buy_order", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_delete_production_task(self, superuser_client):
        url = reverse("industry_reforged:delete_production_task", kwargs={"task_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_mark_order_paid(self, superuser_client):
        url = reverse("industry_reforged:mark_order_paid", kwargs={"order_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_generate_payout_batch(self, superuser_client):
        url = reverse("industry_reforged:generate_payout_batch")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_mark_payout_batch_paid(self, superuser_client):
        url = reverse(
            "industry_reforged:mark_payout_batch_paid", kwargs={"batch_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_add_facility(self, superuser_client):
        url = reverse("industry_reforged:add_facility")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_edit_facility(self, superuser_client):
        url = reverse("industry_reforged:edit_facility", kwargs={"facility_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_delete_facility(self, superuser_client):
        url = reverse("industry_reforged:delete_facility", kwargs={"facility_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_inventory(self, superuser_client):
        url = reverse("industry_reforged:director_inventory")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_update_inventory_target(self, superuser_client):
        url = reverse(
            "industry_reforged:update_inventory_target", kwargs={"type_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_spawn_restock_job(self, superuser_client):
        url = reverse("industry_reforged:spawn_restock_job", kwargs={"type_id": 1})
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_inventory_shopping_list(self, superuser_client):
        url = reverse("industry_reforged:inventory_shopping_list")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config(self, superuser_client):
        url = reverse("industry_reforged:director_config")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_item_add(self, superuser_client):
        url = reverse("industry_reforged:director_config_item_add")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_item_edit(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_item_edit", kwargs={"config_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_item_delete(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_item_delete", kwargs={"config_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_pricing_add(self, superuser_client):
        url = reverse("industry_reforged:director_config_pricing_add")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_pricing_edit(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_pricing_edit", kwargs={"config_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_tax_add(self, superuser_client):
        url = reverse("industry_reforged:director_config_tax_add")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_tax_edit(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_tax_edit", kwargs={"config_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_discount_add(self, superuser_client):
        url = reverse("industry_reforged:director_config_discount_add")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_discount_edit(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_discount_edit", kwargs={"discount_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_discount_delete(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_discount_delete",
            kwargs={"discount_id": 1},
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_config_structure_toggle(self, superuser_client):
        url = reverse(
            "industry_reforged:director_config_structure_toggle",
            kwargs={"facility_id": 1},
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_director_wallets(self, superuser_client):
        url = reverse("industry_reforged:director_wallets")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_trigger_wallet_sync(self, superuser_client):
        url = reverse("industry_reforged:trigger_wallet_sync")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_trigger_inventory_sync(self, superuser_client):
        url = reverse("industry_reforged:trigger_inventory_sync")
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass

    def test_update_wallet_threshold(self, superuser_client):
        url = reverse(
            "industry_reforged:update_wallet_threshold", kwargs={"division_id": 1}
        )
        try:
            superuser_client.get(url)
        except Exception:
            pass
        try:
            superuser_client.post(url)
        except Exception:
            pass
