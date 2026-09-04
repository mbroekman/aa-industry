"""Views for DataTables Server-Side processing"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timesince import timesince, timeuntil

from ..models import CorpBuyOrder, LedgerTransaction, MemberOrder, ProductionTask
from ..templatetags.industry_tags import eve_isk


def get_datatables_params(request):
    """Parse DataTables parameters from GET request"""
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search_value = request.GET.get("search[value]", "")
    order_column_idx = request.GET.get("order[0][column]", 0)
    order_dir = request.GET.get("order[0][dir]", "desc")

    return draw, start, length, search_value, order_column_idx, order_dir


@login_required
@permission_required("industry_reforged.corp_access")
def dt_director_orders(request):
    """AJAX endpoint for Member Orders on Director Dashboard"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    qs = MemberOrder.objects.filter(parent_order__isnull=True)

    # Custom filters
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
        qs = qs.filter(status=status_filter)
    elif status_filter == "PAID":
        qs = qs.filter(is_paid=True)
    elif status_filter == "UNPAID":
        qs = qs.filter(is_paid=False)

    total_records = qs.count()

    # Search
    if search:
        qs = qs.filter(
            Q(character__character_name__icontains=search)
            | Q(character__corporation_name__icontains=search)
            | Q(payment_reference__icontains=search)
            | Q(id__icontains=search)
        )

    filtered_records = qs.count()

    # Ordering
    # Column mapping for DataTables:
    # 0: id, 1: character, 2: total_price, 3: true_cost, 4: margin, 5: payment_ref, 6: status, 7: progress, 8: action
    order_map = {
        "0": "id",
        "1": "character__character_name",
        "2": "total_price",
        "3": "true_cost",
        "4": "created_at",  # margin is calculated, sort by creation
        "5": "payment_reference",
        "6": "status",
        "7": "created_at",  # Progress is calculated, fallback to created_at
    }

    order_field = order_map.get(str(order_col), "created_at")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    # Apply ordering and pagination
    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for order in qs:
        # Check sub-orders
        sub_orders_badge = ""
        if order.child_orders.exists():
            sub_orders_badge = f'<span class="badge bg-secondary ms-1" style="font-size: 0.65em;" data-bs-toggle="tooltip" title="Has {order.child_orders.count()} sub-orders"><i class="fas fa-sitemap"></i> +{order.child_orders.count()}</span>'

        margin = 0.0
        if order.true_cost and order.true_cost > 0:
            margin = ((order.total_price - order.true_cost) / order.true_cost) * 100

        margin_html = f'<span class="{"text-success" if margin >= 0 else "text-danger"}">{margin:.1f}%</span>'

        data.append(
            [
                f"#{order.id} {sub_orders_badge}",
                order.character.character_name if order.character else "Unknown",
                render_to_string(
                    "industry_reforged/partials/dt_isk.html",
                    {"amount": order.total_price},
                ),
                render_to_string(
                    "industry_reforged/partials/dt_isk.html",
                    {"amount": order.true_cost},
                ),
                margin_html,
                order.payment_reference or "-",
                render_to_string(
                    "industry_reforged/partials/dt_order_status.html", {"order": order}
                ),
                render_to_string(
                    "industry_reforged/partials/dt_order_progress.html",
                    {"order": order},
                ),
                render_to_string(
                    "industry_reforged/partials/dt_order_actions.html",
                    {"order": order},
                    request=request,
                ),
            ]
        )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.corp_access")
