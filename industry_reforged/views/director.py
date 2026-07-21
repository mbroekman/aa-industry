"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
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


@login_required
@permission_required("industry_reforged.corp_access")
def director_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main dashboard for Directors to manage orders and jobs."""
    # Django
    from django.db.models import Count, Q, Sum
    from django.db.models.functions import Coalesce

    from ..models import BuilderPayoutBatch, CorpBuyOrder

    # We show orders for characters in the director's corps
    all_orders = MemberOrder.objects.filter(parent_order__isnull=True)

    status_filter = request.GET.get("status", "")
    if status_filter in [
        "REQUESTED",
        "QUOTED",
        "ACCEPTED",
        "REJECTED",
        "IN_PRODUCTION",
        "READY",
        "DELIVERED",
    ]:
        all_orders = all_orders.filter(status=status_filter)
    elif status_filter == "PAID":
        all_orders = all_orders.filter(is_paid=True)
    elif status_filter == "UNPAID":
        all_orders = all_orders.filter(is_paid=False)

    sort_by = request.GET.get("sort", "-created_at")
    valid_sorts = [
        "-created_at",
        "created_at",
        "-total_price",
        "total_price",
        "-id",
        "id",
    ]
    if sort_by in valid_sorts:
        all_orders = all_orders.order_by(sort_by)
    else:
        all_orders = all_orders.order_by("-created_at")

    all_tasks = ProductionTask.objects.all()

    task_status_filter = request.GET.get("task_status", "")
    if task_status_filter in ["UNCLAIMED", "IN_PRODUCTION", "COMPLETED"]:
        all_tasks = all_tasks.filter(status=task_status_filter)

    task_assignee_filter = request.GET.get("task_assignee", "")
    if task_assignee_filter:
        try:
            assignee_id = int(task_assignee_filter)
            all_tasks = all_tasks.filter(assigned_to_id=assignee_id)
        except ValueError:
            pass

    task_sort = request.GET.get("task_sort", "-created_at")
    valid_task_sorts = [
        "-created_at",
        "created_at",
        "-builder_reward",
        "builder_reward",
        "-id",
        "id",
    ]
    if task_sort in valid_task_sorts:
        all_tasks = all_tasks.order_by(task_sort)
    else:
        all_tasks = all_tasks.order_by("-created_at")

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

    task_assignees = (
        ProductionTask.objects.filter(assigned_to__isnull=False)
        .values_list("assigned_to_id", "assigned_to__character_name")
        .distinct()
        .order_by("assigned_to__character_name")
    )

    summary_query = Q(
        created_from_order__status__in=[
            "REQUESTED",
            "QUOTED",
            "ACCEPTED",
            "IN_PRODUCTION",
        ]
    ) | Q(created_from_order__isnull=True, status__in=["UNCLAIMED", "IN_PRODUCTION"])

    production_summary = (
        ProductionTask.objects.filter(summary_query)
        .values("item_type_id", "item_type__name")
        .annotate(
            total_qty=Coalesce(Sum("quantity"), 0),
            unclaimed_qty=Coalesce(Sum("quantity", filter=Q(status="UNCLAIMED")), 0),
            in_production_qty=Coalesce(
                Sum("quantity", filter=Q(status="IN_PRODUCTION")), 0
            ),
            completed_qty=Coalesce(Sum("quantity", filter=Q(status="COMPLETED")), 0),
        )
        .order_by("-total_qty")
    )

    buy_orders = CorpBuyOrder.objects.all().order_by("-created_at")

    context = {
        "title": "Director Control Panel",
        "all_orders": all_orders,
        "all_tasks": all_tasks,
        "payout_tasks": payout_tasks,
        "payout_summary": payout_summary,
        "payout_batches": payout_batches,
        "task_assignees": task_assignees,
        "production_summary": production_summary,
        "buy_orders": buy_orders,
    }
    return render(request, "industry_reforged/director_dashboard.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
def update_buy_order_status(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Update the status of a corporate buy order."""
    if request.method == "POST":
        from ..models import CorpBuyOrder

        order = get_object_or_404(CorpBuyOrder, id=order_id)
        new_status = request.POST.get("status")

        if new_status in dict(CorpBuyOrder.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(
                request,
                f"Buy Order #{order.id} status updated to {order.get_status_display()}.",
            )
        else:
            messages.error(request, "Invalid status.")

    return redirect(
        reverse("industry_reforged:director_dashboard") + "#buy-orders-pane"
    )


@login_required
@permission_required("industry_reforged.corp_access")
def delete_buy_order(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Delete a corporate buy order."""
    if request.method == "POST":
        from ..models import CorpBuyOrder

        order = get_object_or_404(CorpBuyOrder, id=order_id)
        item_name = order.item_type.name
        order.delete()
        messages.success(request, f"Buy Order for {item_name} deleted.")

    return redirect(
        reverse("industry_reforged:director_dashboard") + "#buy-orders-pane"
    )


@login_required
@permission_required("industry_reforged.corp_access")
def delete_production_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    """Delete a ProductionTask. Used by directors to clean up spawned restock jobs."""
    if request.method == "POST":
        from ..models import ProductionTask

        task = get_object_or_404(ProductionTask, id=task_id)
        item_name = task.item_type.name
        task.delete()
        messages.success(request, f"Production Task for {item_name} deleted.")

    return redirect(reverse("industry_reforged:director_dashboard") + "#tasks-pane")


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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
    config_dict = {
        c.item_type_id: {
            "target": c.target_threshold,
            "auto_produce": c.auto_produce,
            "build_or_buy": c.build_or_buy,
        }
        for c in configs
    }

    inventory_list = []
    for item in inventory:
        config_data = config_dict.get(
            item["item_type__id"],
            {"target": 0, "auto_produce": False, "build_or_buy": "BUILD"},
        )
        inventory_list.append(
            {
                "item_type__name": item["item_type__name"],
                "item_type__id": item["item_type__id"],
                "total_qty": item["total_qty"],
                "target": config_data["target"],
                "auto_produce": config_data["auto_produce"],
                "build_or_buy": config_data["build_or_buy"],
            }
        )

    low_stock = []

    inv_dict = {item["item_type__id"]: item["total_qty"] for item in inventory}

    from ..models import CorpBuyOrder, ProductionTask

    open_tasks = (
        ProductionTask.objects.filter(
            created_from_order__isnull=True,
            bom_parent__isnull=True,
            status__in=["UNCLAIMED", "IN_PRODUCTION"],
        )
        .values("item_type_id")
        .annotate(total=Sum("quantity"))
    )
    open_tasks_dict = {t["item_type_id"]: t["total"] for t in open_tasks}

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if corporation:
        open_buys = (
            CorpBuyOrder.objects.filter(
                corporation=corporation, status__in=["OPEN", "IN_PROGRESS"]
            )
            .values("item_type_id")
            .annotate(total=Sum("quantity"))
        )
        open_buys_dict = {b["item_type_id"]: b["total"] for b in open_buys}
    else:
        open_buys_dict = {}

    for config in configs:
        current_qty = inv_dict.get(config.item_type.id, 0)
        in_progress = open_tasks_dict.get(config.item_type.id, 0) + open_buys_dict.get(
            config.item_type.id, 0
        )

        effective_qty = current_qty + in_progress

        if effective_qty < config.target_threshold:
            low_stock.append(
                {
                    "item_type": config.item_type,
                    "current_qty": current_qty,
                    "in_progress": in_progress,
                    "target": config.target_threshold,
                    "deficit": config.target_threshold - effective_qty,
                    "build_or_buy": config.build_or_buy,
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
        "inventory": inventory_list,
        "low_stock": low_stock,
        "facility_inventories": facility_inventories,
    }
    return render(request, "industry_reforged/director_inventory.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def update_inventory_target(request: WSGIRequest, type_id: int) -> HttpResponse:
    """Quickly set the target_threshold for an item from the inventory screen."""
    if request.method == "POST":
        target = int(request.POST.get("target_threshold", 0))
        auto_produce = request.POST.get("auto_produce") == "on"

        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        if not corporation:
            messages.error(request, _("You are not part of a corporation."))
            return redirect("industry_reforged:director_inventory")

        # Third Party
        from eveuniverse.models import EveType

        # Django
        from django.shortcuts import get_object_or_404

        from ..models import CorpItemConfig

        build_or_buy = request.POST.get("build_or_buy", "BUILD")

        eve_type = get_object_or_404(EveType, id=type_id)

        config, created = CorpItemConfig.objects.get_or_create(
            corporation=corporation,
            item_type=eve_type,
            defaults={
                "target_threshold": target,
                "auto_produce": auto_produce,
                "build_or_buy": build_or_buy,
            },
        )
        if not created:
            config.target_threshold = target
            config.auto_produce = auto_produce
            config.build_or_buy = build_or_buy
            config.save()

        messages.success(
            request, f"Target threshold for {eve_type.name} updated to {target}."
        )

    return redirect("industry_reforged:director_inventory")


@login_required
@permission_required("industry_reforged.corp_access")
def spawn_restock_job(request: WSGIRequest, type_id: int) -> HttpResponse:
    """Manually spawn an UNCLAIMED ProductionTask to fulfill a low stock deficit."""
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))

        # Third Party
        from eveuniverse.models import EveType

        # Django
        from django.shortcuts import get_object_or_404

        from ..models import CorpBuyOrder, CorpItemConfig, ProductionTask

        eve_type = get_object_or_404(EveType, id=type_id)

        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        if quantity > 0 and corporation:
            config = CorpItemConfig.objects.filter(
                corporation=corporation, item_type=eve_type
            ).first()
            build_or_buy = config.build_or_buy if config else "BUILD"

            if build_or_buy == "BUILD":
                # Check if a restock job already exists
                existing_task = ProductionTask.objects.filter(
                    item_type=eve_type,
                    created_from_order__isnull=True,
                    bom_parent__isnull=True,
                    status__in=["UNCLAIMED", "IN_PRODUCTION"],
                ).exists()

                if existing_task:
                    messages.warning(
                        request,
                        f"A restock Production Task for {eve_type.name} is already in progress.",
                    )
                    return redirect(
                        reverse("industry_reforged:director_inventory") + "#alerts-pane"
                    )

                from ..models import CorpPricingConfig
                from ..utils.pricing_engine import get_prices_with_overrides

                pricing_config = CorpPricingConfig.objects.filter(
                    corporation=corporation
                ).first()
                reward_percent = (
                    pricing_config.builder_reward_percent if pricing_config else 0.0
                )

                prices = get_prices_with_overrides([eve_type.id], corporation)
                price_per_unit = prices.get(eve_type.id, 0)
                line_total = float(price_per_unit) * quantity
                task_reward = line_total * (reward_percent / 100.0)

                ProductionTask.objects.create(
                    item_type=eve_type,
                    quantity=quantity,
                    status="UNCLAIMED",
                    gamification_value=line_total,
                    builder_reward=task_reward,
                )
                messages.success(
                    request, f"Spawned Production Task for {quantity}x {eve_type.name}."
                )
            else:
                existing_buy = CorpBuyOrder.objects.filter(
                    corporation=corporation,
                    item_type=eve_type,
                    status__in=["OPEN", "IN_PROGRESS"],
                ).exists()

                if existing_buy:
                    messages.warning(
                        request,
                        f"A Procurement Buy Order for {eve_type.name} is already open.",
                    )
                    return redirect(
                        reverse("industry_reforged:director_inventory") + "#alerts-pane"
                    )

                CorpBuyOrder.objects.create(
                    corporation=corporation,
                    item_type=eve_type,
                    quantity=quantity,
                    status="OPEN",
                )
                messages.success(
                    request,
                    f"Generated Procurement Buy Order for {quantity}x {eve_type.name}.",
                )

    return redirect(reverse("industry_reforged:director_inventory") + "#alerts-pane")


@login_required
@permission_required("industry_reforged.corp_access")
def inventory_shopping_list(request: WSGIRequest) -> HttpResponse:
    """Generates a Master Shopping List for all items with a deficit."""
    # Django
    from django.db.models import Sum

    from ..models import CorpInventory, CorpItemConfig
    from ..utils.bom_engine import get_sde_bom

    inventory = (
        CorpInventory.objects.filter(quantity__gt=0)
        .values("item_type__name", "item_type__id")
        .annotate(total_qty=Sum("quantity"))
    )
    inv_dict = {item["item_type__id"]: item["total_qty"] for item in inventory}

    configs = CorpItemConfig.objects.filter(target_threshold__gt=0)

    bom = {}

    def merge_bom(target_bom, new_bom):
        for t_id, data in new_bom.items():
            if t_id in target_bom:
                target_bom[t_id]["quantity"] += data["quantity"]
            else:
                target_bom[t_id] = data

    for config in configs:
        current_qty = inv_dict.get(config.item_type.id, 0)
        if current_qty < config.target_threshold:
            deficit = config.target_threshold - current_qty

            materials, yield_qty = get_sde_bom(config.item_type.id)
            if materials:
                # Standard Library
                import math

                runs = math.ceil(deficit / yield_qty) if yield_qty > 0 else deficit

                type_bom = {}
                for mat in materials:
                    mat_type_id = mat.get("typeid")
                    base_qty = mat.get("quantity", 0)

                    me = config.manual_me / 100.0
                    adjusted_qty = base_qty * (1 - me)

                    req = max(runs, math.ceil(adjusted_qty * runs))
                    type_bom[mat_type_id] = {
                        "type_id": mat_type_id,
                        "name": mat.get("name"),
                        "quantity": req,
                        "base_quantity": req,
                    }
                merge_bom(bom, type_bom)

    total_bom_price = 0
    sorted_bom = []
    if bom:
        from ..utils.pricing_engine import get_fuzzwork_prices

        mat_ids = list(bom.keys())
        prices = get_fuzzwork_prices(mat_ids)
        for mat_id, data in bom.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

        sorted_bom = sorted(bom.values(), key=lambda x: x["name"])

    context = {
        "title": _("Master Deficit Shopping List"),
        "bom_materials": sorted_bom,
        "total_bom_price": total_bom_price,
        "recursive_bom_tree": [],
        "hide_tree": True,
    }
    return render(request, "industry_reforged/shopping_list.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
def update_wallet_threshold(request: WSGIRequest, division_id: int) -> HttpResponse:
    """Updates the warning threshold for a specific wallet division"""
    if request.method == "POST":
        division = get_object_or_404(CorpWalletDivision, id=division_id)

        # Verify the user has access to this corporation's wallets
        user_corps = request.user.character_ownerships.all().values_list(
            "character__corporation_id", flat=True
        )
        if division.corporation.corporation_id not in user_corps:
            messages.error(
                request, _("You do not have permission to modify this wallet.")
            )
            return redirect("industry_reforged:director_wallets")

        try:
            new_threshold = int(request.POST.get("warning_threshold", 500000000))
            if new_threshold < 0:
                raise ValueError("Threshold cannot be negative")
            division.warning_threshold = new_threshold
            division.save()
            messages.success(
                request,
                _(f"Threshold for {division.name} updated to {new_threshold:,} ISK."),
            )
        except ValueError:
            messages.error(request, _("Invalid threshold value provided."))

    return redirect(
        reverse("industry_reforged:director_wallets") + f"?division={division_id}"
    )


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_item_delete(request: WSGIRequest, config_id: int) -> HttpResponse:
    from ..models import CorpItemConfig

    config = get_object_or_404(CorpItemConfig, id=config_id)
    config.delete()
    messages.success(request, _("Item configuration deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#items")


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
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


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_discount_delete(
    request: WSGIRequest, discount_id: int
) -> HttpResponse:
    discount = get_object_or_404(CorpTypeDiscount, id=discount_id)
    discount.delete()
    messages.success(request, _("Type discount deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#discounts")


@login_required
@permission_required("industry_reforged.corp_access")
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
