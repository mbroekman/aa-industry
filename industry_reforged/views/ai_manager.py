# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ..forms import BasketForm, BasketItemFormSet, OpportunityScannerForm
from ..models.ai_manager import (
    AIMarketLog,
    Basket,
    MarketOpportunity,
    OpportunityScanner,
    OpportunityScannerLog,
)
from ..tasks.ai_manager import scan_market_opportunities


@login_required
@permission_required("industry_reforged.add_basket")
def ai_market_manager_dashboard(request):
    """Main dashboard for the AI Market Manager showing all Baskets and Scanners."""
    # Keep session alive on auto-refresh
    request.session.modified = True

    user_corps = get_user_corps(request.user)
    baskets = (
        Basket.objects.filter(corporation__in=user_corps)
        .select_related("corporation", "target_hub")
        .prefetch_related("items", "items__eve_type")
    )
    scanners = OpportunityScanner.objects.filter(
        corporation__in=user_corps
    ).select_related("corporation", "target_hub")

    context = {
        "baskets": baskets,
        "scanners": scanners,
    }
    return render(request, "industry_reforged/ai_manager/dashboard.html", context)


@login_required
@permission_required("industry_reforged.view_aimarketlog")
def ai_audit_log(request):
    """View to show the historical AI Market Logs and Scanner Logs."""
    user_corps = get_user_corps(request.user)

    logs = (
        AIMarketLog.objects.filter(basket_item__basket__corporation__in=user_corps)
        .select_related("basket_item", "basket_item__eve_type")
        .order_by("-timestamp")[:100]
    )
    scanner_logs = (
        OpportunityScannerLog.objects.filter(scanner__corporation__in=user_corps)
        .select_related("scanner")
        .order_by("-timestamp")[:100]
    )

    context = {
        "logs": logs,
        "scanner_logs": scanner_logs,
    }
    return render(request, "industry_reforged/ai_manager/audit_log.html", context)


@login_required
@permission_required("industry_reforged.add_basket")
def opportunity_scanner(request):
    """Proactive view suggesting items with high local velocity and margins."""
    user_corps = get_user_corps(request.user)

    opportunities = (
        MarketOpportunity.objects.filter(corporation__in=user_corps)
        .select_related("eve_type", "corporation", "target_hub")
        .order_by("-margin", "-velocity")
    )
    region_map = dict(OpportunityScannerForm.COMMON_REGIONS)

    context = {"opportunities": opportunities, "region_map": region_map}
    return render(request, "industry_reforged/ai_manager/opportunities.html", context)


@login_required
@permission_required("industry_reforged.add_basket")
def scanner_create(request):
    user_corps = get_user_corps(request.user)
    if request.method == "POST":
        form = OpportunityScannerForm(request.POST, user_corps=user_corps)
        if form.is_valid():
            form.save()
            messages.success(request, _("Opportunity Scanner created successfully."))
            return redirect("industry_reforged:ai_manager_dashboard")
    else:
        form = OpportunityScannerForm(user_corps=user_corps)

    context = {"form": form, "title": _("Create Opportunity Scanner")}
    return render(request, "industry_reforged/ai_manager/scanner_form.html", context)


