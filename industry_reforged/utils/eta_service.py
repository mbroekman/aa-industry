"""
Claimed-job ETA computation.

Estimates when a claimed ProductionTask should be done, preferring the real ESI-reported
end_date of the EVE industry job the claimant actually started (once the heuristic linker
connects it via TaskJobLink) over the claim-time estimate (assigned_at + estimated_duration_
seconds), which is all that's available in the gap between claiming in-app and the linker
catching up (or if duration was never successfully computed at creation time).
"""

# Standard Library
import datetime
from typing import Any

# Django
from django.core.cache import cache
from django.utils import timezone

DEFAULT_BUFFER_HOURS = 2
CACHE_TTL_BUFFER_HOURS = 3600  # 1 hour - config rarely changes, cheap to keep fresh


def get_task_eta(task: Any) -> datetime.datetime | None:
    """
    Best-known completion time for a claimed task, or None if it can't be determined.

    Preference order:
    1. The latest end_date among this task's still-active/ready linked EVE industry jobs
       (the real ESI timer - strictly more accurate than an estimate).
    2. assigned_at + estimated_duration_seconds, if both are set and duration is non-zero.
    3. None ("unknown") - never guessed as "now"/"overdue" from incomplete data.
    """
    latest_job_end: datetime.datetime | None = None
    for link in task.linked_jobs.select_related(
        "character_job", "corporation_job"
    ).all():
        job = link.character_job or link.corporation_job
        if not job or job.status not in ("active", "ready") or not job.end_date:
            continue
        if latest_job_end is None or job.end_date > latest_job_end:
            latest_job_end = job.end_date

    if latest_job_end is not None:
        return latest_job_end

    if task.assigned_at and task.estimated_duration_seconds > 0:
        return task.assigned_at + datetime.timedelta(
            seconds=task.estimated_duration_seconds
        )

    return None


def is_overdue(task: Any, buffer_hours) -> bool:
    """A task counts as overdue only once its ETA (if known) plus the grace buffer has
    passed. Unknown ETA is never treated as overdue - no data means no alarm."""
    if task.status != "IN_PRODUCTION":
        return False
    eta = get_task_eta(task)
    if eta is None:
        return False
    return timezone.now() > eta + datetime.timedelta(hours=float(buffer_hours))


def get_corp_buffer_hours(corporation) -> int:
    """The corp's configured overdue grace period/reminder interval, cached 1h. Defaults
    to DEFAULT_BUFFER_HOURS if the corp hasn't configured one yet."""
    if not corporation:
        return DEFAULT_BUFFER_HOURS

    cache_key = f"industry_reforged_job_buffer_hours_{corporation.corporation_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Third Party
    from ..models import JobTrackingConfig

    config = JobTrackingConfig.objects.filter(corporation=corporation).first()
    buffer_hours = config.completion_buffer_hours if config else DEFAULT_BUFFER_HOURS
    cache.set(cache_key, buffer_hours, timeout=CACHE_TTL_BUFFER_HOURS)
    return buffer_hours
