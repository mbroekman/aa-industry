"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..forms import (
    CorpItemConfigForm,
    CorpPricingConfigForm,
    CorpTypeDiscountForm,
)
from ..models import (
    CorpInventory,
    CorpItemConfig,
    CorpPricingConfig,
    CorpTypeDiscount,
    CorpWalletDivision,
    CorpWalletJournal,
    MemberOrder,
    ProductionTask,
    TaskExecutionLog,
    TaxConfig,
)


def director_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main dashboard for Directors to manage orders and jobs."""
    # Django
    from django.db.models import Count, Sum

    from ..models import BuilderPayoutBatch

    # We show orders for characters in the director's corps
    all_orders = MemberOrder.objects.filter(parent_order__isnull=True).order_by(
        "-created_at"
    )
    all_tasks = ProductionTask.objects.all().order_by("-created_at")

    payout_tasks = (
        ProductionTask.objects.filter(
            status="COMPLETED", builder_reward__gt=0, payout_batch__isnull=True
        )
        .select_related("assigned_to", "item_type")
        .order_by("-completed_at")[:200]
    )

    payout_summary = (
        ProductionTask.objects.filter(
            status="COMPLETED", builder_reward__gt=0, payout_batch__isnull=True
        )
        .values("assigned_to__id", "assigned_to__character_name")
        .annotate(total_reward=Sum("builder_reward"), task_count=Count("id"))
        .order_by("-total_reward")
    )

    payout_batches = BuilderPayoutBatch.objects.all().order_by("-created_at")

    context = {
        "title": "Director Control Panel",
        "all_orders": all_orders,
        "all_tasks": all_tasks,
        "payout_tasks": payout_tasks,
        "payout_summary": payout_summary,
        "payout_batches": payout_batches,
    }
    return render(request, "industry_reforged/director_dashboard.html", context)


def mark_order_delivered(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Mark an order as DELIVERED and notify the buyer."""
    if request.method == "POST":
        order = get_object_or_404(MemberOrder, id=order_id)
        if order.status == "READY":
            order.status = "DELIVERED"
            order.save()
            messages.success(request, f"Order #{order.id} marked as DELIVERED.")

            # Notify the buyer
            # Alliance Auth
            from allianceauth.notifications.models import Notification

            user = None
            try:
                user = order.character.character_ownership.user
            except Exception:
                pass

            if user:
                Notification.objects.notify_user(
                    user=user,
                    title=f"Order #{order.id} Delivered!",
                    message=f"Your order #{order.id} for {order.total_price} ISK has been contracted to you in-game.",
                    level="success",
                )
        else:
            messages.error(request, "Order must be in READY state to be delivered.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#orders-pane")


