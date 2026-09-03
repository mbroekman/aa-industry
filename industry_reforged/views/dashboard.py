"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from ..forms import UserPIConfigForm
from ..models import (
    CharacterIndustryJob,
    CharacterPlanet,
    CorporationIndustryJob,
    MemberOrder,
    UserPIConfig,
)


@login_required
@permission_required("industry_reforged.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """
    return personal_dashboard(request)


@login_required
@permission_required("industry_reforged.basic_access")
def personal_dashboard(request: WSGIRequest) -> HttpResponse:
    """Personal Dashboard View"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    jobs_qs = CharacterIndustryJob.objects.filter(
        character_id__in=user_characters
    ).select_related("blueprint_type", "product_type", "character")
    jobs = list(jobs_qs)
    for j in jobs:
        j.job_type = "Personal"

    corp_jobs_qs = CorporationIndustryJob.objects.filter(
        installer_id__in=user_characters
    ).select_related("blueprint_type", "product_type", "installer")
    corp_jobs = list(corp_jobs_qs)
    for j in corp_jobs:
        j.character = j.installer
        j.job_type = "Corp"

    jobs.extend(corp_jobs)

    # Sort descending by end_date, putting jobs without end_date at the end
    # Standard Library
    import datetime

    # Django
    from django.utils import timezone

    def get_sort_key(j):
        return j.end_date or timezone.make_aware(datetime.datetime.min)

    jobs.sort(key=get_sort_key, reverse=True)

    active_statuses = ["active", "paused", "ready"]

    manufacturing_activities = [1, 9]
    research_activities = [3, 4, 5, 8]

    active_jobs = [
        j
        for j in jobs
        if j.status in active_statuses and j.activity_id in manufacturing_activities
    ]
    history_jobs = [
        j
        for j in jobs
        if j.status not in active_statuses and j.activity_id in manufacturing_activities
    ]

    active_research_jobs = [
        j
        for j in jobs
        if j.status in active_statuses and j.activity_id in research_activities
    ]
    history_research_jobs = [
        j
        for j in jobs
        if j.status not in active_statuses and j.activity_id in research_activities
    ]

    planets = list(
        CharacterPlanet.objects.filter(character_id__in=user_characters)
        .select_related("character", "planet_type", "eve_system", "eve_planet")
        .prefetch_related("pins", "pins__type", "pins__product_type")
        .order_by("character__character_name", "planet_id")
    )

    expired_chars = set()
    full_storage_chars = set()
    deficit_chars = set()
    depleted_factory_chars = set()

    for planet in planets:
        if planet.has_expired_extractors:
            expired_chars.add(planet.character_id)
        if planet.has_full_storage:
            full_storage_chars.add(planet.character_id)
        if planet.has_extraction_deficit:
            deficit_chars.add(planet.character_id)
        if planet.is_factory_depleted:
            depleted_factory_chars.add(planet.character_id)

    for planet in planets:
        planet.character_has_expired_extractors = planet.character_id in expired_chars
        planet.character_has_full_storage = planet.character_id in full_storage_chars
        planet.character_has_extraction_deficit = planet.character_id in deficit_chars
        planet.character_has_depleted_factories = (
            planet.character_id in depleted_factory_chars
        )
        planet.character_needs_attention = (
            planet.character_has_expired_extractors
            or planet.character_has_full_storage
            or planet.character_has_extraction_deficit
            or planet.character_has_depleted_factories
        )

    pi_config, _created = UserPIConfig.objects.get_or_create(user=request.user)

    if request.method == "POST" and "update_pi_config" in request.POST:
        pi_config_form = UserPIConfigForm(request.POST, instance=pi_config)
        if pi_config_form.is_valid():
            pi_config_form.save()
            messages.success(request, _("PI configuration updated."))
            return redirect(
                reverse("industry_reforged:personal_dashboard") + "#pi-pane"
            )
    else:
        pi_config_form = UserPIConfigForm(instance=pi_config)

    context = {
        "active_jobs": active_jobs,
        "history_jobs": history_jobs,
        "active_research_jobs": active_research_jobs,
        "history_research_jobs": history_research_jobs,
        "planets": planets,
        "pi_config_form": pi_config_form,
        "title": "Personal Industry Dashboard",
    }
    return render(request, "industry_reforged/personal_dashboard.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def corporate_dashboard(request: WSGIRequest) -> HttpResponse:
    """Corporate Dashboard View"""

    active_jobs = []
    history_jobs = []

    context = {
        "active_jobs": active_jobs,
        "history_jobs": history_jobs,
        "title": "Corporate Industry Dashboard",
    }
    return render(request, "industry_reforged/corporate_dashboard.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
def orders_dashboard(request: WSGIRequest) -> HttpResponse:
    """Member Orders Dashboard"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    orders = MemberOrder.objects.filter(
        character_id__in=user_characters, parent_order__isnull=True
    ).order_by("-created_at")

    context = {"orders": orders, "title": "My Orders"}
    return render(request, "industry_reforged/orders_dashboard.html", context)