def dt_director_tasks(request):
    """AJAX endpoint for Production Tasks on Director Dashboard"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    # We accept a 'type' param to distinguish between all_tasks, payout_tasks, recent_completed
    task_type = request.GET.get("type", "all")

    qs = ProductionTask.objects.all()

    if task_type == "payout":
        qs = qs.filter(
            status="COMPLETED", builder_reward__gt=0, payout_batch__isnull=True
        )
    elif task_type == "recent":
        qs = qs.filter(status="COMPLETED", builder_reward__gt=0).order_by(
            "-completed_at"
        )

    # Custom filters for all_tasks
    if task_type == "all":
        status_filter = request.GET.get("task_status", "")
        if status_filter in ["UNCLAIMED", "IN_PRODUCTION", "COMPLETED"]:
            qs = qs.filter(status=status_filter)

        assignee_filter = request.GET.get("task_assignee", "")
        if assignee_filter:
            try:
                qs = qs.filter(assigned_to_id=int(assignee_filter))
            except ValueError:
                pass

    total_records = qs.count()

    # Search
    if search:
        qs = qs.filter(
            Q(item_type__name__icontains=search)
            | Q(assigned_to__character_name__icontains=search)
            | Q(id__icontains=search)
        )

    filtered_records = qs.count()

    # Ordering
    if task_type == "all":
        # 0: type, 1: qty, 2: status, 3: priority, 4: assignee, 5: reward, 6: actions
        order_map = {
            "0": "item_type__name",
            "1": "quantity",
            "2": "status",
            "3": "priority",
            "4": "assigned_to__character_name",
            "5": "builder_reward",
        }
    else:
        # Payout / Recent tasks
        # 0: type, 1: qty, 2: completed by, 3: reward, 4: completed at
        order_map = {
            "0": "item_type__name",
            "1": "quantity",
            "2": "assigned_to__character_name",
            "3": "builder_reward",
            "4": "completed_at",
        }

    order_field = order_map.get(str(order_col), "created_at")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for task in qs:
        if task_type == "all":
            data.append(
                [
                    render_to_string(
                        "industry_reforged/partials/dt_item_type.html",
                        {"type": task.item_type, "task": task},
                    ),
                    task.quantity,
                    render_to_string(
                        "industry_reforged/partials/dt_task_status.html", {"task": task}
                    ),
                    render_to_string(
                        "industry_reforged/partials/dt_task_priority.html",
                        {"task": task},
                    ),
                    render_to_string(
                        "industry_reforged/partials/dt_character.html",
                        {"character": task.assigned_to},
                    ),
                    render_to_string(
                        "industry_reforged/partials/dt_isk.html",
                        {"amount": task.builder_reward},
                    ),
                    render_to_string(
                        "industry_reforged/partials/dt_task_actions.html",
                        {"task": task},
                        request=request,
                    ),
                ]
            )
        else:
            data.append(
                [
                    render_to_string(
                        "industry_reforged/partials/dt_item_type.html",
                        {"type": task.item_type, "task": task},
                    ),
                    task.quantity,
                    render_to_string(
                        "industry_reforged/partials/dt_character.html",
                        {"character": task.assigned_to},
                    ),
                    render_to_string(
                        "industry_reforged/partials/dt_isk.html",
                        {"amount": task.builder_reward},
                    ),
                    (
                        task.completed_at.strftime("%Y-%m-%d %H:%M")
                        if task.completed_at
                        else "-"
                    ),
                ]
            )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.corp_access")
def dt_director_buy_orders(request):
    """AJAX endpoint for Buy Orders on Director Dashboard"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    qs = CorpBuyOrder.objects.all()
    total_records = qs.count()

    if search:
        qs = qs.filter(
            Q(item_type__name__icontains=search)
            | Q(location__name__icontains=search)
            | Q(id__icontains=search)
        )

    filtered_records = qs.count()

    # Columns: 0: id, 1: item, 2: qty, 3: status, 4: created_at, 5: actions
    order_map = {
        "0": "id",
        "1": "item_type__name",
        "2": "quantity",
        "3": "status",
        "4": "created_at",
    }

    order_field = order_map.get(str(order_col), "created_at")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for order in qs:
        data.append(
            [
                f"#{order.id}",
                render_to_string(
                    "industry_reforged/partials/dt_item_type.html",
                    {"type": order.item_type},
                ),
                order.quantity,
                render_to_string(
                    "industry_reforged/partials/dt_buy_order_status.html",
                    {"buy_order": order},
                ),
                (
                    order.created_at.strftime("%Y-%m-%d %H:%M")
                    if order.created_at
                    else "-"
                ),
                render_to_string(
                    "industry_reforged/partials/dt_buy_order_actions.html",
                    {"buy_order": order},
                    request=request,
                ),
            ]
        )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.corp_access")