@login_required
@permission_required("industry_reforged.change_basket")
def scanner_edit(request, pk):
    scanner = get_object_or_404(OpportunityScanner, pk=pk)
    user_corps = get_user_corps(request.user)

    if request.method == "POST":
        form = OpportunityScannerForm(
            request.POST, instance=scanner, user_corps=user_corps
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Opportunity Scanner updated successfully."))
            return redirect("industry_reforged:ai_manager_dashboard")
    else:
        form = OpportunityScannerForm(instance=scanner, user_corps=user_corps)

    context = {"form": form, "title": _("Edit Opportunity Scanner"), "scanner": scanner}
    return render(request, "industry_reforged/ai_manager/scanner_form.html", context)


@login_required
@permission_required("industry_reforged.delete_basket")
def scanner_delete(request, pk):
    scanner = get_object_or_404(OpportunityScanner, pk=pk)
    if request.method == "POST":
        scanner.delete()
        messages.success(request, _("Scanner deleted successfully."))
        return redirect("industry_reforged:ai_manager_dashboard")
    return render(
        request,
        "industry_reforged/ai_manager/scanner_confirm_delete.html",
        {"scanner": scanner},
    )


@login_required
@permission_required("industry_reforged.add_basket")
def scanner_run(request, pk):
    scanner = get_object_or_404(OpportunityScanner, pk=pk)
    if request.method == "POST":
        target_hub_id = scanner.target_hub.facility_id if scanner.target_hub else None
        scanner.is_running = True
        scanner.save(update_fields=["is_running"])
        scan_market_opportunities.delay(
            scanner.corporation.corporation_id,
            scanner.target_region_id,
            scanner.categories,
            target_hub_id=target_hub_id,
            scanner_id=scanner.id,
        )
        messages.success(
            request,
            _(
                f"Scan '{scanner.name}' started in the background. Please check the Opportunities page later."
            ),
        )
        return redirect("industry_reforged:ai_manager_dashboard")
    return redirect("industry_reforged:ai_manager_dashboard")


def get_user_corps(user):
    """Helper to get corporations the user has access to based on their characters."""
    chars = user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    corp_ids = (
        EveCharacter.objects.filter(character_id__in=chars)
        .values_list("corporation_id", flat=True)
        .distinct()
    )
    return EveCorporationInfo.objects.filter(corporation_id__in=corp_ids)


@login_required
@permission_required("industry_reforged.corp_access")
def basket_create(request):
    """View to create a new basket."""
    user_corps = get_user_corps(request.user)
    if request.method == "POST":
        form = BasketForm(request.POST, user_corps=user_corps)
        if form.is_valid():
            basket = form.save()
            formset = BasketItemFormSet(request.POST, instance=basket)
            if formset.is_valid():
                formset.save()
                messages.success(request, _("Basket created successfully."))
                return redirect("industry_reforged:ai_manager_dashboard")
            else:
                basket.delete()
        else:
            formset = BasketItemFormSet(request.POST)
    else:
        form = BasketForm(user_corps=user_corps)
        formset = BasketItemFormSet()

    context = {"form": form, "formset": formset, "title": _("Create Basket")}
    return render(request, "industry_reforged/ai_manager/basket_form.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def basket_edit(request, pk):
    """View to edit an existing basket."""
    user_corps = get_user_corps(request.user)
    basket = get_object_or_404(Basket, pk=pk, corporation__in=user_corps)

    if request.method == "POST":
        form = BasketForm(request.POST, instance=basket, user_corps=user_corps)
        formset = BasketItemFormSet(request.POST, instance=basket)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("Basket updated successfully."))
            return redirect("industry_reforged:ai_manager_dashboard")
    else:
        form = BasketForm(instance=basket, user_corps=user_corps)
        formset = BasketItemFormSet(instance=basket)

    context = {
        "form": form,
        "formset": formset,
        "title": _("Edit Basket"),
        "basket": basket,
    }
    return render(request, "industry_reforged/ai_manager/basket_form.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def basket_delete(request, pk):
    """View to safely delete a basket."""
    user_corps = get_user_corps(request.user)
    basket = get_object_or_404(Basket, pk=pk, corporation__in=user_corps)
    if request.method == "POST":
        basket.delete()
        messages.success(request, _("Basket deleted successfully."))
        return redirect("industry_reforged:ai_manager_dashboard")

    context = {"basket": basket}
    return render(
        request, "industry_reforged/ai_manager/basket_confirm_delete.html", context
    )


@login_required
@permission_required("industry_reforged.access_ai_market_manager")
def scanner_logs(request, pk):
    """Show execution logs for a scanner."""
    scanner = get_object_or_404(OpportunityScanner, pk=pk)

    # Check permissions (must have access to the corp)
    user_corps = get_user_corps(request.user)
    if not user_corps or scanner.corporation not in user_corps:
        messages.error(request, _("You do not have permission to view this scanner."))
        return redirect("industry_reforged:ai_manager_dashboard")

    logs = scanner.logs.all()[:50]

    context = {
        "scanner": scanner,
        "logs": logs,
    }
    return render(request, "industry_reforged/ai_manager/scanner_logs.html", context)


@login_required
@permission_required("industry_reforged.access_ai_market_manager")
def scanner_missing_bpos(request, pk):
    """Show missing blueprints for a scanner."""
    scanner = get_object_or_404(OpportunityScanner, pk=pk)

    # Check permissions
    user_corps = get_user_corps(request.user)
    if not user_corps or scanner.corporation not in user_corps:
        messages.error(request, _("You do not have permission to view this scanner."))
        return redirect("industry_reforged:ai_manager_dashboard")

    missing_bpos = scanner.missing_opportunities.all()

    context = {
        "scanner": scanner,
        "missing_bpos": missing_bpos,
    }
    return render(
        request, "industry_reforged/ai_manager/scanner_missing_bpos.html", context
    )


@login_required
@permission_required("industry_reforged.add_basket")
def basket_run(request, pk):
    basket = get_object_or_404(Basket, pk=pk)
    if request.method == "POST":
        basket.is_running = True
        basket.save(update_fields=["is_running"])
        from ..tasks.ai_manager import evaluate_baskets

        evaluate_baskets.delay(basket.id)
        messages.success(
            request, _(f"Basket '{basket.name}' evaluation started in the background.")
        )
        return redirect("industry_reforged:ai_manager_dashboard")
    return redirect("industry_reforged:ai_manager_dashboard")


@login_required
@permission_required("industry_reforged.view_basket")
def basket_logs(request, pk):
    basket = get_object_or_404(Basket, pk=pk)
    # Get all logs for items in this basket
    from ..models.ai_manager import AIMarketLog

    logs = (
        AIMarketLog.objects.filter(basket_item__basket=basket)
        .select_related("basket_item", "basket_item__eve_type")
        .order_by("-timestamp")[:100]
    )

    context = {
        "title": _("Basket Logs: ") + basket.name,
        "logs": logs,
        "basket": basket,
    }
    return render(request, "industry_reforged/ai_manager/basket_logs.html", context)
