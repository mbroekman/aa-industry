"""App URLs"""

# Django
from django.urls import path

# AA Industry App
from industry_reforged.views import (
    api,
    dashboard,
    director,
    facilities,
    industrialist,
    orders,
)

app_name: str = "industry_reforged"  # pylint: disable=invalid-name

urlpatterns = [
    path("", dashboard.index, name="index"),
    path("personal/", dashboard.personal_dashboard, name="personal_dashboard"),
    path("corporate/", dashboard.corporate_dashboard, name="corporate_dashboard"),
    path("add-personal-token/", api.add_personal_token, name="add_personal_token"),
    path("add-corporate-token/", api.add_corporate_token, name="add_corporate_token"),
    path("personal/sync-pi/", api.trigger_pi_sync, name="trigger_pi_sync"),
    path("orders/", dashboard.orders_dashboard, name="orders_dashboard"),
    path("orders/create/", orders.create_order, name="create_order"),
    path("orders/shopping-list/", orders.shopping_list, name="shopping_list"),
    path("orders/<int:order_id>/", orders.view_quote, name="view_quote"),
    path("orders/<int:order_id>/accept/", orders.accept_quote, name="accept_quote"),
    path("orders/<int:order_id>/reject/", orders.reject_quote, name="reject_quote"),
    path(
        "orders/<int:order_id>/htmx-update-facility/",
        orders.htmx_update_quote_facility,
        name="htmx_update_quote_facility",
    ),
    path(
        "orders/<int:order_id>/update-me-overrides/",
        orders.update_quote_me_overrides,
        name="update_quote_me_overrides",
    ),
    path("orders/<int:order_id>/delete/", orders.delete_order, name="delete_order"),
    path(
        "orders/<int:order_id>/provide-quote/",
        orders.provide_quote,
        name="provide_quote",
    ),
    path(
        "orders/<int:order_id>/split/",
        orders.split_order,
        name="split_order",
    ),
    path(
        "orders/<int:order_id>/split-component/",
        orders.split_bom_component,
        name="split_bom_component",
    ),
    path(
        "industrialist/",
        industrialist.industrialist_dashboard,
        name="industrialist_dashboard",
    ),
    path(
        "industrialist/claim/<int:task_id>/",
        industrialist.claim_task,
        name="claim_task",
    ),
    path(
        "industrialist/unclaim/<int:task_id>/",
        industrialist.unclaim_task,
        name="unclaim_task",
    ),
    path(
        "industrialist/bulk-claim/",
        industrialist.bulk_claim_tasks,
        name="bulk_claim_tasks",
    ),
    path(
        "industrialist/bulk-unclaim/",
        industrialist.bulk_unclaim_tasks,
        name="bulk_unclaim_tasks",
    ),
    path(
        "industrialist/complete/<int:task_id>/",
        industrialist.complete_task,
        name="complete_task",
    ),
    path(
        "industrialist/bulk-complete/",
        industrialist.bulk_complete_tasks,
        name="bulk_complete_tasks",
    ),
    path(
        "industrialist/leaderboard/",
        industrialist.industrialist_leaderboard,
        name="industrialist_leaderboard",
    ),
    path("director/", director.director_dashboard, name="director_dashboard"),
    path(
        "director/order/<int:order_id>/delivered/",
        director.mark_order_delivered,
        name="mark_order_delivered",
    ),
    path(
        "director/buy-order/<int:order_id>/update-status/",
        director.update_buy_order_status,
        name="update_buy_order_status",
    ),
    path(
        "director/buy-order/<int:order_id>/delete/",
        director.delete_buy_order,
        name="delete_buy_order",
    ),
    path(
        "director/task/<int:task_id>/delete/",
        director.delete_production_task,
        name="delete_production_task",
    ),
    path(
        "director/order/<int:order_id>/paid/",
        director.mark_order_paid,
        name="mark_order_paid",
    ),
    path(
        "director/payout/generate/",
        director.generate_payout_batch,
        name="generate_payout_batch",
    ),
    path(
        "director/payout/batch/<int:batch_id>/paid/",
        director.mark_payout_batch_paid,
        name="mark_payout_batch_paid",
    ),
    path("director/facilities/add/", facilities.add_facility, name="add_facility"),
    path(
        "director/facilities/<int:facility_id>/edit/",
        facilities.edit_facility,
        name="edit_facility",
    ),
    path(
        "director/facilities/<int:facility_id>/delete/",
        facilities.delete_facility,
        name="delete_facility",
    ),
    path("director/inventory/", director.director_inventory, name="director_inventory"),
    path(
        "director/inventory/target/<int:type_id>/",
        director.update_inventory_target,
        name="update_inventory_target",
    ),
    path(
        "director/inventory/spawn/<int:type_id>/",
        director.spawn_restock_job,
        name="spawn_restock_job",
    ),
    path(
        "director/inventory/shopping-list/",
        director.inventory_shopping_list,
        name="inventory_shopping_list",
    ),
    path("director/config/", director.director_config, name="director_config"),
    path(
        "director/config/item/add/",
        director.director_config_item_edit,
        name="director_config_item_add",
    ),
    path(
        "director/config/item/<int:config_id>/",
        director.director_config_item_edit,
        name="director_config_item_edit",
    ),
    path(
        "director/config/item/<int:config_id>/delete/",
        director.director_config_item_delete,
        name="director_config_item_delete",
    ),
    path(
        "director/config/pricing/add/",
        director.director_config_pricing_edit,
        name="director_config_pricing_add",
    ),
    path(
        "director/config/pricing/<int:config_id>/edit/",
        director.director_config_pricing_edit,
        name="director_config_pricing_edit",
    ),
    path(
        "director/config/tax/add/",
        director.director_config_tax_edit,
        name="director_config_tax_add",
    ),
    path(
        "director/config/tax/<int:config_id>/edit/",
        director.director_config_tax_edit,
        name="director_config_tax_edit",
    ),
    path(
        "director/config/discount/add/",
        director.director_config_discount_edit,
        name="director_config_discount_add",
    ),
    path(
        "director/config/discount/<int:discount_id>/",
        director.director_config_discount_edit,
        name="director_config_discount_edit",
    ),
    path(
        "director/config/discount/<int:discount_id>/delete/",
        director.director_config_discount_delete,
        name="director_config_discount_delete",
    ),
    path(
        "director/config/structure/<int:facility_id>/toggle/",
        director.director_config_structure_toggle,
        name="director_config_structure_toggle",
    ),
    path(
        "director/wallets/",
        director.director_wallets,
        name="director_wallets",
    ),
    path(
        "director/wallets/sync/",
        api.trigger_wallet_sync,
        name="trigger_wallet_sync",
    ),
    path(
        "director/sync-inventory/",
        api.trigger_inventory_sync,
        name="trigger_inventory_sync",
    ),
    path(
        "director/wallets/update-threshold/<int:division_id>/",
        director.update_wallet_threshold,
        name="update_wallet_threshold",
    ),
]