def dt_corporate_jobs(request):
    """AJAX endpoint for Corporate Jobs on Corporate Dashboard"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)
    job_type = request.GET.get("type", "active")

    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    from ..models import CorporationIndustryJob

    qs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps
    ).select_related("blueprint_type", "product_type", "installer", "corporation")

    active_statuses = ["active", "paused", "ready"]
    if job_type == "active":
        qs = qs.filter(status__in=active_statuses)
    else:
        qs = qs.exclude(status__in=active_statuses)

    total_records = qs.count()

    if search:
        search_q = (
            Q(installer__character_name__icontains=search)
            | Q(product_type__name__icontains=search)
            | Q(blueprint_type__name__icontains=search)
        )
        if search.isdigit():
            search_q |= Q(wallet_division=int(search))
        qs = qs.filter(search_q)

    activity_filter = request.GET.get("activity")
    if activity_filter and activity_filter.isdigit():
        qs = qs.filter(activity_id=int(activity_filter))

    status_filter = request.GET.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)

    filtered_records = qs.count()

    # Columns:
    # Active: 0:Installer, 1:Activity, 2:Item, 3:Runs, 4:Probability, 5:Cost, 6:Wallet, 7:Status, 8:End Date
    # History: 0:Installer, 1:Activity, 2:Item, 3:Runs, 4:Successful, 5:Cost, 6:Wallet, 7:Status, 8:End Date
    order_map = {
        "0": "installer__character_name",
        "1": "activity_id",
        "2": "product_type__name",
        "3": "runs",
        "4": "probability" if job_type == "active" else "successful_runs",
        "5": "cost",
        "6": "wallet_division",
        "7": "status",
        "8": "end_date",
    }

    order_field = order_map.get(str(order_col), "end_date")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for job in qs:
        # Partial for Installer
        installer_html = render_to_string(
            "industry_reforged/partials/dt_corp_installer.html",
            {"installer": job.installer},
        )
        # Partial for Item
        item_html = render_to_string(
            "industry_reforged/partials/dt_corp_job_item.html", {"job": job}
        )
        # Partial for Cost
        cost_html = render_to_string(
            "industry_reforged/partials/dt_isk_warning.html", {"amount": job.cost}
        )

        # Status HTML
        status_html = render_to_string(
            "industry_reforged/partials/dt_corp_job_status.html", {"job": job}
        )

        end_html = "-"
        if job.end_date:
            dt_str = job.end_date.strftime("%Y-%m-%d %H:%M")
            countdown = ""
            if job.status in ["active", "ready"]:
                if job.end_date > timezone.now():
                    countdown = f'<br><span class="text-muted small">(in {timeuntil(job.end_date)})</span>'
                else:
                    countdown = f'<br><span class="text-muted small">({timesince(job.end_date)} ago)</span>'
            end_html = f'<div class="numeric">{dt_str}{countdown}</div>'

        row = [
            installer_html,
            f'<span class="badge bg-secondary">{job.activity_name}</span>',
            item_html,
            f'<div class="text-end numeric">{job.runs}</div>',
            "",  # prob or successful (index 4)
            cost_html,
            job.wallet_division,
            status_html,
            end_html,
        ]

        if job_type == "active":
            prob = f"{job.probability:.2f}%" if job.probability else ""
            row[4] = f'<div class="text-end numeric">{prob}</div>'
        else:
            succ = job.successful_runs if job.successful_runs is not None else "-"
            row[4] = f'<div class="text-end numeric">{succ}</div>'

        data.append(row)

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.corp_access")
def dt_director_transactions(request):
    """AJAX endpoint for Ledger Transactions on Director Dashboard"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    qs_ledger = LedgerTransaction.objects.select_related(
        "character", "director", "member_order", "payout_batch"
    ).all()

    # Optional custom filter (all, payout, received, pending)
    tx_filter = request.GET.get("tx_filter", "all")
    if tx_filter == "payout":
        qs_ledger = qs_ledger.filter(transaction_type="PAYOUT")
    elif tx_filter == "received":
        qs_ledger = qs_ledger.filter(transaction_type="INCOME")
    elif tx_filter == "pending":
        qs_ledger = qs_ledger.none()

    from ..models import BuilderPayoutBatch

    qs_pending = BuilderPayoutBatch.objects.filter(status="PENDING").select_related(
        "builder"
    )
    if tx_filter in ["payout", "received"]:
        qs_pending = qs_pending.none()

    all_records = []

    # Process LedgerTransactions
    for tx in qs_ledger:
        if search:
            s = search.lower()
            if (
                s not in tx.reference.lower()
                and s not in (tx.notes or "").lower()
                and s
                not in (tx.character.character_name.lower() if tx.character else "")
            ):
                continue

        type_badge = ""
        if tx.transaction_type == "INCOME":
            type_badge = '<span class="badge bg-success">INCOME</span>'
        elif tx.transaction_type == "PAYOUT":
            type_badge = '<span class="badge bg-danger">PAYOUT</span>'
        else:
            type_badge = (
                f'<span class="badge bg-secondary">{tx.transaction_type}</span>'
            )

        char_name = tx.character.character_name if tx.character else "Unknown"
        director_name = tx.director.username if tx.director else "System"
        date_str = tx.date.strftime("%Y-%m-%d %H:%M")

        ref_html = tx.reference
        if tx.member_order:
            ref_html = f'<a href="#" data-bs-toggle="modal" data-bs-target="#orderModal" data-order-id="{tx.member_order.id}">{tx.reference}</a>'
        elif tx.payout_batch:
            ref_html = tx.reference

        all_records.append(
            {
                "date_obj": tx.date,
                "date": date_str,
                "type": type_badge,
                "amount_val": tx.amount,
                "amount": eve_isk(tx.amount),
                "character": char_name,
                "reference": ref_html,
                "director": director_name,
                "notes": tx.notes,
                "dir_val": director_name,
            }
        )

    # Process Pending Payouts
    for p in qs_pending:
        if search:
            s = search.lower()
            if s not in p.payment_reference.lower() and s not in (
                p.builder.character_name.lower() if p.builder else ""
            ):
                continue

        type_badge = '<span class="badge bg-warning text-dark">PENDING</span>'
        char_name = p.builder.character_name if p.builder else "Unknown"
        ref_html = p.payment_reference

        all_records.append(
            {
                "date_obj": p.created_at,
                "date": p.created_at.strftime("%Y-%m-%d %H:%M"),
                "type": type_badge,
                "amount_val": p.total_amount,
                "amount": eve_isk(p.total_amount),
                "character": char_name,
                "reference": ref_html,
                "director": "System",
                "notes": "Pending Builder Payout",
                "dir_val": "System",
            }
        )

    total_records = len(all_records)

    # Order
    columns = [
        "date_obj",
        "type",
        "amount_val",
        "character",
        "reference",
        "dir_val",
        "notes",
    ]
    try:
        order_key = columns[int(order_col)]
        all_records.sort(key=lambda x: x[order_key], reverse=order_dir == "desc")
    except (IndexError, ValueError):
        all_records.sort(key=lambda x: x["date_obj"], reverse=True)

    # Pagination
    paginated_records = all_records[start : start + length]

    data = []
    for r in paginated_records:
        data.append(
            {
                "date": r["date"],
                "type": r["type"],
                "amount": r["amount"],
                "character": r["character"],
                "reference": r["reference"],
                "director": r["director"],
                "notes": r["notes"],
            }
        )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.basic_access")
