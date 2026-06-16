"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render

# Alliance Auth
from esi.decorators import token_required

from .models import CharacterIndustryJob, CharacterPlanet, CorporationIndustryJob
from .tasks import update_character_pi


@login_required
@permission_required("industry.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """
    return personal_dashboard(request)


@login_required
@permission_required("industry.basic_access")
def personal_dashboard(request: WSGIRequest) -> HttpResponse:
    """Personal Dashboard View"""
    # Fetch all jobs for the current user's characters
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    jobs = CharacterIndustryJob.objects.filter(
        character_id__in=user_characters
    ).select_related("blueprint_type", "product_type", "character")

    # Fetch PI Planets
    planets = (
        CharacterPlanet.objects.filter(character_id__in=user_characters)
        .select_related("character", "planet_type")
        .prefetch_related("pins", "pins__type", "pins__product_type")
    )

    context = {"jobs": jobs, "planets": planets, "title": "Personal Industry Dashboard"}
    return render(request, "industry/personal_dashboard.html", context)


@login_required
@permission_required("industry.corp_access")
def corporate_dashboard(request: WSGIRequest) -> HttpResponse:
    """Corporate Dashboard View"""
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    jobs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps
    ).select_related("blueprint_type", "product_type", "installer", "corporation")

    context = {"jobs": jobs, "title": "Corporate Industry Dashboard"}
    return render(request, "industry/corporate_dashboard.html", context)


@login_required
@token_required(
    scopes=["esi-industry.read_character_jobs.v1", "esi-planets.manage_planets.v1"]
)
def add_personal_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a personal token"""
    return redirect("industry:personal_dashboard")


@login_required
@token_required(scopes=["esi-industry.read_corporation_jobs.v1"])
def add_corporate_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a corporate token"""
    return redirect("industry:corporate_dashboard")


@login_required
@permission_required("industry.basic_access")
def trigger_pi_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger PI sync for all characters of the user"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    for char_id in user_characters:
        update_character_pi.delay(character_id=char_id)

    messages.success(
        request,
        "Planetary Interaction sync has been queued in the background. Please refresh in a few minutes.",
    )
    return redirect("industry:personal_dashboard")
