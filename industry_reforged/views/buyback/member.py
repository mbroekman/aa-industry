"""App Views"""

# Standard Library
from decimal import Decimal, InvalidOperation

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from ...models import (
    BuybackContract,
    BuybackContractItem,
    BuybackProgram,
    BuybackUserSettings,
)
from ...tasks.buyback import watchlist_flag_notes
from ...utils.inventory_parser import parse_inventory_paste_with_unpacked
from ...utils.pricing_engine import calculate_buyback_quote

CALCULATOR_TEMPLATE = "industry_reforged/buyback/calculator.html"


def _generate_tracking_number(prefix: str = "BB") -> str:
    while True:
        candidate = f"{prefix}-{get_random_string(8).upper()}"
        if not BuybackContract.objects.filter(tracking_number=candidate).exists():
            return candidate


def _compute_donation(gross_total: Decimal, mode: str, raw_value: str) -> Decimal:
    """Resolves the member's chosen donation (ISK amount or percentage of the
    gross appraisal) into a concrete ISK amount, clamped to [0, gross_total]
    so a donation can never exceed - let alone invert - the payout."""
    try:
        value = (
            Decimal(raw_value.strip().replace(",", "."))
            if raw_value
            else Decimal("0.00")
        )
    except InvalidOperation:
        value = Decimal("0.00")
    if value < 0:
        value = Decimal("0.00")

    if mode == "percent":
        value = min(value, Decimal("100.00"))
        donation = (gross_total * value / Decimal("100.00")).quantize(Decimal("0.01"))
    else:
        donation = value.quantize(Decimal("0.01"))

    return min(donation, gross_total)


def _visible_programs(user):
    return (
        BuybackProgram.objects.visible_to(user)
        .select_related("corporation", "recipient_character")
        .prefetch_related("facilities", "known_locations")
    )