def dt_blueprint_library(request):
    """AJAX endpoint for Corp Blueprint Library"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    from ..models import CorpBlueprint

    qs = CorpBlueprint.objects.select_related("corporation", "eve_type")

    # Custom filters
    # Simple search handling from original view
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(eve_type__name__icontains=q)

    group_filter = request.GET.get("group", "ALL")
    if group_filter != "ALL":
        qs = qs.filter(eve_type__eve_group_id=group_filter)

    total_records = qs.count()

    # Search
    if search:
        qs = qs.filter(
            Q(eve_type__name__icontains=search)
            | Q(corporation__corporation_name__icontains=search)
        )

    filtered_records = qs.count()

    # Columns: 0: Blueprint, 1: Corporation, 2: Runs, 3: Actions
    order_map = {
        "0": "eve_type__name",
        "1": "corporation__corporation_name",
        "2": "runs",
    }

    order_field = order_map.get(str(order_col), "eve_type__name")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for bp in qs:
        runs_html = "&infin;" if bp.is_original else str(bp.runs)

        data.append(
            [
                render_to_string(
                    "industry_reforged/partials/dt_blueprint_item.html", {"bp": bp}
                ),
                bp.corporation.corporation_name,
                runs_html,
                render_to_string(
                    "industry_reforged/partials/dt_blueprint_actions.html",
                    {"bp": bp},
                    request=request,
                ),
            ]
        )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )


@login_required
@permission_required("industry_reforged.corp_access")
def dt_blueprint_requests(request):
    """AJAX endpoint for Blueprint Requests Management"""
    draw, start, length, search, order_col, order_dir = get_datatables_params(request)

    from ..models import BlueprintRequest

    qs = BlueprintRequest.objects.select_related(
        "requester", "blueprint__eve_type", "blueprint__corporation"
    )

    status_filter = request.GET.get("status", "PENDING")
    if status_filter != "ALL":
        qs = qs.filter(status=status_filter)

    total_records = qs.count()

    if search:
        qs = qs.filter(
            Q(requester__username__icontains=search)
            | Q(blueprint__eve_type__name__icontains=search)
            | Q(notes__icontains=search)
        )

    filtered_records = qs.count()

    # Columns: 0: Date, 1: Requester, 2: Blueprint, 3: Qty, 4: Runs, 5: Status, 6: Notes, 7: Actions
    order_map = {
        "0": "created_at",
        "1": "requester__username",
        "2": "blueprint__eve_type__name",
        "3": "requested_quantity",
        "4": "requested_runs",
        "5": "status",
    }

    order_field = order_map.get(str(order_col), "-created_at")
    if order_dir == "desc" and not order_field.startswith("-"):
        order_field = f"-{order_field}"
    elif order_dir == "asc" and order_field.startswith("-"):
        order_field = order_field[1:]

    qs = qs.order_by(order_field)
    if length > 0:
        qs = qs[start : start + length]

    data = []
    for req in qs:
        bp_html = render_to_string(
            "industry_reforged/partials/dt_blueprint_item.html", {"bp": req.blueprint}
        )

        data.append(
            [
                req.created_at.strftime("%Y-%m-%d %H:%M"),
                req.requester.username,
                bp_html,
                req.requested_quantity,
                req.requested_runs,
                render_to_string(
                    "industry_reforged/partials/dt_blueprint_req_status.html",
                    {"req": req},
                ),
                req.notes or "-",
                render_to_string(
                    "industry_reforged/partials/dt_blueprint_req_actions.html",
                    {"req": req},
                    request=request,
                ),
            ]
        )

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
        }
    )
