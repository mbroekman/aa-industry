"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from ...models import (
    MemberOrder,
    ProductionTask,
)
from ...utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_recursive_tasks_bom,
    get_recursive_bom_tree,
    get_sde_bom,
)


def shopping_list(request: WSGIRequest) -> HttpResponse:
    """Generate a consolidated Shopping List for selected orders."""
    order_ids = request.GET.getlist("order_ids")
    task_ids = request.GET.getlist("task_ids")
    type_id = request.GET.get("type_id")
    quantity = request.GET.get("quantity")
    item_name = request.GET.get("item_name")

    if not order_ids and not task_ids and not type_id:
        messages.warning(request, _("No items selected for shopping list."))
        return redirect(request.headers.get("referer", "industry_reforged:index"))

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    bom = {}
    orders = []
    tasks = []
    recursive_bom_tree = []

    def merge_bom(target, source):
        for mat_id, data in source.items():
            if mat_id in target:
                target[mat_id]["quantity"] += data["quantity"]
                target[mat_id]["base_quantity"] += data.get(
                    "base_quantity", data["quantity"]
                )
            else:
                target[mat_id] = data

    if order_ids:
        orders = MemberOrder.objects.filter(
            id__in=order_ids, character_id__in=user_characters
        )
        for order in orders:
            recursive_bom_tree.extend(calculate_recursive_order_bom(order))
            merge_bom(bom, calculate_order_bom(order))

    if task_ids:
        # User can view tasks if they have basic_access (to claim them) or corp_access.
        # Unclaimed tasks are visible to all. Claimed tasks should be filtered by ownership.
        all_tasks = ProductionTask.objects.filter(id__in=task_ids)
        valid_tasks = []
        for t in all_tasks:
            if t.status == "UNCLAIMED" or (
                t.assigned_to_id and t.assigned_to_id in user_characters
            ):
                valid_tasks.append(t)

        tasks = valid_tasks

        corp_info = None
        main_char = request.user.profile.main_character
        if main_char and main_char.corporation:
            corp_info = main_char.corporation

        recursive_bom_tree.extend(
            calculate_recursive_tasks_bom(tasks, corp_info=corp_info)
        )
        from ...utils.bom_engine import calculate_tasks_bom

        merge_bom(bom, calculate_tasks_bom(tasks, corp_info=corp_info))

    if type_id and quantity:
        quantity = int(quantity)
        materials, yield_qty, _activity = get_sde_bom(type_id)

        corp_info = None
        main_char = request.user.profile.main_character
        if main_char and main_char.corporation:
            corp_info = main_char.corporation

        corp_stock = {}
        if corp_info:
            # Django
            from django.db.models import Sum

            from ...models import CorpInventory

            inventory = (
                CorpInventory.objects.filter(corporation=corp_info, quantity__gt=0)
                .values("item_type_id")
                .annotate(total=Sum("quantity"))
            )
            for inv in inventory:
                corp_stock[inv["item_type_id"]] = inv["total"]

        node = get_recursive_bom_tree(
            type_id,
            item_name or str(type_id),
            quantity,
            {type_id: {"exclude_from_orders": False}},
        )
        recursive_bom_tree.append(node)

        # Standard Library
        import math

        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity
        type_bom = {}
        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)
            req = max(runs, math.ceil(base_qty * runs))
            type_bom[mat_type_id] = {
                "type_id": mat_type_id,
                "name": mat.get("name"),
                "quantity": req,
                "base_quantity": req,
                "corp_stock": corp_stock.get(mat_type_id, 0),
            }
        merge_bom(bom, type_bom)

    total_bom_price = 0
    sorted_bom = []
    if bom:
        mat_ids = list(bom.keys())

        from ...utils.pricing_engine import get_fuzzwork_prices

        prices = get_fuzzwork_prices(mat_ids)
        for mat_id, data in bom.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

        sorted_bom = sorted(bom.values(), key=lambda x: x["name"])

    context = {
        "title": _("Shopping List"),
        "orders": orders,
        "tasks": tasks,
        "custom_item_name": item_name,
        "custom_item_quantity": quantity,
        "bom_materials": sorted_bom,
        "total_bom_price": total_bom_price,
        "recursive_bom_tree": recursive_bom_tree,
    }
    return render(request, "industry_reforged/shopping_list.html", context)
