"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

from ...forms import (
    BuybackItemRuleForm,
    BuybackProgramForm,
    BuybackStaticPriceForm,
    BuybackWatchlistItemForm,
)
from ...models import (
    BuybackContract,
    BuybackItemRule,
    BuybackProgram,
    BuybackStaticPrice,
    BuybackUntrackedContract,
    BuybackWatchlistItem,
)
from ...utils import buyback_notify


def _director_corporation(request: WSGIRequest):
    """Directors only ever manage their own main character's corporation."""
    main = request.user.profile.main_character
    if not main:
        return None
    return EveCorporationInfo.objects.filter(corporation_id=main.corporation_id).first()


def _no_corporation(request: WSGIRequest) -> HttpResponse:
    messages.error(request, _("You are not part of a corporation."))
    return redirect("industry_reforged:index")


def _back_to_config() -> HttpResponse:
    return redirect(reverse("industry_reforged:director_config") + "#buyback")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_program_edit(
    request: WSGIRequest, program_id: int = None
) -> HttpResponse:
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    if program_id:
        instance = get_object_or_404(
            BuybackProgram, id=program_id, corporation=corporation
        )
    else:
        instance = BuybackProgram(corporation=corporation)

    if request.method == "POST":
        form = BuybackProgramForm(
            request.POST, instance=instance, corporation=corporation
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Buyback program saved successfully."))
            return _back_to_config()
    else:
        form = BuybackProgramForm(instance=instance, corporation=corporation)

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
@require_POST
def director_config_buyback_program_delete(
    request: WSGIRequest, program_id: int
) -> HttpResponse:
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    program = get_object_or_404(BuybackProgram, id=program_id, corporation=corporation)
    if program.contracts.exists():
        messages.error(
            request,
            _(
                "Buyback program '%(name)s' has contracts and can't be deleted. "
                "Deactivate it instead."
            )
            % {"name": program.name},
        )
        return _back_to_config()

    name = program.name
    program.delete()
    messages.success(request, _("Buyback program '%(name)s' deleted.") % {"name": name})
    return _back_to_config()


def _edit_program_child(request, model, form_class, obj_id, titles, saved_message):
    """Add/edit view for a watchlist entry, item rule or static price, limited
    to programs of the director's own corporation."""
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    if obj_id:
        instance = get_object_or_404(model, id=obj_id, program__corporation=corporation)
    else:
        instance = model()

    if request.method == "POST":
        form = form_class(request.POST, instance=instance, corporation=corporation)
        if form.is_valid():
            form.save()
            messages.success(request, saved_message)
            return _back_to_config()
    else:
        form = form_class(instance=instance, corporation=corporation)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": titles[1] if obj_id else titles[0],
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#buyback",
        },
    )


def _delete_program_child(request, model, obj_id, deleted_message):
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    get_object_or_404(model, id=obj_id, program__corporation=corporation).delete()
    messages.success(request, deleted_message)
    return _back_to_config()


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_watchlist_edit(
    request: WSGIRequest, item_id: int = None
) -> HttpResponse:
    return _edit_program_child(
        request,
        BuybackWatchlistItem,
        BuybackWatchlistItemForm,
        item_id,
        (_("Add Watchlist Item"), _("Edit Watchlist Item")),
        _("Watchlist item saved successfully."),
    )


