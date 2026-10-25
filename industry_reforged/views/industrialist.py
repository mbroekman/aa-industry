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
    CorpMOTD,
    CorporationIndustryJob,
    MemberOrder,
    ProductionTask,
)
from ..utils.bom_engine import calculate_tasks_bom
from .orders.notifications import notify_order_ready


@login_required
@permission_required("industry_reforged.industrialist_access")
def industrialist_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main execution dashboard for industrialists"""
    # Keep session alive on auto-refresh
    if hasattr(request, "session"):
        request.session.modified = True

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

    # Django
    from django.db.models import Case, Count, IntegerField, Q, Value, When

    priority_order = Case(
        When(priority="URGENT", then=Value(1)),
        When(priority="HIGH", then=Value(2)),
        When(priority="NORMAL", then=Value(3)),
        When(priority="LOW", then=Value(4)),
        default=Value(3),
        output_field=IntegerField(),
    )

    from ..utils import skill_service

    unauthed_characters = skill_service.get_unauthed_characters(request.user)

    # Unclaimed tasks. Fetched unfiltered by BOM position - visibility is decided below in
    # Python, since it now also depends on the per-viewer skill-eligibility of each task's
    # parent, not just the static is_claimable flag SQL can express directly.
    all_unclaimed_qs = (
        ProductionTask.objects.filter(status="UNCLAIMED")
        .select_related(
            "item_type", "bom_parent", "bom_parent__item_type", "created_from_order"
        )
        .annotate(
            incomplete_children_count=Count(
                "bom_children", filter=~Q(bom_children__status="COMPLETED")
            ),
            prio_rank=priority_order,
        )
        .order_by("prio_rank", "created_from_order__created_at", "id")
    )
    all_unclaimed = list(all_unclaimed_qs)

    # One skill fetch for the whole page, reused across every task via this memo - cheap
    # even for a large Job Market since the underlying lookups are themselves cached.
    user_skill_levels = skill_service.get_user_skill_levels(request.user)
    eligibility_memo: dict[tuple[int, int], tuple[bool, list]] = {}

    def get_buildable(item_type_id: int, activity_id: int):
        key = (item_type_id, activity_id)
        if key not in eligibility_memo:
            eligibility_memo[key] = skill_service.check_eligibility_with_levels(
                user_skill_levels, item_type_id, activity_id
            )
        return eligibility_memo[key]

    def is_directly_visible(t) -> bool:
        if t.bom_parent_id is None:
            return True
        if not t.bom_parent.is_claimable:
            return True
        parent_buildable, _ = get_buildable(
            t.bom_parent.item_type_id, t.bom_parent.activity_id
        )
        return not parent_buildable

    visible_unclaimed = [t for t in all_unclaimed if is_directly_visible(t)]
    unclaimed_tasks = build_task_tree(visible_unclaimed)

    # Skill-gated eligibility: disable (not hide) tasks no character the user owns could
    # ever build, independent of slot availability (e.g. capital/T3/advanced-reaction
    # blueprints hard-gated behind specific skills). Tasks released above specifically
    # because their parent is skill-gated get a small explanatory note in the template.
    for task in unclaimed_tasks:
        task.buildable, task.missing_skills = get_buildable(
            task.item_type_id, task.activity_id
        )
        task.missing_skills_text = skill_service.missing_skills_text(
            task.missing_skills
        )

        task.released_by_parent_skill_gate = False
        if task.bom_parent_id and task.bom_parent.is_claimable:
            parent_buildable, parent_missing = get_buildable(
                task.bom_parent.item_type_id, task.bom_parent.activity_id
            )
            if not parent_buildable:
                task.released_by_parent_skill_gate = True
                task.parent_missing_skills_text = skill_service.missing_skills_text(
                    parent_missing
                )

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
        )
        .filter(Q(bom_parent__isnull=True) | Q(bom_parent__is_claimable=False))
        .select_related("item_type", "bom_parent")
        .prefetch_related("linked_jobs__character_job", "linked_jobs__corporation_job")
        .annotate(
            incomplete_children_count=Count(
                "bom_children", filter=~Q(bom_children__status="COMPLETED")
            )
        )
        .order_by("-assigned_at", "id")
    )
    my_tasks = list(my_tasks_qs)

    # My completed tasks (limit to recent 10 to avoid clutter)
    my_completed_tasks = list(
        ProductionTask.objects.filter(
            status="COMPLETED",
            assigned_to_id__in=user_characters,
        )
        .filter(Q(bom_parent__isnull=True) | Q(bom_parent__is_claimable=False))
        .select_related("item_type")
        .prefetch_related("linked_jobs__character_job", "linked_jobs__corporation_job")
        .order_by("-completed_at")[:10]
    )

    # Summary of claimed tasks vs active jobs
    my_claimed_summary = []

    # Django
    from django.db.models import Q, Sum

    # Load ALL IN_PRODUCTION tasks for Build Steps proportional calculation
    all_my_tasks = list(
        ProductionTask.objects.filter(
            status="IN_PRODUCTION",
            assigned_to_id__in=user_characters,
        ).select_related("item_type", "bom_parent")
    )

    if all_my_tasks:
        # AA Industry App
        from industry_reforged.models import TaskJobLink

        # Pre-fetch TaskJobLinks to get progress per task
        task_links = TaskJobLink.objects.filter(task__in=all_my_tasks).select_related(
            "character_job", "corporation_job", "task__item_type"
        )

        for t in all_my_tasks:
            t.task_eve_delivered = 0
            t.task_eve_active = 0
            t.task_eve_ready = 0

        task_map = {t.id: t for t in all_my_tasks}

        for link in task_links:
            job = link.character_job or link.corporation_job
            if not job:
                continue

            task = task_map.get(link.task_id)
            if not task:
                continue

            portion = getattr(link.task.item_type, "portion_size", 1) or 1
            runs = link.linked_runs * portion

            if job.status == "delivered":
                task.task_eve_delivered += runs
            elif job.status == "ready":
                task.task_eve_ready += runs
            elif job.status == "active":
                task.task_eve_active += runs

        memo_remaining = {}
        memo_effective_needed = {}

        def get_effective_needed(t):
            if t.id in memo_effective_needed:
                return memo_effective_needed[t.id]

            if not t.bom_parent_id or t.bom_parent_id not in task_map:
                val = t.quantity
            else:
                parent = task_map[t.bom_parent_id]
                parent_rem = get_remaining(parent)
                if parent.quantity > 0:
                    val = round(parent_rem * (t.quantity / parent.quantity))
                else:
                    val = 0

            memo_effective_needed[t.id] = val
            return val

        def get_remaining(t):
            if t.id in memo_remaining:
                return memo_remaining[t.id]

            needed = get_effective_needed(t)
            completed = t.task_eve_delivered
            in_progress = t.task_eve_active + t.task_eve_ready

            rem = max(0, needed - completed - in_progress)
            memo_remaining[t.id] = rem
            return rem

        # Determine all corp IDs for this user
        corp_ids = request.user.character_ownerships.all().values_list(
            "character__corporation_id", flat=True
        )

        # Pre-fetch available stock from CorpInventory
        # AA Industry App
        from industry_reforged.models import CorpInventory

        type_ids = [item.item_type_id for item in all_my_tasks]
        stock_dict = {}
        if type_ids and corp_ids:
            inventory_qs = (
                CorpInventory.objects.filter(
                    corporation__corporation_id__in=corp_ids, item_type_id__in=type_ids
                )
                .values("item_type_id")
                .annotate(total_qty=Sum("quantity"))
            )

            for inv in inventory_qs:
                stock_dict[inv["item_type_id"]] = inv["total_qty"]

        # Mapping for activity_name
        activity_name_map = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            11: "Reactions",
        }

        grouped_tasks = {}

        for t in all_my_tasks:
            type_id = t.item_type_id
            activity_id = t.activity_id

            key = (type_id, activity_id)
            if key not in grouped_tasks:
                grouped_tasks[key] = []
            grouped_tasks[key].append(t)

        for (type_id, activity_id), tasks in grouped_tasks.items():
            activity_name = activity_name_map.get(
                activity_id, f"Activity {activity_id}"
            )

            # Splitting tasks into those that are "done" (consumed/completed) and "active"
            active_tasks = [
                t
                for t in tasks
                if get_remaining(t) > 0 or t.task_eve_active > 0 or t.task_eve_ready > 0
            ]

            if active_tasks:
                # If there are active tasks, we only summarize the active ones
                # so the user doesn't see inflated "Claimed" numbers from old, already-consumed tasks.
                tasks_to_summarize = active_tasks

                # Determine row status based on the active tasks
                eve_ready = sum(t.task_eve_ready for t in active_tasks)
                remaining = sum(get_remaining(t) for t in active_tasks)
                in_progress = sum(
                    t.task_eve_active + t.task_eve_ready for t in active_tasks
                )

                if remaining <= 0 and in_progress <= 0:
                    row_status = (
                        "completed"  # Fallback, though active_tasks should prevent this
                    )
                elif remaining <= 0 and eve_ready > 0:
                    row_status = "ready"
                else:
                    row_status = "active"
            else:
                # If all tasks are completed/consumed, we summarize all of them
                # so the row still appears under the "Completed" filter.
                tasks_to_summarize = tasks
                row_status = "completed"

            # Sum up dynamic properties using the filtered list
            claimed = sum(t.quantity for t in tasks_to_summarize)
            remaining = sum(get_remaining(t) for t in tasks_to_summarize)
            eve_active = sum(t.task_eve_active for t in tasks_to_summarize)
            eve_ready = sum(t.task_eve_ready for t in tasks_to_summarize)
            eve_delivered = sum(t.task_eve_delivered for t in tasks_to_summarize)
            in_progress = eve_active + eve_ready

            # Since 'completed' includes what's consumed, we calculate it dynamically
            # so that Claimed = Completed + Remaining (to_build) + InProgress
            completed = max(0, claimed - in_progress - remaining)

            progress_percent = (completed / claimed * 100) if claimed > 0 else 100

            my_claimed_summary.append(
                {
                    "item_type_id": type_id,
                    "item_type_name": tasks[0].item_type.name,
                    "activity_name": activity_name,
                    "claimed": claimed,
                    "to_build": remaining,
                    "in_progress": in_progress,
                    "eve_active": eve_active,
                    "eve_ready": eve_ready,
                    "eve_delivered": eve_delivered,
                    "completed": completed,
                    "remaining": remaining,
                    "corp_stock": stock_dict.get(type_id, 0),
                    "row_status": row_status,
                    "progress_percent": progress_percent,
                }
            )

        # Sort the summary to match original order
        my_claimed_summary.sort(key=lambda x: (x["activity_name"], x["item_type_name"]))

    # Active corp jobs (from ESI sync)
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    corp_active_jobs = (
        CorporationIndustryJob.objects.filter(
            corporation__corporation_id__in=user_corps,
            status__in=["active", "ready", "delivered", "paused", "cancelled"],
            taskjoblink__isnull=False,
        )
        .select_related("blueprint_type", "product_type", "installer")
        .distinct()
    )

    # Determine the oldest claim date for the current user's active tasks ONLY
    # Django
    from django.db.models import Q

    oldest_claim_date = None

    assigned_dates = [
        t.assigned_at for t in my_tasks if t.assigned_at and t.status == "IN_PRODUCTION"
    ]
    if assigned_dates:
        oldest_claim_date = min(assigned_dates)

    q_filter = Q(taskjoblink__isnull=False) | Q(status__in=["active", "ready"])
    if oldest_claim_date:
        q_filter |= Q(start_date__gte=oldest_claim_date)

    # My EVE jobs (Corp jobs installed by the industrialist)
    my_eve_jobs = (
        CorporationIndustryJob.objects.filter(
            installer_id__in=user_characters,
            status__in=["active", "ready", "delivered", "paused", "cancelled"],
        )
        .filter(q_filter)
        .select_related("blueprint_type", "product_type", "installer")
        .distinct()
    )

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

    # My payout tasks for the Payment Summary tab
    my_payout_tasks = (
        ProductionTask.objects.filter(
            status="COMPLETED", assigned_to_id__in=user_characters, builder_reward__gt=0
        )
        .select_related("item_type", "payout_batch")
        .order_by("-completed_at")
    )

    # Builder task progress tracking
    active_order_ids = set()
    for task in my_tasks + my_completed_tasks:
        if task.created_from_order_id:
            active_order_ids.add(task.created_from_order_id)

    order_progress = {}
    if active_order_ids:
        # Django
        from django.db.models import Exists, OuterRef, Sum

        from ..models import TaskJobLink

        has_linked_jobs = TaskJobLink.objects.filter(task_id=OuterRef("bom_parent_id"))

        progress_qs = (
            ProductionTask.objects.filter(created_from_order_id__in=active_order_ids)
            .annotate(parent_has_jobs=Exists(has_linked_jobs))
            .values("created_from_order_id", "item_type_id")
            .annotate(
                total_qty=Sum("quantity"),
                completed_qty=Sum("quantity", filter=Q(status="COMPLETED")),
                consumed_qty=Sum(
                    "quantity",
                    filter=Q(status="COMPLETED")
                    & (
                        Q(bom_parent__status="COMPLETED")
                        | (
                            Q(bom_parent__status="IN_PRODUCTION")
                            & Q(parent_has_jobs=True)
                        )
                    ),
                ),
            )
        )
        for p in progress_qs:
            comp = p["completed_qty"] or 0
            cons = p["consumed_qty"] or 0
            order_progress[(p["created_from_order_id"], p["item_type_id"])] = {
                "total": p["total_qty"] or 0,
                "completed": comp,
                "consumed": cons,
                "available": comp - cons,
            }

    for task in my_tasks + my_completed_tasks:
        # Order Progress
        if task.created_from_order_id:
            prog = order_progress.get((task.created_from_order_id, task.item_type_id))
            if prog:
                task.order_total_qty = prog["total"]
                task.order_completed_qty = prog["completed"]
                task.order_consumed_qty = prog["consumed"]
                task.order_available_qty = prog["available"]

        # EVE Progress
        eve_delivered = 0
        eve_active = 0
        portion_size = task.portion_size

        for link in getattr(task, "linked_jobs_cached", task.linked_jobs.all()):
            job = link.character_job or link.corporation_job
            if job:
                if job.status == "delivered":
                    eve_delivered += link.linked_runs * portion_size
                elif job.status in ["active", "ready"]:
                    eve_active += link.linked_runs * portion_size

        task.eve_delivered_qty = min(eve_delivered, task.quantity)
        task.eve_overdelivered_qty = max(0, eve_delivered - task.quantity)
        task.eve_active_qty = eve_active
        task.eve_remaining_qty = max(0, task.quantity - eve_delivered)

    # Live available slots detection
    from ..utils.slot_service import get_user_available_slots

    user_slots = get_user_available_slots(request.user)

    # Materials still missing to finish the member's own claimed jobs - same
    # BOM engine already used for the order-page and shopping-list materials
    # tables, just scoped to this member's claimed ProductionTasks and
    # filtered down to only the materials actually short (this tab is about
    # what's missing, not a full BOM breakdown - that's what Shopping List is for).
    my_missing_materials = []
    if my_tasks:
        all_materials = calculate_tasks_bom(my_tasks, corp_info=corporation).values()
        for mat in all_materials:
            mat["shortfall"] = max(0, mat.get("quantity", 0) - mat.get("corp_stock", 0))
        my_missing_materials = sorted(
            (m for m in all_materials if m["shortfall"] > 0),
            key=lambda m: (m.get("group_name") or "", m.get("name") or ""),
        )
    my_missing_materials_shortage_count = len(my_missing_materials)

    context = {
        "title": "Industrialist Dashboard",
        "motd": motd,
        "dynamic_motd_stats": dynamic_motd_stats,
        "unclaimed_tasks": unclaimed_tasks,
        "my_tasks": my_tasks,
        "my_completed_tasks": my_completed_tasks,
        "corp_active_jobs": corp_active_jobs,
        "my_eve_jobs": my_eve_jobs,
        "my_claimed_summary": my_claimed_summary,
        "my_payout_tasks": my_payout_tasks,
        "user_slots": user_slots,
        "my_missing_materials": my_missing_materials,
        "my_missing_materials_shortage_count": my_missing_materials_shortage_count,
        "unauthed_characters": unauthed_characters,
    }
    return render(request, "industry_reforged/industrialist_dashboard.html", context)


@login_required
@permission_required("industry_reforged.industrialist_access")
def claim_task_preview(request: WSGIRequest) -> HttpResponse:
    """AJAX endpoint for real-time live preview of claim metrics in the modal."""
    # Standard Library
    import math
    from decimal import Decimal

    # Django
    from django.http import JsonResponse

    from ..models import CorpPricingConfig, ProductionTask
    from ..templatetags.industry_tags import format_duration
    from ..utils.pricing_engine import (
        calculate_task_builder_reward,
        get_item_production_details,
    )

    task_id = request.GET.get("task_id") or request.POST.get("task_id")
    task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
    if not task:
        return JsonResponse(
            {"success": False, "error": "Task not found or already claimed"}, status=404
        )

    try:
        claim_qty = int(
            request.GET.get("claim_quantity")
            or request.POST.get("claim_quantity")
            or task.quantity
        )
    except (ValueError, TypeError):
        claim_qty = task.quantity
    claim_qty = max(1, min(claim_qty, task.quantity))

    try:
        allocated_slots = int(
            request.GET.get("allocated_slots")
            or request.POST.get("allocated_slots")
            or 1
        )
    except (ValueError, TypeError):
        allocated_slots = 1
    allocated_slots = max(1, allocated_slots)

    base_dur_sec, portion_size = get_item_production_details(
        task.item_type_id, task.activity_id
    )
    runs_total = max(1, math.ceil(claim_qty / max(portion_size, 1)))
    runs_per_slot = max(1, math.ceil(runs_total / allocated_slots))
    wall_clock_sec = int(base_dur_sec * runs_per_slot * 0.75) if base_dur_sec > 0 else 0

    from ..utils import skill_service
    from ..utils.slot_service import get_user_available_slots

    main_character = request.user.profile.main_character
    failures = (
        skill_service.check_claim_tree_eligibility(main_character.character_id, task)
        if main_character
        else []
    )
    eligible = not failures

    # Slots realistically usable for THIS item (corp + skill eligible characters
    # only) - distinct from the generic account-wide total shown elsewhere, which
    # includes characters that could never build this specific item.
    eligible_slots = get_user_available_slots(
        request.user, activity_id=task.activity_id, item_type_id=task.item_type_id
    )

    corp = None
    if (
        task.created_from_order
        and task.created_from_order.character
        and task.created_from_order.character.corporation
    ):
        corp = task.created_from_order.character.corporation
    elif (
        request.user.profile.main_character
        and request.user.profile.main_character.corporation
    ):
        corp = request.user.profile.main_character.corporation
    pricing_config = (
        CorpPricingConfig.objects.filter(corporation=corp).first() if corp else None
    )

    rem_qty = task.quantity - claim_qty
    ratio = Decimal(str(claim_qty)) / Decimal(str(task.quantity))

    # Pro-rata reward distribution based on the original task's builder_reward
    if task.builder_reward and task.builder_reward > 0:
        reward_claimed = (task.builder_reward * ratio).quantize(Decimal("0.01"))
        reward_rem = (
            (task.builder_reward - reward_claimed) if rem_qty > 0 else Decimal("0.00")
        )
    else:
        # Fallback if task had no builder_reward stored
        full_reward, _dur = calculate_task_builder_reward(
            task.item_type,
            task.quantity,
            task.activity_id,
            task.priority,
            pricing_config,
            task.gamification_value,
        )
        reward_claimed = (full_reward * ratio).quantize(Decimal("0.01"))
        reward_rem = (full_reward - reward_claimed) if rem_qty > 0 else Decimal("0.00")

    return JsonResponse(
        {
            "success": True,
            "task_id": task.id,
            "total_quantity": task.quantity,
            "claim_quantity": claim_qty,
            "allocated_slots": allocated_slots,
            "runs_claimed": runs_total,
            "runs_per_slot": runs_per_slot,
            "portion_size": portion_size,
            "base_duration_seconds": base_dur_sec,
            "wall_clock_seconds": wall_clock_sec,
            "wall_clock_formatted": format_duration(wall_clock_sec),
            "reward_claimed": float(reward_claimed),
            "reward_claimed_formatted": f"{reward_claimed:,.2f} ISK",
            "rem_quantity": rem_qty,
            "rem_reward": float(reward_rem) if rem_qty > 0 else 0.0,
            "rem_reward_formatted": (
                f"{reward_rem:,.2f} ISK" if rem_qty > 0 else "0.00 ISK"
            ),
            "eligible": eligible,
            "missing_skills_text": skill_service.claim_tree_failure_text(failures),
            "eligible_available_slots": eligible_slots["available_slots"],
            "eligible_character_count": eligible_slots["character_count"],
        }
    )


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

        from ..utils import skill_service

        unauthed = skill_service.get_unauthed_characters(request.user)
        if unauthed:
            messages.error(
                request,
                _(
                    "Cannot claim tasks: %(characters)s still need(s) the Skills "
                    "permission re-authed, or your skills/slots will be shown "
                    "incorrectly. Use the link on your dashboard to fix this."
                )
                % {
                    "characters": ", ".join(c.character_name for c in unauthed),
                },
            )
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
        if task:
            if (
                not task.is_claimable
                and task.bom_children.exclude(status="COMPLETED").exists()
            ):
                messages.error(
                    request,
                    _("Cannot claim this task until all sub-jobs are completed."),
                )
                return redirect("industry_reforged:industrialist_dashboard")

            # Skill-gated hard-stop: re-check server-side against the specific character
            # the claim will be attributed to, regardless of what the dashboard rendered -
            # a direct POST must not be able to bypass this. Covers every UNCLAIMED BOM
            # sub-task the claim would take along, not just the task itself.
            failures = skill_service.check_claim_tree_eligibility(
                character.character_id, task
            )
            if failures:
                messages.error(
                    request,
                    _(
                        "Cannot claim this task: %(character)s lacks the required "
                        "skill(s). %(skills)s"
                    )
                    % {
                        "character": character.character_name,
                        "skills": skill_service.claim_tree_failure_text(failures),
                    },
                )
                return redirect("industry_reforged:industrialist_dashboard")

            def has_owned_ancestor(t, char):
                visited = set()
                current = t.bom_parent
                while current:
                    if current.id in visited:
                        break
                    visited.add(current.id)
                    if current.assigned_to == char:
                        return True
                    current = current.bom_parent
                return False

            # Check if partial claim was requested
            try:
                claim_qty = int(request.POST.get("claim_quantity", task.quantity))
            except (ValueError, TypeError):
                claim_qty = task.quantity

            try:
                allocated_slots = max(1, int(request.POST.get("allocated_slots", 1)))
            except (ValueError, TypeError):
                allocated_slots = 1

            # Validate claim_qty bounds
            claim_qty = max(1, min(claim_qty, task.quantity))

            if claim_qty < task.quantity:
                # Standard Library
                import math
                from decimal import Decimal

                from ..models import CorpPricingConfig
                from ..utils.pricing_engine import (
                    calculate_task_builder_reward,
                    get_item_production_details,
                )

                rem_qty = task.quantity - claim_qty
                ratio = Decimal(str(claim_qty)) / Decimal(str(task.quantity))
                claimed_val = (task.gamification_value * ratio).quantize(
                    Decimal("0.01")
                )
                rem_val = task.gamification_value - claimed_val

                corp = None
                if (
                    task.created_from_order
                    and task.created_from_order.character
                    and task.created_from_order.character.corporation
                ):
                    corp = task.created_from_order.character.corporation
                elif character and character.corporation:
                    corp = character.corporation

                pricing_config = (
                    CorpPricingConfig.objects.filter(corporation=corp).first()
                    if corp
                    else None
                )

                # Pro-rata reward distribution based on the original task's builder_reward
                if task.builder_reward and task.builder_reward > 0:
                    reward_claimed = (task.builder_reward * ratio).quantize(
                        Decimal("0.01")
                    )
                    reward_rem = (
                        (task.builder_reward - reward_claimed)
                        if rem_qty > 0
                        else Decimal("0.00")
                    )
                else:
                    full_reward, _dur = calculate_task_builder_reward(
                        task.item_type,
                        task.quantity,
                        task.activity_id,
                        task.priority,
                        pricing_config,
                        task.gamification_value,
                    )
                    reward_claimed = (full_reward * ratio).quantize(Decimal("0.01"))
                    reward_rem = (
                        (full_reward - reward_claimed)
                        if rem_qty > 0
                        else Decimal("0.00")
                    )

                base_dur_sec, portion_size = get_item_production_details(
                    task.item_type_id, task.activity_id
                )
                runs_total = max(1, math.ceil(claim_qty / max(portion_size, 1)))
                runs_per_slot = max(1, math.ceil(runs_total / allocated_slots))
                dur_claimed = (
                    int(base_dur_sec * runs_per_slot * 0.75) if base_dur_sec > 0 else 0
                )
                rem_runs = max(1, math.ceil(rem_qty / max(portion_size, 1)))
                dur_rem = int(base_dur_sec * rem_runs * 0.75) if base_dur_sec > 0 else 0

                # Create the claimed task
                ProductionTask.objects.create(
                    item_type=task.item_type,
                    quantity=claim_qty,
                    activity_id=task.activity_id,
                    status="IN_PRODUCTION",
                    priority=task.priority,
                    origin=task.origin,
                    hidden=task.hidden,
                    created_from_order=task.created_from_order,
                    created_from_blueprint_request=task.created_from_blueprint_request,
                    assigned_to=character,
                    assigned_at=timezone.now(),
                    allocated_slots=allocated_slots,
                    bom_parent=task.bom_parent,
                    gamification_value=claimed_val,
                    builder_reward=(
                        Decimal("0.00")
                        if has_owned_ancestor(task, character)
                        else reward_claimed
                    ),
                    estimated_duration_seconds=dur_claimed,
                    is_claimable=task.is_claimable,
                )

                # Update the remaining task on Job Market
                task.quantity = rem_qty
                task.gamification_value = rem_val
                task.builder_reward = reward_rem
                task.estimated_duration_seconds = dur_rem
                task.save(
                    update_fields=[
                        "quantity",
                        "gamification_value",
                        "builder_reward",
                        "estimated_duration_seconds",
                    ]
                )

                messages.success(
                    request,
                    f"Successfully claimed batch of {claim_qty}x {task.item_type.name} ({allocated_slots} slot(s)). Remaining {rem_qty}x left on Job Market.",
                )
            else:
                # Full task claim
                def claim_recursive(t, char):
                    if t.status == "UNCLAIMED":
                        t.status = "IN_PRODUCTION"
                        t.assigned_to = char
                        t.assigned_at = timezone.now()
                        t.allocated_slots = allocated_slots
                        if allocated_slots > 1:
                            # Standard Library
                            import math

                            from ..utils.pricing_engine import (
                                get_item_production_details,
                            )

                            b_sec, p_size = get_item_production_details(
                                t.item_type_id, t.activity_id
                            )
                            r_total = max(1, math.ceil(t.quantity / max(p_size, 1)))
                            r_per_slot = max(1, math.ceil(r_total / allocated_slots))
                            t.estimated_duration_seconds = (
                                int(b_sec * r_per_slot * 0.75) if b_sec > 0 else 0
                            )
                        if has_owned_ancestor(t, char):
                            t.builder_reward = 0
                        t.save()
                    for child in t.bom_children.all():
                        claim_recursive(child, char)

                claim_recursive(task, character)

                messages.success(
                    request,
                    f"Successfully claimed {task.quantity}x {task.item_type.name}.",
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
        from ..utils.pricing_engine import calculate_task_builder_reward

        def unclaim_recursive(t, char, config):
            if t.status == "IN_PRODUCTION" and t.assigned_to == char:
                t.status = "UNCLAIMED"
                t.assigned_to = None
                t.assigned_at = None
                t.last_overdue_notified_at = None
                t.builder_reward, _ = calculate_task_builder_reward(
                    eve_type=t.item_type,
                    quantity=t.quantity,
                    activity_id=t.activity_id,
                    priority=t.priority,
                    pricing_config=config,
                    line_total_value=t.gamification_value,
                )
                t.save()
            for child in t.bom_children.all():
                unclaim_recursive(child, char, config)

        if task.assigned_to:
            unclaim_recursive(task, task.assigned_to, pricing_config)

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

        from ..utils import skill_service

        unauthed = skill_service.get_unauthed_characters(request.user)
        if unauthed:
            messages.error(
                request,
                _(
                    "Cannot claim tasks: %(characters)s still need(s) the Skills "
                    "permission re-authed, or your skills/slots will be shown "
                    "incorrectly. Use the link on your dashboard to fix this."
                )
                % {
                    "characters": ", ".join(c.character_name for c in unauthed),
                },
            )
            return redirect("industry_reforged:industrialist_dashboard")

        tasks = ProductionTask.objects.filter(id__in=task_ids, status="UNCLAIMED")
        if tasks.exists():
            count = 0

            def has_owned_ancestor(t, char):
                visited = set()
                current = t.bom_parent
                while current:
                    if current.id in visited:
                        break
                    visited.add(current.id)
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
                if (
                    not task.is_claimable
                    and task.bom_children.exclude(status="COMPLETED").exists()
                ):
                    messages.warning(
                        request,
                        _("Skipped %(item)s because sub-jobs are incomplete.")
                        % {"item": task.item_type.name},
                    )
                    continue
                # Same skill hard-stop as claim_task - bulk must not be a bypass.
                failures = skill_service.check_claim_tree_eligibility(
                    character.character_id, task
                )
                if failures:
                    messages.warning(
                        request,
                        _(
                            "Skipped %(item)s: %(character)s lacks the required "
                            "skill(s). %(skills)s"
                        )
                        % {
                            "item": task.item_type.name,
                            "character": character.character_name,
                            "skills": skill_service.claim_tree_failure_text(failures),
                        },
                    )
                    continue
                claim_recursive(task, character)

            if count > 0:
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
            from ..utils.pricing_engine import calculate_task_builder_reward

            def unclaim_recursive(t, char, config):
                nonlocal count
                if t.status == "IN_PRODUCTION" and t.assigned_to == char:
                    t.status = "UNCLAIMED"
                    t.assigned_to = None
                    t.assigned_at = None
                    t.last_overdue_notified_at = None
                    t.builder_reward, _ = calculate_task_builder_reward(
                        eve_type=t.item_type,
                        quantity=t.quantity,
                        activity_id=t.activity_id,
                        priority=t.priority,
                        pricing_config=config,
                        line_total_value=t.gamification_value,
                    )
                    t.save()
                    count += 1
                for child in t.bom_children.all():
                    unclaim_recursive(child, char, config)

            for task in tasks:
                if task.assigned_to:
                    unclaim_recursive(task, task.assigned_to, pricing_config)

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
