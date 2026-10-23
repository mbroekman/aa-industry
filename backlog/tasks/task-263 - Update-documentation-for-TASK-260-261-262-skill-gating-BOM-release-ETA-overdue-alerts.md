---
id: TASK-263
title: >-
  Update documentation for TASK-260/261/262 (skill gating, BOM release,
  ETA/overdue alerts)
status: Done
assignee: []
created_date: '2026-10-23 14:06'
updated_date: '2026-10-23 14:09'
labels: []
dependencies:
  - TASK-262
modified_files:
  - user_manual_en.md
  - README.md
  - backlog/docs/doc-19 - Architecture-Overview.md
priority: medium
type: docs
ordinal: 437000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update user_manual_en.md (primary - role-based feature descriptions for Builders and Directors), README.md Features summary, and backlog/docs/doc-19 Architecture-Overview.md (currency marker + new subsystems) to reflect the three features shipped this session: skill-gated job eligibility (TASK-260), BOM sub-component release when a parent is skill-gated (TASK-261), and claimed-job ETA tracking / Production Tasks columns / Job Alerts buffer config / overdue notifications (TASK-262). CHANGELOG.md already covers these commit-by-commit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 user_manual_en.md section 2.1 (Industrialist Dashboard) documents: disabled jobs + tooltip for missing skills, the claim-time hard-stop, the item-scoped eligible-slots number in the Claim modal, BOM sub-component release with the Released note, and overdue reminder notifications
- [x] #2 user_manual_en.md section 3.1 (Director Control Panel) documents the new Claimed At / Estimated Done columns on Production Tasks
- [x] #3 user_manual_en.md section 3.4 (Director Config) documents the new Job Alerts (completion buffer) setting
- [x] #4 README.md Features section mentions skill-gated eligibility, BOM release and ETA/overdue alerting
- [x] #5 doc-19 Architecture-Overview.md status/date bumped and the three new subsystems (skill_service.py, eta_service.py, JobTrackingConfig) added
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
user_manual_en.md: added Skill-Gated Jobs, Sub-Component Release and Overdue Reminders bullets to 2.1 (Builders); extended the Production Tasks bullet in 3.1 with the new Claimed At/Estimated Done columns; added Job Alerts bullet to 3.4; mentioned the overdue batch in the Directors Webhook description (3.6); added an Overdue Job Checks bullet to section 4. README.md Features section gained two new bullets (skill-gated eligibility + BOM release, ETA/overdue alerting). doc-19 Architecture-Overview.md: bumped the status line, documented the one-hop OR visibility rule under the ProductionTask central-model section, added JobTrackingConfig to the data model table, added check_overdue_production_tasks to the Celery schedule table (15->16 entries) and job_tracking.py to the per-file summaries, added skill_service.py and eta_service.py to the utils/ business-logic section. CHANGELOG.md was already complete from the TASK-260/261/262 commits themselves.
<!-- SECTION:NOTES:END -->
