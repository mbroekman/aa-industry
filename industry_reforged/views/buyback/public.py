"""Login-free buyback views for programs a director marked public.

These are listed in auth_hooks' UrlHook excluded_views and only work when the
host sets APPS_WITH_PUBLIC_VIEWS = ["industry_reforged"]. Without that, Alliance
Auth still requires a login for them, which is the safe default.
"""

# Django
from django.contrib.auth.decorators import login_not_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from ...models import BuybackContract, BuybackProgram
from .member import run_calculator


@login_not_required
def buyback_public_calculator(request: WSGIRequest, program_id: int) -> HttpResponse:
    program = get_object_or_404(
        BuybackProgram.objects.filter(is_active=True, is_public=True), id=program_id
    )
    user = request.user
    character = (
        user.profile.main_character
        if user.is_authenticated and hasattr(user, "profile")
        else None
    )
    return run_calculator(
        request,
        BuybackProgram.objects.filter(pk=program.pk)
        .select_related("corporation", "recipient_character")
        .prefetch_related("facilities", "known_locations"),
        {"title": program.name},
        character=character,
        public=True,
    )


@login_not_required
def buyback_public_contract(request: WSGIRequest, tracking_number: str) -> HttpResponse:
    """Status and in-game instructions for a contract from a public calculator.
    The random tracking number is what grants access, like an order link."""
    contract = get_object_or_404(
        BuybackContract.objects.select_related("program__corporation"),
        tracking_number=tracking_number,
        program__is_public=True,
    )
    context = {
        "title": _("Buyback Contract %(tracking_number)s")
        % {"tracking_number": contract.tracking_number},
        "contract": contract,
        "items": contract.items.select_related("eve_type"),
        "public": True,
    }
    return render(request, "industry_reforged/buyback/contract_detail.html", context)
