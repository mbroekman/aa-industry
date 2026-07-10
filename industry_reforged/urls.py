"""App URLs"""

# Django
from django.urls import path

# AA Industry App
from industry_reforged import views

app_name: str = "industry_reforged"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.index, name="index"),
    path("personal/", views.personal_dashboard, name="personal_dashboard"),
    path("corporate/", views.corporate_dashboard, name="corporate_dashboard"),
    path("add-personal-token/", views.add_personal_token, name="add_personal_token"),
    path("add-corporate-token/", views.add_corporate_token, name="add_corporate_token"),
    path("personal/sync-pi/", views.trigger_pi_sync, name="trigger_pi_sync"),
    path("orders/", views.orders_dashboard, name="orders_dashboard"),
    path("orders/create/", views.create_order, name="create_order"),
    path("orders/shopping-list/", views.shopping_list, name="shopping_list"),
    path("orders/<int:order_id>/", views.view_quote, name="view_quote"),
    path("orders/<int:order_id>/accept/", views.accept_quote, name="accept_quote"),
    path("orders/<int:order_id>/reject/", views.reject_quote, name="reject_quote"),
    path(
        "orders/<int:order_id>/htmx-update-facility/",
        views.htmx_update_quote_facility,
        name="htmx_update_quote_facility",
    ),
    path("orders/<int:order_id>/delete/", views.delete_order, name="delete_order"),
    path(
        "orders/<int:order_id>/provide-quote/",
        views.provide_quote,
        name="provide_quote",
    ),
    path(
        "industrialist/", views.industrialist_dashboard, name="industrialist_dashboard"
    ),
    path("industrialist/claim/<int:task_id>/", views.claim_task, name="claim_task"),
    path(
        "industrialist/unclaim/<int:task_id>/", views.unclaim_task, name="unclaim_task"
    ),
    path("industrialist/bulk-claim/", views.bulk_claim_tasks, name="bulk_claim_tasks"),
    path(
        "industrialist/bulk-unclaim/",
        views.bulk_unclaim_tasks,
        name="bulk_unclaim_tasks",
    ),
    path(
        "industrialist/complete/<int:task_id>/",
        views.complete_task,
        name="complete_task",
    ),
    path(
        "industrialist/bulk-complete/",
        views.bulk_complete_tasks,
        name="bulk_complete_tasks",
    ),
    path(
        "industrialist/leaderboard/",
        views.industrialist_leaderboard,
        name="industrialist_leaderboard",
    ),
    path("director/", views.director_dashboard, name="director_dashboard"),
    path(
        "director/order/<int:order_id>/deliver/",
        views.mark_order_delivered,
        name="mark_order_delivered",
    ),
    path(
        "director/order/<int:order_id>/paid/",
        views.mark_order_paid,
        name="mark_order_paid",
    ),
    path(
        "director/payout/generate/",
        views.generate_payout_batch,
        name="generate_payout_batch",
    ),
    path(
        "director/payout/batch/<int:batch_id>/paid/",
        views.mark_payout_batch_paid,
        name="mark_payout_batch_paid",
    ),
    path("director/facilities/add/", views.add_facility, name="add_facility"),
    path(
        "director/facilities/<int:facility_id>/edit/",
        views.edit_facility,
        name="edit_facility",
    ),
    path(
        "director/facilities/<int:facility_id>/delete/",
        views.delete_facility,
        name="delete_facility",
    ),
    path("director/inventory/", views.director_inventory, name="director_inventory"),
    path("director/config/", views.director_config, name="director_config"),
    path(
        "director/config/item/add/",
        views.director_config_item_edit,
        name="director_config_item_add",
    ),
    path(
        "director/config/item/<int:config_id>/",
        views.director_config_item_edit,
        name="director_config_item_edit",
    ),
    path(
        "director/config/item/<int:config_id>/delete/",
        views.director_config_item_delete,
        name="director_config_item_delete",
    ),
    path(
        "director/config/pricing/",
        views.director_config_pricing_edit,
        name="director_config_pricing_edit",
    ),
    path(
        "director/config/tax/",
        views.director_config_tax_edit,
        name="director_config_tax_edit",
    ),
    path(
        "director/config/discount/add/",
        views.director_config_discount_edit,
        name="director_config_discount_add",
    ),
    path(
        "director/config/discount/<int:discount_id>/",
        views.director_config_discount_edit,
        name="director_config_discount_edit",
    ),
    path(
        "director/config/discount/<int:discount_id>/delete/",
        views.director_config_discount_delete,
        name="director_config_discount_delete",
    ),
    path(
        "director/config/structure/<int:facility_id>/toggle/",
        views.director_config_structure_toggle,
        name="director_config_structure_toggle",
    ),
    path(
        "director/wallets/",
        views.director_wallets,
        name="director_wallets",
    ),
    path(
        "director/wallets/sync/",
        views.trigger_wallet_sync,
        name="trigger_wallet_sync",
    ),
    path(
        "director/sync-inventory/",
        views.trigger_inventory_sync,
        name="trigger_inventory_sync",
    ),
]
