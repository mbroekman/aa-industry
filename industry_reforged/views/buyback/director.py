"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from ...forms import BuybackProgramForm, BuybackWatchlistItemForm
from ...models import (
    BuybackContract,
    BuybackProgram,
    BuybackWatchlistItem,
    LedgerTransaction,
)
from ...tasks.utils import notify_discord_user


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_program_edit(
    request: WSGIRequest, program_id: int = None
) -> HttpResponse:
    if program_id:
        instance = get_object_or_404(BuybackProgram, id=program_id)
    else:
        instance = BuybackProgram()

    if request.method == "POST":
        form = BuybackProgramForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Buyback program saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#buyback")
    else:
        form = BuybackProgramForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": (
                _("Edit Buyback Program") if program_id else _("Add Buyback Program")
            ),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#buyback",
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_program_delete(
    request: WSGIRequest, program_id: int
) -> HttpResponse:
    program = get_object_or_404(BuybackProgram, id=program_id)
    name = program.name
    program.delete()
    messages.success(request, _("Buyback program '%(name)s' deleted.") % {"name": name})
    return redirect(reverse("industry_reforged:director_config") + "#buyback")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_watchlist_edit(
    request: WSGIRequest, item_id: int = None
) -> HttpResponse:
    if item_id:
        instance = get_object_or_404(BuybackWatchlistItem, id=item_id)
    else:
        instance = BuybackWatchlistItem()

    if request.method == "POST":
        form = BuybackWatchlistItemForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Watchlist item saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#buyback")
    else:
        form = BuybackWatchlistItemForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": _("Edit Watchlist Item") if item_id else _("Add Watchlist Item"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#buyback",
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_watchlist_delete(
    request: WSGIRequest, item_id: int
) -> HttpResponse:
    item = get_object_or_404(BuybackWatchlistItem, id=item_id)
    item.delete()
    messages.success(request, _("Watchlist item deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#buyback")


@login_required
@permission_required("industry_reforged.corp_access")
def director_buyback_review(request: WSGIRequest) -> HttpResponse:
    """Queue of FLAGGED/MATCHED contracts awaiting a payout decision."""
    contracts = (
        BuybackContract.objects.filter(status__in=["FLAGGED", "MATCHED"])
        .select_related("program", "character")
        .prefetch_related("items__eve_type")
        .order_by("-created_at")
    )
    context = {
        "title": _("Buyback Review Queue"),
        "contracts": contracts,
    }
    return render(request, "industry_reforged/buyback/director_review.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def director_buyback_contract_resolve(
    request: WSGIRequest, tracking_number: str
) -> HttpResponse:
    """POST action: accept_and_pay creates the payout LedgerTransaction and marks
    PAID; reject marks REJECTED and notifies the member. Never re-processes an
    already-terminal contract, so a double-click can never double-pay."""
    contract = get_object_or_404(BuybackContract, tracking_number=tracking_number)

    if request.method == "POST" and contract.status in ("MATCHED", "FLAGGED"):
        action = request.POST.get("action")
        if action == "accept_and_pay":
            LedgerTransaction.objects.create(
                transaction_type="BUYBACK_PAYOUT",
                amount=contract.quoted_price,
                character=contract.character,
                director=request.user,
                reference=contract.tracking_number,
                notes="Buyback payout",
                buyback_contract=contract,
            )
            contract.status = "PAID"
            contract.save(update_fields=["status"])
            messages.success(
                request,
                _("Contract %(tracking_number)s paid out.")
                % {"tracking_number": contract.tracking_number},
            )
        elif action == "reject":
            reason = request.POST.get("reason", "").strip()
            contract.status = "REJECTED"
            if reason:
                contract.flag_notes = reason
            contract.save(update_fields=["status", "flag_notes"])
            if contract.character:
                notify_discord_user(
                    contract.character,
                    f"Your buyback contract {contract.tracking_number} was rejected. {reason}".strip(),
                )
            messages.success(
                request,
                _("Contract %(tracking_number)s rejected.")
                % {"tracking_number": contract.tracking_number},
            )
    elif request.method == "POST":
        messages.error(request, _("This contract has already been resolved."))

    return redirect("industry_reforged:director_buyback_review")
