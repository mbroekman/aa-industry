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
        "orders/<int:order_id>/provide-quote/",
        views.provide_quote,
        name="provide_quote",
    ),
    path(
        "industrialist/", views.industrialist_dashboard, name="industrialist_dashboard"
    ),
    path("industrialist/claim/<int:task_id>/", views.claim_task, name="claim_task"),
    path(
        "industrialist/complete/<int:task_id>/",
        views.complete_task,
        name="complete_task",
    ),
    path(
        "industrialist/leaderboard/",
        views.industrialist_leaderboard,
        name="industrialist_leaderboard",
    ),
    path("director/", views.director_dashboard, name="director_dashboard"),
    path("director/inventory/", views.director_inventory, name="director_inventory"),
    path("director/config/", views.director_config, name="director_config"),
    path(
        "director/config/discover/",
        views.director_discover_hangars,
        name="director_discover_hangars",
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
