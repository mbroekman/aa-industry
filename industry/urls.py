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
]
