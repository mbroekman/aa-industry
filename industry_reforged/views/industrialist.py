"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import (
    CharacterIndustryJob,
    CorpMOTD,
    CorporationIndustryJob,
    MemberOrder,
    ProductionTask,
)
from .orders import notify_order_ready


@login_required
@permission_required("industry_reforged.industrialist_access")
def industrialist_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main execution dashboard for industrialists"""

    # Setup corp context
    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    motd = None
    if corporation:
        motd = CorpMOTD.objects.filter(corporation=corporation).first()

    # Helper to convert a queryset into a depth-sorted tree list
    def build_task_tree(qs):
        roots = []
        task_map = {}
        for t in qs:
            t.depth = 0
            t.children_list = []
            task_map[t.id] = t

        for t in qs:
            if t.bom_parent_id and t.bom_parent_id in task_map:
                task_map[t.bom_parent_id].children_list.append(t)
            else:
                roots.append(t)

        flattened = []

        def flatten(node, d):
            node.depth = d
            flattened.append(node)
            for child in node.children_list:
                flatten(child, d + 1)

        for root in roots:
            flatten(root, 0)
        return flattened

    # Unclaimed tasks
    unclaimed_tasks_qs = (
        ProductionTask.objects.filter(status="UNCLAIMED", bom_parent__isnull=True)
        .select_related("item_type", "bom_parent", "created_from_order")
        .order_by("-created_from_order__created_at", "id")
    )
    unclaimed_tasks = build_task_tree(unclaimed_tasks_qs)

    # My active tasks
    # Django
    from django.db.models import Count, Q

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    my_tasks_qs = (
        ProductionTask.objects.filter(
            status="IN_PRODUCTION",
            assigned_to_id__in=user_characters,
            bom_parent__isnull=True,
        )
        .select_related("item_type", "bom_parent")
        .annotate(
            incomplete_children_count=Count(
                "bom_children", filter=~Q(bom_children__status="COMPLETED")
            )
        )
        .order_by("-assigned_at", "id")
    )
    my_tasks = build_task_tree(my_tasks_qs)

    # My completed tasks (limit to recent 10 to avoid clutter)
    my_completed_tasks = ProductionTask.objects.filter(
        status="COMPLETED", assigned_to_id__in=user_characters, bom_parent__isnull=True
    ).order_by("-completed_at")[:10]

    # Summary of claimed tasks vs active jobs
    my_claimed_summary = []

    # Django
    from django.db.models import Sum

    # Total Claimed (from ProductionTask)
    claimed_grouped = (
        ProductionTask.objects.filter(
            status="IN_PRODUCTION", assigned_to_id__in=user_characters
        )
        .values("item_type__id", "item_type__name", "activity_id")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("item_type__name")
    )

    if claimed_grouped:
        # Third Party
        from eveuniverse.models import EveIndustryActivityProduct

        # Get active Character/Corp jobs for the user
        char_jobs = CharacterIndustryJob.objects.filter(
            character_id__in=user_characters, status__in=["active", "ready"]
        )

        # Determine all corp IDs for this user
        corp_ids = request.user.character_ownerships.all().values_list(
            "character__corporation_id", flat=True
        )

        corp_jobs = CorporationIndustryJob.objects.filter(
            installer_id__in=user_characters,
            status__in=["active", "ready"],
            corporation__corporation_id__in=corp_ids,
        )

        # Calculate completed to be accurate
        completed_grouped = (
            ProductionTask.objects.filter(
                status="COMPLETED", assigned_to_id__in=user_characters
            )
            .values("item_type__id")
            .annotate(total_quantity=Sum("quantity"))
        )
        completed_dict = {
            item["item_type__id"]: item["total_quantity"] for item in completed_grouped
        }

        # Mapping for activity_name
        activity_name_map = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            11: "Reactions",
        }

        for item in claimed_grouped:
            type_id = item["item_type__id"]
            activity_id = item["activity_id"]
            activity_name = activity_name_map.get(
                activity_id, f"Activity {activity_id}"
            )

            in_progress = 0

            # Fetch portion size
            portion_size = 1
            bp_prod = EveIndustryActivityProduct.objects.filter(
                product_eve_type_id=type_id, activity_id=activity_id
            ).first()
            if bp_prod:
                portion_size = bp_prod.quantity

            # Filter jobs matching the product
            matching_char_jobs = [j for j in char_jobs if j.product_type_id == type_id]
            matching_corp_jobs = [j for j in corp_jobs if j.product_type_id == type_id]

            for j in matching_char_jobs:
                in_progress += j.runs * portion_size
            for j in matching_corp_jobs:
                in_progress += j.runs * portion_size

            total_claimed = item["total_quantity"]
            completed = completed_dict.get(type_id, 0)
            remaining = max(0, total_claimed - in_progress)

            my_claimed_summary.append(
                {
                    "item_type_id": type_id,
                    "item_type_name": item["item_type__name"],
                    "activity_name": activity_name,
                    "total_claimed": total_claimed,
                    "in_progress": in_progress,
                    "completed": completed,
                    "remaining": remaining,
                }
            )

    # Active corp jobs (from ESI sync)
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    corp_active_jobs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps, status="active"
    ).select_related("blueprint_type", "product_type", "installer")

    # Standard Library
    import random

    # Django
    from django.db.models import Sum

    slogans = [
        _("Keep the forge burning!"),
        _("Building the future of the corporation, one module at a time."),
        _("Industry is the backbone of our fleet."),
        _("Another day, another Capital ship."),
        _("Tritanium flows where the industrialists go."),
        _("Measure twice, build once."),
        _("The anvil never sleeps."),
        _("Forging victory out of raw materials."),
    ]

    orders_qs = MemberOrder.objects.filter(status__in=["ACCEPTED", "IN_PRODUCTION"])
    dynamic_motd_stats = {
        "orders_in_production": orders_qs.filter(parent_order__isnull=True).count(),
        "open_tasks": len(unclaimed_tasks),
        "active_jobs": corp_active_jobs.count(),
        "value_in_progress": orders_qs.aggregate(total=Sum("total_price"))["total"]
        or 0.0,
        "slogan": random.choice(slogans),
    }

    context = {
        "title": "Industrialist Dashboard",
        "motd": motd,
        "dynamic_motd_stats": dynamic_motd_stats,
        "unclaimed_tasks": unclaimed_tasks,
        "my_tasks": my_tasks,
        "my_completed_tasks": my_completed_tasks,
        "corp_active_jobs": corp_active_jobs,
        "my_claimed_summary": my_claimed_summary,
    }
    return render(request, "industry_reforged/industrialist_dashboard.html", context)


@login_required
@permission_required("industry_reforged.industrialist_access")
def claim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to claim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
        if task:

            def has_owned_ancestor(t, char):
                current = t.bom_parent
                while current:
                    if current.assigned_to == char:
                        return True
                    current = current.bom_parent
                return False

            def claim_recursive(t, char):
                if t.status == "UNCLAIMED":
                    t.status = "IN_PRODUCTION"
                    t.assigned_to = char
                    t.assigned_at = timezone.now()
                    if has_owned_ancestor(t, char):
                        t.builder_reward = 0
                    t.save()
                for child in t.bom_children.all():
                    claim_recursive(child, char)

            claim_recursive(task, character)

            messages.success(
                request, f"Successfully claimed {task.quantity}x {task.item_type.name}."
            )
        else:
            messages.error(request, _("Task is no longer available or does not exist."))

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def unclaim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to unclaim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="IN_PRODUCTION").first()
        if not task:
            messages.error(request, _("Task is no longer available or does not exist."))
            return redirect("industry_reforged:industrialist_dashboard")

        if task.assigned_to != character and not request.user.has_perm(
            "industry_reforged.corp_access"
        ):
            messages.error(request, _("You can only unclaim your own tasks."))
            return redirect("industry_reforged:industrialist_dashboard")

        # AA Industry App
        from industry_reforged.models import CorpPricingConfig

        corp_info = None
        if character.corporation:
            corp_info = character.corporation
        elif (
            request.user.has_perm("industry_reforged.corp_access")
            and request.user.profile.main_character.corporation
        ):
            corp_info = request.user.profile.main_character.corporation

        pricing_config = (
            CorpPricingConfig.objects.filter(corporation=corp_info).first()
            if corp_info
            else None
        )
        reward_pct = (
            float(pricing_config.builder_reward_percent) if pricing_config else 0.0
        )

        def unclaim_recursive(t, char, pct):
            if t.status == "IN_PRODUCTION" and t.assigned_to == char:
                t.status = "UNCLAIMED"
                t.assigned_to = None
                t.assigned_at = None
                t.builder_reward = (float(t.gamification_value) * pct) / 100.0
                t.save()
            for child in t.bom_children.all():
                unclaim_recursive(child, char, pct)

        if task.assigned_to:
            unclaim_recursive(task, task.assigned_to, reward_pct)

        messages.success(
            request, f"Successfully unclaimed {task.quantity}x {task.item_type.name}."
        )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_claim_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to claim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        tasks = ProductionTask.objects.filter(id__in=task_ids, status="UNCLAIMED")
        if tasks.exists():
            count = 0

            def has_owned_ancestor(t, char):
                current = t.bom_parent
                while current:
                    if current.assigned_to == char:
                        return True
                    current = current.bom_parent
                return False

            def claim_recursive(t, char):
                nonlocal count
                if t.status == "UNCLAIMED":
                    t.status = "IN_PRODUCTION"
                    t.assigned_to = char
                    t.assigned_at = timezone.now()
                    if has_owned_ancestor(t, char):
                        t.builder_reward = 0
                    t.save()
                    count += 1
                for child in t.bom_children.all():
                    claim_recursive(child, char)

            for task in tasks:
                claim_recursive(task, character)

            messages.success(request, f"Successfully claimed {count} tasks.")
        else:
            messages.error(
                request, _("No valid tasks selected or they are already claimed.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_unclaim_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to unclaim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        tasks = ProductionTask.objects.filter(id__in=task_ids, status="IN_PRODUCTION")
        if not request.user.has_perm("industry_reforged.corp_access"):
            tasks = tasks.filter(assigned_to=character)

        if tasks.exists():
            count = 0
            # AA Industry App
            from industry_reforged.models import CorpPricingConfig

            corp_info = None
            if character.corporation:
                corp_info = character.corporation
            elif (
                request.user.has_perm("industry_reforged.corp_access")
                and request.user.profile.main_character.corporation
            ):
                corp_info = request.user.profile.main_character.corporation

            pricing_config = (
                CorpPricingConfig.objects.filter(corporation=corp_info).first()
                if corp_info
                else None
            )
            reward_pct = (
                float(pricing_config.builder_reward_percent) if pricing_config else 0.0
            )

            def unclaim_recursive(t, char, pct):
                nonlocal count
                if t.status == "IN_PRODUCTION" and t.assigned_to == char:
                    t.status = "UNCLAIMED"
                    t.assigned_to = None
                    t.assigned_at = None
                    t.builder_reward = (float(t.gamification_value) * pct) / 100.0
                    t.save()
                    count += 1
                for child in t.bom_children.all():
                    unclaim_recursive(child, char, pct)

            for task in tasks:
                if task.assigned_to:
                    unclaim_recursive(task, task.assigned_to, reward_pct)

            messages.success(request, f"Successfully unclaimed {count} tasks.")
        else:
            messages.error(
                request, _("No valid tasks selected or you do not own them.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def complete_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        user_characters = request.user.character_ownerships.all().values_list(
            "character_id", flat=True
        )

        task = ProductionTask.objects.filter(
            id=task_id, assigned_to_id__in=user_characters, status="IN_PRODUCTION"
        ).first()
        if task:

            def complete_tree(t):
                if t.status != "COMPLETED":
                    t.status = "COMPLETED"
                    t.completed_at = timezone.now()
                    t.save()
                    for child in t.bom_children.exclude(status="COMPLETED"):
                        complete_tree(child)

            complete_tree(task)

            # Check if all tasks for the order family are completed
            if task.created_from_order:
                order = task.created_from_order
                parent = order.parent_order if order.parent_order else order

                # Django
                from django.db.models import Q

                remaining = (
                    ProductionTask.objects.filter(
                        Q(created_from_order=parent)
                        | Q(created_from_order__parent_order=parent)
                    )
                    .exclude(status="COMPLETED")
                    .exists()
                )

                if not remaining and parent.status != "READY":
                    parent.status = "READY"
                    parent.save()
                    notify_order_ready(parent)

            messages.success(
                request, f"Marked {task.quantity}x {task.item_type.name} as completed!"
            )
        else:
            messages.error(request, _("Task not found or not assigned to you."))

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_complete_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        user_characters = request.user.character_ownerships.all().values_list(
            "character_id", flat=True
        )

        tasks = ProductionTask.objects.filter(
            id__in=task_ids, assigned_to_id__in=user_characters, status="IN_PRODUCTION"
        )
        if tasks.exists():

            def complete_tree(t):
                completed_count = 0
                if t.status != "COMPLETED":
                    t.status = "COMPLETED"
                    t.completed_at = timezone.now()
                    t.save()
                    completed_count += 1
                    for child in t.bom_children.exclude(status="COMPLETED"):
                        completed_count += complete_tree(child)
                return completed_count

            total_completed = 0
            for task in tasks:
                total_completed += complete_tree(task)

            # Check orders for completion
            checked_parents = set()
            for task in tasks:
                if task.created_from_order:
                    order = task.created_from_order
                    parent = order.parent_order if order.parent_order else order

                    if parent.id not in checked_parents:
                        checked_parents.add(parent.id)
                        # Django
                        from django.db.models import Q

                        remaining = (
                            ProductionTask.objects.filter(
                                Q(created_from_order=parent)
                                | Q(created_from_order__parent_order=parent)
                            )
                            .exclude(status="COMPLETED")
                            .exists()
                        )

                        if not remaining and parent.status != "READY":
                            parent.status = "READY"
                            parent.save()
                            notify_order_ready(parent)

            messages.success(
                request,
                f"Successfully marked {total_completed} tasks (including sub-tasks) as completed.",
            )
        else:
            messages.error(
                request, _("No valid tasks selected or they are already completed.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def industrialist_leaderboard(request: WSGIRequest) -> HttpResponse:
    """Leaderboard and History view"""
    # Django
    from django.db.models import Count, Sum

    # Leaderboard by points (gamification_value)
    leaderboard_isk = (
        ProductionTask.objects.filter(status="COMPLETED")
        .values("assigned_to__character_name")
        .annotate(total_isk=Sum("gamification_value"), tasks=Count("id"))
        .order_by("-total_isk")[:25]
    )

    # Leaderboard by volume
    leaderboard_vol = (
        ProductionTask.objects.filter(status="COMPLETED")
        .values("assigned_to__character_name")
        .annotate(total_isk=Sum("gamification_value"), tasks=Count("id"))
        .order_by("-tasks")[:25]
    )

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    personal_history = ProductionTask.objects.filter(
        status="COMPLETED", assigned_to_id__in=user_characters
    ).order_by("-completed_at")

    context = {
        "title": "Industrialist Leaderboards",
        "leaderboard_isk": leaderboard_isk,
        "leaderboard_vol": leaderboard_vol,
        "personal_history": personal_history,
    }
    return render(request, "industry_reforged/industrialist_leaderboard.html", context)