def run_calculator(
    request: WSGIRequest, programs, context: dict, *, character, public: bool
) -> HttpResponse:
    """Shared by the member calculator and a program's public calculator.

    GET renders the paste form; POST previews a quote, and on confirm creates
    the BuybackContract + items with a fresh tracking number. `programs` is
    the set the visitor may use, so a program id outside it is a 404 even on
    a hand-crafted POST.
    """
    context["programs"] = programs
    context["public"] = public

    if request.method != "POST":
        return render(request, CALCULATOR_TEMPLATE, context)

    program_id = request.POST.get("program_id", "")
    if not program_id.isdigit():
        raise Http404
    program = get_object_or_404(programs, id=int(program_id))
    inventory_text = request.POST.get("inventory_text", "").strip()
    context["selected_program"] = program
    context["inventory_text"] = inventory_text

    if not inventory_text:
        messages.error(request, _("Please paste your inventory list."))
        return render(request, CALCULATOR_TEMPLATE, context)

    if not public and not character:
        messages.error(
            request, _("You must have a main character set to submit a buyback.")
        )
        return render(request, CALCULATOR_TEMPLATE, context)

    parsed_items, unrecognized, unpacked_type_ids = parse_inventory_paste_with_unpacked(
        inventory_text
    )
    if unrecognized:
        messages.warning(
            request,
            _("Could not recognize the following items: %(items)s")
            % {"items": ", ".join(unrecognized)},
        )

    if not parsed_items:
        messages.error(request, _("No valid items found in the pasted list."))
        return render(request, CALCULATOR_TEMPLATE, context)

    gross_total, item_details = calculate_buyback_quote(
        parsed_items, program, unpacked_type_ids=unpacked_type_ids
    )
    base_total = sum((d["base_line_total"] for d in item_details), Decimal("0.00"))
    hauling_total = sum(
        (d.get("hauling_cost", Decimal("0.00")) for d in item_details),
        Decimal("0.00"),
    )
    modifier_impact = gross_total + hauling_total - base_total
    any_blocked = any(d["blocked"] for d in item_details)
    whole_appraisal_refused = program.reject_appraisal_on_disallowed and any_blocked
    if whole_appraisal_refused:
        messages.error(
            request,
            _(
                "This program only accepts an appraisal when every item is accepted. "
                "Remove the items marked as not accepted and try again."
            ),
        )

    seller_note = request.POST.get("seller_note", "").strip()[:500]
    donation_mode = request.POST.get("donation_mode", "isk")
    donation_amount = _compute_donation(
        gross_total, donation_mode, request.POST.get("donation_value", "")
    )
    net_total = gross_total - donation_amount

    context.update(
        {
            "total_price": gross_total,
            "item_details": item_details,
            "base_total": base_total,
            "modifier_impact": modifier_impact,
            "hauling_total": hauling_total,
            "whole_appraisal_refused": whole_appraisal_refused,
            "donation_mode": donation_mode,
            "donation_value": request.POST.get("donation_value", ""),
            "seller_note": seller_note,
            "donation_amount": donation_amount,
            "net_total": net_total,
        }
    )

    if request.POST.get("confirm") != "1" or whole_appraisal_refused:
        # Preview only - nothing is persisted and no ESI call is made here.
        return render(request, CALCULATOR_TEMPLATE, context)

    submittable = [d for d in item_details if not d["blocked"]]
    if not submittable:
        messages.error(
            request, _("None of the items in this list are accepted by this program.")
        )
        return render(request, CALCULATOR_TEMPLATE, context)

    watchlist_notes = watchlist_flag_notes(
        program, [d["eve_type"].id for d in submittable]
    )
    tracking_number = _generate_tracking_number(program.tracking_prefix)
    contract = BuybackContract.objects.create(
        tracking_number=tracking_number,
        program=program,
        character=character,
        quoted_price=net_total,
        donation_amount=donation_amount,
        hauling_cost=hauling_total,
        status="PENDING",
        flag_watchlist=bool(watchlist_notes),
        flag_notes="\n".join(watchlist_notes),
        is_public_submission=public and character is None,
        seller_note=seller_note,
    )
    BuybackContractItem.objects.bulk_create(
        [
            BuybackContractItem(
                contract=contract,
                eve_type=d["eve_type"],
                quantity=d["quantity"],
                unit_price=d["unit_price"],
                base_unit_price=d["base_unit_price"],
            )
            for d in submittable
        ]
    )

    messages.success(
        request,
        _("Submitted! Your tracking number is %(tracking_number)s.")
        % {"tracking_number": tracking_number},
    )
    detail_view = (
        "industry_reforged:buyback_public_contract"
        if public
        else "industry_reforged:buyback_contract_detail"
    )
    return redirect(detail_view, tracking_number=tracking_number)


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_dashboard(request: WSGIRequest) -> HttpResponse:
    """Lists the programs this member may use and their own contract history."""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    my_contracts = (
        BuybackContract.objects.filter(character_id__in=user_characters)
        .select_related("program")
        .order_by("-created_at")[:50]
    )

    context = {
        "title": _("Buyback Program"),
        "programs": _visible_programs(request.user),
        "my_contracts": my_contracts,
        "notifications_disabled": BuybackUserSettings.objects.filter(
            user=request.user, disable_notifications=True
        ).exists(),
    }
    return render(request, "industry_reforged/buyback/dashboard.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
@require_POST
def buyback_notification_settings(request: WSGIRequest) -> HttpResponse:
    """Turn the member's buyback DMs and Auth notifications on or off."""
    disabled = request.POST.get("notifications") == "off"
    BuybackUserSettings.objects.update_or_create(
        user=request.user, defaults={"disable_notifications": disabled}
    )
    messages.success(
        request,
        (
            _("Buyback notifications turned off.")
            if disabled
            else _("Buyback notifications turned on.")
        ),
    )
    return redirect("industry_reforged:buyback_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_calculator(request: WSGIRequest) -> HttpResponse:
    return run_calculator(
        request,
        _visible_programs(request.user),
        {"title": _("Buyback Calculator")},
        character=request.user.profile.main_character,
        public=False,
    )


def _get_owned_contract_or_403(request, tracking_number):
    """The contract if this user owns it, or directs its program's corporation."""
    contract = get_object_or_404(
        BuybackContract.objects.select_related("program__corporation", "character"),
        tracking_number=tracking_number,
    )
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    if contract.character_id in user_characters:
        return contract

    main = request.user.profile.main_character
    is_program_director = (
        request.user.has_perm("industry_reforged.corp_access")
        and main is not None
        and main.corporation_id == contract.program.corporation.corporation_id
    )
    return contract if is_program_director else None


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_contract_detail(request: WSGIRequest, tracking_number: str) -> HttpResponse:
    """Status page for one buyback contract - owner or a manager only."""
    contract = _get_owned_contract_or_403(request, tracking_number)
    if contract is None:
        messages.error(request, _("Access denied."))
        return redirect("industry_reforged:buyback_dashboard")

    context = {
        "title": _("Buyback Contract %(tracking_number)s")
        % {"tracking_number": contract.tracking_number},
        "contract": contract,
        "items": contract.items.select_related("eve_type"),
        "comparison": item_comparison(contract),
    }
    return render(request, "industry_reforged/buyback/contract_detail.html", context)


def item_comparison(contract) -> list[dict]:
    """Appraised vs. in-game quantity per item, once the contract is matched.
    Empty until the poller has stored the in-game contract's items."""
    if not contract.esi_items:
        return []
    # Third Party
    from eveuniverse.models import EveType

    quoted = {}
    for item in contract.items.select_related("eve_type"):
        quoted[item.eve_type_id] = quoted.get(item.eve_type_id, 0) + item.quantity
    actual = {}
    for item in contract.esi_items:
        actual[item["type_id"]] = actual.get(item["type_id"], 0) + item["quantity"]

    type_ids = set(quoted) | set(actual)
    names = dict(EveType.objects.filter(id__in=type_ids).values_list("id", "name"))
    rows = [
        {
            "name": names.get(type_id, str(type_id)),
            "quoted": quoted.get(type_id, 0),
            "actual": actual.get(type_id, 0),
            "matches": quoted.get(type_id, 0) == actual.get(type_id, 0),
        }
        for type_id in type_ids
    ]
    return sorted(rows, key=lambda row: (row["matches"], row["name"]))


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_contract_cancel(request: WSGIRequest, tracking_number: str) -> HttpResponse:
    """Member-initiated cancel - only while the contract is still PENDING."""
    contract = _get_owned_contract_or_403(request, tracking_number)
    if contract is None:
        messages.error(request, _("Access denied."))
        return redirect("industry_reforged:buyback_dashboard")

    if request.method == "POST":
        if contract.status == "PENDING":
            contract.status = "CANCELLED"
            contract.save(update_fields=["status", "updated_at"])
            messages.success(request, _("Contract cancelled."))
        else:
            messages.error(request, _("Only pending contracts can be cancelled."))

    return redirect(
        "industry_reforged:buyback_contract_detail", tracking_number=tracking_number
    )