def mark_order_paid(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Manually process payment (partial or full) and optional notes."""
    if request.method == "POST":
        order = get_object_or_404(MemberOrder, id=order_id)
        if not order.is_paid:
            amount_str = request.POST.get("amount")
            note_str = request.POST.get("note", "").strip()

            # Standard Library
            from decimal import Decimal

            # Django
            from django.utils import timezone

            try:
                if amount_str:
                    amount = Decimal(amount_str.replace(",", "."))
                else:
                    # Default to remaining if not provided
                    amount = order.total_price - order.amount_paid
            except (ValueError, TypeError, ArithmeticError):
                messages.error(request, "Invalid amount provided.")
                return redirect(
                    reverse("industry_reforged:director_dashboard") + "#orders-pane"
                )

            if amount > 0:
                order.amount_paid += amount

            if note_str or amount > 0:
                ts = timezone.now().strftime("%Y-%m-%d %H:%M")
                log_note = f"[{ts}] Manual Entry: "
                if amount > 0:
                    log_note += f"Processed {amount:,.2f} ISK. "
                if note_str:
                    log_note += f"Note: {note_str}"

                if order.notes:
                    order.notes += f"\n{log_note}"
                else:
                    order.notes = log_note

            if order.amount_paid >= order.total_price:
                order.is_paid = True

            order.save()
            messages.success(
                request,
                f"Order #{order.id} ({order.payment_reference}) payment updated.",
            )
        else:
            messages.error(request, "Order is already fully paid.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#orders-pane")


def generate_payout_batch(request: WSGIRequest) -> HttpResponse:
    """Generate a BuilderPayoutBatch for a specific builder."""
    if request.method == "POST":
        builder_id = request.POST.get("builder_id")

        # Django
        from django.db.models import Sum
        from django.utils.crypto import get_random_string

        from ..models import BuilderPayoutBatch, EveCharacter

        builder = get_object_or_404(EveCharacter, id=builder_id)

        # Get tasks
        tasks = ProductionTask.objects.filter(
            status="COMPLETED",
            assigned_to=builder,
            builder_reward__gt=0,
            payout_batch__isnull=True,
        )

        if not tasks.exists():
            messages.warning(
                request, f"No pending payouts found for {builder.character_name}."
            )
            return redirect(
                reverse("industry_reforged:director_dashboard") + "#payouts-pane"
            )

        total_amount = tasks.aggregate(total=Sum("builder_reward"))["total"]

        # Generate random unique ref like PAY-ABCD-1234
        ref = "PAY-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()

        # Assuming the director's corp is paying. We'll just take the first corporation for now.
        # Ideally, it's the corp of the order or the director's corp.
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        if not corporation:
            messages.error(
                request, "You are not part of a corporation to create payouts."
            )
            return redirect(
                reverse("industry_reforged:director_dashboard") + "#payouts-pane"
            )

        batch = BuilderPayoutBatch.objects.create(
            corporation=corporation,
            builder=builder,
            total_amount=total_amount,
            payment_reference=ref,
            status="PENDING",
        )

        # Assign tasks to batch
        tasks.update(payout_batch=batch)
        messages.success(
            request,
            f"Generated Payout Batch for {builder.character_name} with reference: {ref}",
        )

    return redirect(reverse("industry_reforged:director_dashboard") + "#payouts-pane")


def mark_payout_batch_paid(request: WSGIRequest, batch_id: int) -> HttpResponse:
    """Manually mark a BuilderPayoutBatch as paid."""
    from ..models import BuilderPayoutBatch

    if request.method == "POST":
        batch = get_object_or_404(BuilderPayoutBatch, id=batch_id)
        if batch.status == "PENDING":
            batch.status = "PAID"
            batch.paid_at = timezone.now()
            batch.save()
            messages.success(
                request, f"Payout Batch {batch.payment_reference} marked as PAID."
            )
        else:
            messages.error(request, "Batch is already paid.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#payouts-pane")


def director_inventory(request: WSGIRequest) -> HttpResponse:
    """Inventory and Analytics for Directors."""
    # Django
    from django.db.models import Sum

    inventory = (
        CorpInventory.objects.filter(quantity__gt=0)
        .values("item_type__name", "item_type__id")
        .annotate(total_qty=Sum("quantity"))
    )

    configs = CorpItemConfig.objects.filter(target_threshold__gt=0)
    low_stock = []

    inv_dict = {item["item_type__id"]: item["total_qty"] for item in inventory}

    for config in configs:
        current_qty = inv_dict.get(config.item_type.id, 0)
        if current_qty < config.target_threshold:
            low_stock.append(
                {
                    "item_type": config.item_type,
                    "current_qty": current_qty,
                    "target": config.target_threshold,
                    "deficit": config.target_threshold - current_qty,
                }
            )

    from ..models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)
    facility_inventories = []

    for facility in facilities:
        invs = (
            CorpInventory.objects.filter(
                location_id=facility.facility_id, quantity__gt=0
            )
            .values("item_type__name", "item_type__id")
            .annotate(total_qty=Sum("quantity"))
        )
        if invs:
            facility_inventories.append({"facility": facility, "inventory": invs})

    context = {
        "title": "Director Inventory & Analytics",
        "inventory": inventory,
        "low_stock": low_stock,
        "facility_inventories": facility_inventories,
    }
    return render(request, "industry_reforged/director_inventory.html", context)


def director_config(request: WSGIRequest) -> HttpResponse:
    """Mass edit form for Item Configurations."""

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:index")

    item_configs = CorpItemConfig.objects.all().select_related(
        "corporation", "item_type"
    )
    pricing_configs = CorpPricingConfig.objects.all().select_related("corporation")
    type_discounts = CorpTypeDiscount.objects.all().select_related(
        "config__corporation", "eve_type"
    )
    tax_configs = TaxConfig.objects.all().select_related("corporation")
    task_logs = TaskExecutionLog.objects.all().order_by("task_name")

    from ..models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)

    context = {
        "title": "Configurations",
        "configs": item_configs,
        "pricing_configs": pricing_configs,
        "type_discounts": type_discounts,
        "tax_configs": tax_configs,
        "task_logs": task_logs,
        "facilities": facilities,
    }
    return render(request, "industry_reforged/director_config.html", context)


def director_config_structure_toggle(
    request: WSGIRequest, facility_id: int
) -> HttpResponse:
    """Toggle the sync_inventory flag for an Industry Facility."""
    # Django
    from django.shortcuts import get_object_or_404

    from ..models import IndustryFacility

    facility = get_object_or_404(IndustryFacility, facility_id=facility_id)
    facility.sync_inventory = not facility.sync_inventory
    facility.save()

    status = "enabled" if facility.sync_inventory else "disabled"
    messages.success(request, f"Inventory sync for {facility.name} has been {status}.")
    return redirect(reverse("industry_reforged:director_config") + "#facilities")


def director_wallets(request: WSGIRequest) -> HttpResponse:
    """Corporate Wallets and Transactions"""

    # We show wallets for the first configured corp for simplicity, or all user corps
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )

    divisions = CorpWalletDivision.objects.filter(
        corporation__corporation_id__in=user_corps
    ).order_by("division")

    # Filter journals (default to first division if any)
    selected_division_id = request.GET.get("division")
    if selected_division_id:
        journals = CorpWalletJournal.objects.filter(
            division_id=selected_division_id
        ).order_by("-date")[:500]
    else:
        # Just show the first division's journals by default
        first_div = divisions.first()
        if first_div:
            journals = CorpWalletJournal.objects.filter(division=first_div).order_by(
                "-date"
            )[:500]
            selected_division_id = first_div.id
        else:
            journals = []

    context = {
        "title": "Corporate Wallets",
        "divisions": divisions,
        "journals": journals,
        "selected_division_id": (
            int(selected_division_id) if selected_division_id else None
        ),
    }
    return render(request, "industry_reforged/director_wallets.html", context)


def director_config_item_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    from ..models import CorpItemConfig

    if config_id:
        instance = get_object_or_404(CorpItemConfig, id=config_id)
    else:
        instance = CorpItemConfig()

    if request.method == "POST":
        form = CorpItemConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Item configuration saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#items")
    else:
        form = CorpItemConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": (
                _("Edit Item Configuration")
                if config_id
                else _("Add Item Configuration")
            ),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#items",
        },
    )


def director_config_item_delete(request: WSGIRequest, config_id: int) -> HttpResponse:
    from ..models import CorpItemConfig

    config = get_object_or_404(CorpItemConfig, id=config_id)
    config.delete()
    messages.success(request, _("Item configuration deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#items")


def director_config_pricing_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    if config_id:
        instance = get_object_or_404(CorpPricingConfig, id=config_id)
    else:
        instance = CorpPricingConfig()

    if request.method == "POST":
        form = CorpPricingConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Global pricing configuration saved."))
            return redirect(reverse("industry_reforged:director_config") + "#pricing")
    else:
        form = CorpPricingConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": (
                _("Edit Corporation Pricing")
                if config_id
                else _("Add Corporation Pricing")
            ),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#pricing",
        },
    )


def director_config_discount_edit(
    request: WSGIRequest, discount_id: int = None
) -> HttpResponse:
    if discount_id:
        instance = get_object_or_404(CorpTypeDiscount, id=discount_id)
    else:
        instance = CorpTypeDiscount()

    if request.method == "POST":
        form = CorpTypeDiscountForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Type discount saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#discounts")
    else:
        form = CorpTypeDiscountForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": _("Edit Type Discount") if discount_id else _("Add Type Discount"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#discounts",
        },
    )


def director_config_discount_delete(
    request: WSGIRequest, discount_id: int
) -> HttpResponse:
    discount = get_object_or_404(CorpTypeDiscount, id=discount_id)
    discount.delete()
    messages.success(request, _("Type discount deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#discounts")


def director_config_tax_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    from ..forms import TaxConfigForm
    from ..models import TaxConfig

    if config_id:
        instance = get_object_or_404(TaxConfig, id=config_id)
    else:
        instance = TaxConfig()

    if request.method == "POST":
        form = TaxConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("System taxes saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#pricing")
    else:
        form = TaxConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": _("Edit System Taxes") if config_id else _("Add System Taxes"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#pricing",
        },
    )
