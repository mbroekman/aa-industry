"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from esi.decorators import token_required

from ..models import (
    CorporationSyncConfig,
)
from ..tasks.inventory import task_sync_corp_inventory
from ..tasks.pi import update_character_pi
from ..tasks.wallets import task_sync_corp_wallets


@login_required
@token_required(
    scopes=["esi-industry.read_character_jobs.v1", "esi-planets.manage_planets.v1"]
)
def add_personal_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a personal token"""
    return redirect("industry_reforged:personal_dashboard")


@login_required
@token_required(
    scopes=[
        "esi-industry.read_corporation_jobs.v1",
        "esi-assets.read_corporation_assets.v1",
        "esi-universe.read_structures.v1",
        "esi-corporations.read_structures.v1",
        "esi-corporations.read_divisions.v1",
        "esi-wallet.read_corporation_wallets.v1",
    ]
)
def add_corporate_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a corporate token and automatically configure sync."""
    character = EveCharacter.objects.filter(character_id=token.character_id).first()
    if character and character.corporation:
        CorporationSyncConfig.objects.update_or_create(
            corporation=character.corporation, defaults={"sync_character": character}
        )

    # After granting, redirect back to the page the user came from or the director dashboard
    referer = request.headers.get("referer")
    if referer and "director" in referer:
        return redirect("industry_reforged:director_config")
    return redirect("industry_reforged:corporate_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def trigger_pi_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger PI sync for all characters of the user"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    for char_id in user_characters:
        update_character_pi.delay(character_id=char_id)

    messages.success(
        request,
        _(
            "Planetary Interaction sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:personal_dashboard")


@login_required
@permission_required("industry_reforged.corp_access")
def trigger_inventory_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger inventory sync for all configured corporations"""

    task_sync_corp_inventory.delay()
    messages.success(
        request,
        _(
            "Corporate Inventory sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:director_inventory")


@login_required
@permission_required("industry_reforged.corp_access")
def trigger_wallet_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger wallet sync for all configured corporations"""

    task_sync_corp_wallets.delay()
    messages.success(
        request,
        _(
            "Corporate Wallet sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:director_wallets")
