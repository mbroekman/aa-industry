"""App URLs"""

# Django
from django.urls import path

# AA Industry App
from industry import views

app_name: str = "industry"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.index, name="index"),
    path("personal/", views.personal_dashboard, name="personal_dashboard"),
    path("corporate/", views.corporate_dashboard, name="corporate_dashboard"),
    path("add-personal-token/", views.add_personal_token, name="add_personal_token"),
    path("add-corporate-token/", views.add_corporate_token, name="add_corporate_token"),
    path("personal/sync-pi/", views.trigger_pi_sync, name="trigger_pi_sync"),
    path("orders/", views.orders_dashboard, name="orders_dashboard"),
    path("orders/create/", views.create_order, name="create_order"),
    path("orders/<int:order_id>/", views.view_quote, name="view_quote"),
    path("orders/<int:order_id>/accept/", views.accept_quote, name="accept_quote"),
    path("orders/<int:order_id>/reject/", views.reject_quote, name="reject_quote"),
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
]
