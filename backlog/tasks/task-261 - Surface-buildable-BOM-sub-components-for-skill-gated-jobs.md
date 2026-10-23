---
id: TASK-261
title: Surface buildable BOM sub-components for skill-gated jobs
status: Done
assignee: []
created_date: '2026-10-23 10:13'
updated_date: '2026-10-23 10:18'
labels: []
dependencies:
  - TASK-260
modified_files:
  - industry_reforged/utils/skill_service.py
  - industry_reforged/views/industrialist.py
  - industry_reforged/templates/industry_reforged/industrialist_dashboard.html
  - industry_reforged/tests/test_skill_eligibility.py
priority: high
type: feature
ordinal: 435000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When a corp member can't build a top-level item due to a missing EVE skill (Capital Ship Construction, T3 Engineering skills, advanced Reactions tiers), they're currently stuck with nothing to do for that order even though the BOM sub-components are already real ProductionTask rows (created recursively at accept_quote time, bom_parent/bom_children) sitting invisible in the DB. Extend the Job Market visibility rule with one more OR clause: a task is also directly visible if its bom_parent is_claimable=True but skill_service says the viewing user can't build it. Cascades to arbitrary depth for free since each level independently passes the same one-hop test against its own parent - no tree-walk, no new admin config, no migration. Full design: C:\Users\mbroe\.claude\plans\lucky-sparking-cosmos.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 skill_service.py: new check_eligibility_with_levels(skill_levels, item_type_id, activity_id) taking pre-fetched skill levels, avoiding one get_user_skill_levels() call per task on the dashboard
- [x] #2 industrialist_dashboard: unclaimed_tasks_qs widened to all UNCLAIMED tasks, visibility decided in Python via bom_parent is None OR bom_parent.is_claimable==False OR not buildable(bom_parent, user) - using the select_related bom_parent object, not a same-list task_map
- [x] #3 build_task_tree unchanged - still just nests an opaque flat list by bom_parent_id
- [x] #4 Released child rows get task.released_by_parent_skill_gate + a small inline note in industrialist_dashboard.html explaining why they appeared, reusing the existing tooltip/disabled-row patterns
- [x] #5 claim_task/claim_task_preview untouched - a skilled corpmate can still claim the parent directly as today, this is purely additive visibility
- [x] #6 Test coverage: buildable child released, cascading double-gate (grandchild released when both parent and child are skill-gated), non-gated parent unaffected (regression guard), static+skill combined (no duplicate row), end-to-end claim of a released child, claim-after-partial-claim preservation when a skilled user later claims the parent
- [x] #7 Full suite green, ruff clean, no migrations
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented exactly per the approved plan (one-hop OR visibility rule, additive to the existing static is_claimable mechanism). 7 new tests covering: buildable child released, cascading double-gate releasing a grandchild, non-gated parent unaffected (regression guard), static+skill combined (no duplicate row), end-to-end claim of a released child, and claim-after-partial-claim preservation when a skilled corpmate later claims the parent via claim_recursive. 320/320 tests passing, ruff clean, no migrations. Known pre-existing gaps flagged (not fixed, per plan): claim_recursive doesn't re-check skill eligibility per cascaded sub-node on a full-tree claim; a released row whose own parent isn't itself visible renders as a depth-0 root (build_task_tree quirk, pre-existing).
<!-- SECTION:NOTES:END -->