@login_required
@permission_required("industry_reforged.corp_access")
@require_POST
def director_config_buyback_watchlist_delete(
    request: WSGIRequest, item_id: int
) -> HttpResponse:
    return _delete_program_child(
        request, BuybackWatchlistItem, item_id, _("Watchlist item deleted.")
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_rule_edit(
    request: WSGIRequest, rule_id: int = None
) -> HttpResponse:
    return _edit_program_child(
        request,
        BuybackItemRule,
        BuybackItemRuleForm,
        rule_id,
        (_("Add Item Rule"), _("Edit Item Rule")),
        _("Item rule saved."),
    )


@login_required
@permission_required("industry_reforged.corp_access")
@require_POST
def director_config_buyback_rule_delete(
    request: WSGIRequest, rule_id: int
) -> HttpResponse:
    return _delete_program_child(
        request, BuybackItemRule, rule_id, _("Item rule deleted.")
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_buyback_static_price_edit(
    request: WSGIRequest, price_id: int = None
) -> HttpResponse:
    return _edit_program_child(
        request,
        BuybackStaticPrice,
        BuybackStaticPriceForm,
        price_id,
        (_("Add Fixed Price"), _("Edit Fixed Price")),
        _("Fixed price saved."),
    )


@login_required
@permission_required("industry_reforged.corp_access")
@require_POST
def director_config_buyback_static_price_delete(
    request: WSGIRequest, price_id: int
) -> HttpResponse:
    return _delete_program_child(
        request, BuybackStaticPrice, price_id, _("Fixed price deleted.")
    )


@login_required
@permission_required("industry_reforged.corp_access")
@require_POST
def director_buyback_load_market_groups(request: WSGIRequest) -> HttpResponse:
    """Queue loading every EVE market group, needed to pick one for a rule."""
    from ...tasks.buyback import buyback_load_market_groups

    buyback_load_market_groups.delay()
    messages.success(
        request,
        _(
            "Loading market groups in the background. This takes a few minutes; "
            "reload this page afterwards."
        ),
    )
    return _back_to_config()


@login_required
@permission_required("industry_reforged.corp_access")
def director_buyback_review(request: WSGIRequest) -> HttpResponse:
    """Queue of FLAGGED/MATCHED contracts awaiting a payout decision."""
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    contracts = (
        BuybackContract.objects.filter(
            status__in=["FLAGGED", "MATCHED"], program__corporation=corporation
        )
        .select_related("program", "character")
        .prefetch_related("items__eve_type")
        .order_by("-created_at")
    )
    untracked_contracts = BuybackUntrackedContract.objects.filter(
        program__corporation=corporation, dismissed=False
    ).select_related("program")
    context = {
        "title": _("Buyback Review Queue"),
        "contracts": contracts,
        "untracked_contracts": untracked_contracts,
    }
    return render(request, "industry_reforged/buyback/director_review.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
@require_POST
def director_buyback_untracked_dismiss(
    request: WSGIRequest, untracked_id: int
) -> HttpResponse:
    """Mark a suspicious contract as handled; it stays recorded so the poller
    never reports the same in-game contract again."""
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    untracked = get_object_or_404(
        BuybackUntrackedContract, id=untracked_id, program__corporation=corporation
    )
    untracked.dismissed = True
    untracked.save(update_fields=["dismissed"])
    messages.success(request, _("Suspicious contract dismissed."))
    return redirect("industry_reforged:director_buyback_review")


@login_required
@permission_required("industry_reforged.corp_access")
def director_buyback_contract_resolve(
    request: WSGIRequest, tracking_number: str
) -> HttpResponse:
    """POST action: accept_and_pay records the payout (once) and marks PAID;
    reject marks REJECTED and notifies the member. Never re-processes an
    already-terminal contract, so a double-click can never double-pay."""
    corporation = _director_corporation(request)
    if not corporation:
        return _no_corporation(request)

    contract = get_object_or_404(
        BuybackContract,
        tracking_number=tracking_number,
        program__corporation=corporation,
    )

    if request.method == "POST" and contract.status in ("MATCHED", "FLAGGED"):
        action = request.POST.get("action")
        if action == "accept_and_pay":
            if contract.mark_paid(director=request.user):
                buyback_notify.notify_seller(
                    contract,
                    f"Buyback contract {contract.tracking_number}",
                    f"Your buyback contract {contract.tracking_number} was paid out.",
                    "success",
                )
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
            contract.save(update_fields=["status", "flag_notes", "updated_at"])
            buyback_notify.notify_seller(
                contract,
                f"Buyback contract {contract.tracking_number}",
                f"Your buyback contract {contract.tracking_number} was rejected. {reason}".strip(),
                "danger",
            )
            messages.success(
                request,
                _("Contract %(tracking_number)s rejected.")
                % {"tracking_number": contract.tracking_number},
            )
    elif request.method == "POST":
        messages.error(request, _("This contract has already been resolved."))

    return redirect("industry_reforged:director_buyback_review")
