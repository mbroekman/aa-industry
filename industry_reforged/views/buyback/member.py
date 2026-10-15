"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from ...models import BuybackContract, BuybackContractItem, BuybackProgram
from ...utils.inventory_parser import parse_inventory_paste
from ...utils.pricing_engine import calculate_buyback_quote


def _generate_tracking_number() -> str:
    while True:
        candidate = "BB-" + get_random_string(8).upper()
        if not BuybackContract.objects.filter(tracking_number=candidate).exists():
            return candidate


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_dashboard(request: WSGIRequest) -> HttpResponse:
    """Lists active buyback programs and the member's own contract history."""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    programs = BuybackProgram.objects.filter(is_active=True).select_related(
        "corporation", "facility", "known_location"
    )
    my_contracts = (
        BuybackContract.objects.filter(character_id__in=user_characters)
        .select_related("program")
        .order_by("-created_at")[:50]
    )

    context = {
        "title": _("Buyback Program"),
        "programs": programs,
        "my_contracts": my_contracts,
    }
    return render(request, "industry_reforged/buyback/dashboard.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_calculator(request: WSGIRequest) -> HttpResponse:
    """GET renders the paste form; POST previews a quote, and on confirm,
    creates the BuybackContract + items with a fresh tracking number."""
    programs = BuybackProgram.objects.filter(is_active=True).select_related(
        "corporation", "facility", "known_location"
    )

    context = {
        "title": _("Buyback Calculator"),
        "programs": programs,
    }

    if request.method != "POST":
        return render(request, "industry_reforged/buyback/calculator.html", context)

    program_id = request.POST.get("program_id")
    inventory_text = request.POST.get("inventory_text", "").strip()
    program = get_object_or_404(BuybackProgram, id=program_id, is_active=True)
    context["selected_program"] = program
    context["inventory_text"] = inventory_text

    if not inventory_text:
        messages.error(request, _("Please paste your inventory list."))
        return render(request, "industry_reforged/buyback/calculator.html", context)

    character = request.user.profile.main_character
    if not character:
        messages.error(request, _("You must have a main character set to submit a buyback."))
        return render(request, "industry_reforged/buyback/calculator.html", context)

    parsed_items, unrecognized = parse_inventory_paste(inventory_text)
    if unrecognized:
        messages.warning(
            request,
            _("Could not recognize the following items: %(items)s")
            % {"items": ", ".join(unrecognized)},
        )

    if not parsed_items:
        messages.error(request, _("No valid items found in the pasted list."))
        return render(request, "industry_reforged/buyback/calculator.html", context)

    total_price, item_details = calculate_buyback_quote(parsed_items, program)
    context["total_price"] = total_price
    context["item_details"] = item_details

    if request.POST.get("confirm") != "1":
        # Preview only - nothing is persisted and no ESI call is made here.
        return render(request, "industry_reforged/buyback/calculator.html", context)

    submittable = [d for d in item_details if not d["blocked"]]
    if not submittable:
        messages.error(request, _("Every item in this list was blocked by the watchlist."))
        return render(request, "industry_reforged/buyback/calculator.html", context)

    tracking_number = _generate_tracking_number()
    contract = BuybackContract.objects.create(
        tracking_number=tracking_number,
        program=program,
        character=character,
        quoted_price=total_price,
        status="PENDING",
    )
    BuybackContractItem.objects.bulk_create(
        [
            BuybackContractItem(
                contract=contract,
                eve_type=d["eve_type"],
                quantity=d["quantity"],
                unit_price=d["unit_price"],
            )
            for d in submittable
        ]
    )

    messages.success(
        request,
        _("Submitted! Your tracking number is %(tracking_number)s.")
        % {"tracking_number": tracking_number},
    )
    return redirect("industry_reforged:buyback_contract_detail", tracking_number=tracking_number)


def _get_owned_contract_or_403(request, tracking_number):
    contract = get_object_or_404(
        BuybackContract.objects.select_related("program", "character"),
        tracking_number=tracking_number,
    )
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    is_owner = contract.character_id in user_characters
    is_manager = request.user.has_perm("industry_reforged.corp_access")
    if not is_owner and not is_manager:
        return None
    return contract


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_contract_detail(request: WSGIRequest, tracking_number: str) -> HttpResponse:
    """Status page for one buyback contract - owner or a manager only."""
    contract = _get_owned_contract_or_403(request, tracking_number)
    if contract is None:
        messages.error(request, _("Access denied."))
        return redirect("industry_reforged:buyback_dashboard")

    context = {
        "title": _("Buyback Contract %(tracking_number)s") % {"tracking_number": contract.tracking_number},
        "contract": contract,
        "items": contract.items.select_related("eve_type"),
    }
    return render(request, "industry_reforged/buyback/contract_detail.html", context)


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
            contract.save(update_fields=["status"])
            messages.success(request, _("Contract cancelled."))
        else:
            messages.error(request, _("Only pending contracts can be cancelled."))

    return redirect("industry_reforged:buyback_contract_detail", tracking_number=tracking_number)
