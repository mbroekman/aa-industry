---
id: TASK-262
title: 'Claimed-job ETA tracking, overview tab and overdue alerting'
status: Done
assignee: []
created_date: '2026-10-23 13:12'
updated_date: '2026-10-23 13:25'
labels: []
dependencies:
  - TASK-260
modified_files:
  - industry_reforged/models/config.py
  - industry_reforged/models/orders.py
  - industry_reforged/models/__init__.py
  - >-
    industry_reforged/migrations/0081_productiontask_last_overdue_notified_at_and_more.py
  - industry_reforged/utils/eta_service.py
  - industry_reforged/forms.py
  - industry_reforged/views/director.py
  - industry_reforged/views/datatables.py
  - industry_reforged/views/industrialist.py
  - industry_reforged/urls.py
  - industry_reforged/templates/industry_reforged/director_config.html
  - industry_reforged/templates/industry_reforged/director_dashboard.html
  - >-
    industry_reforged/templates/industry_reforged/partials/dt_task_claimed_at.html
  - industry_reforged/templates/industry_reforged/partials/dt_task_eta.html
  - industry_reforged/tasks/job_tracking.py
  - industry_reforged/tasks/__init__.py
  - industry_reforged/tests/test_job_eta_tracking.py
priority: high
type: feature
ordinal: 436000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Track claim time (ProductionTask.assigned_at, already exists) and estimate when a claimed job should be done (claim time + estimated_duration_seconds, or the real ESI end_date once a TaskJobLink exists - preferred when available) plus a corp-wide configurable grace buffer. New director_dashboard tab lists all IN_PRODUCTION tasks corp-wide with claimant, claimed-at and ETA. Periodic Celery task flags overdue tasks, notifies the claimant (AA in-app + Discord DM) with recurring reminders on a cooldown (same buffer value doubles as grace period and repeat interval, confirmed with user), plus one batched director webhook embed per run via the existing directors_webhook. Full design: C:\Users\mbroe\.claude\plans\lucky-sparking-cosmos.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Migration: new JobTrackingConfig model (corporation OneToOne, completion_buffer_hours) + ProductionTask.last_overdue_notified_at
- [x] #2 New utils/eta_service.py: get_task_eta (prefers linked-job ESI end_date, falls back to assigned_at+estimated_duration_seconds, None when unknown - duration=0 or no assigned_at never counts as overdue), is_overdue, get_corp_buffer_hours
- [x] #3 JobTrackingConfigForm + director_config_job_tracking_add/_edit views + new card/tab in director_config.html, same shape as CorporationPricingConfigForm/director_config_pricing_method_edit
- [x] #4 director_dashboard gets a new corp-wide active-jobs tab: Item, Claimed By, Claimed At, Estimated Done (ESI-confirmed vs Estimated badge, or Unknown), overdue highlight
- [x] #5 New periodic Celery task check_overdue_production_tasks: notifies claimant (AA in-app + Discord DM) on first overdue and again after each buffer-interval cooldown while still overdue, one batched directors_webhook embed per corp per run, documented in CELERYBEAT_SCHEDULE + README.md in the same commit
- [x] #6 unclaim_recursive (both copies) resets last_overdue_notified_at to None alongside the existing assigned_at reset
- [x] #7 Tests: get_task_eta/is_overdue correctness incl. unknown-ETA edge cases, Celery task notifies-then-cools-down-then-re-notifies, one embed per corp per run not per task, reset after reclaim, overview view rendering
- [x] #8 Full suite green, ruff clean, migration applies cleanly
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Design pivot during implementation: instead of a brand-new director_dashboard tab (as originally planned), extended the EXISTING 'Production Tasks' table (already supports filtering to IN_PRODUCTION + shows Claimed By) with two new columns (Claimed At, Estimated Done) via the existing dt_director_tasks AJAX endpoint - avoids duplicating UI/logic that already existed for exactly this purpose. 338/338 tests passing (18 new), ruff clean on all new/touched code (pre-existing lint debt elsewhere in forms.py/director.py/tasks/__init__.py left untouched, not part of this change), migration applies cleanly (exercised by the full test suite's DB setup).
<!-- SECTION:NOTES:END -->
