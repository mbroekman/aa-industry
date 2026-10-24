---
id: TASK-269
title: >-
  Enforce skill eligibility on every claim path (bulk + BOM subtree) and request
  contracts scope
status: Done
assignee: []
created_date: '2026-10-24 16:46'
updated_date: '2026-10-24 16:51'
labels:
  - security
  - bug
dependencies: []
priority: high
ordinal: 443000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Permission/scope audit found: (1) bulk_claim_tasks skips the per-task skill hard-stop that claim_task applies, so a bulk POST bypasses it; (2) claim_task and bulk_claim_tasks auto-claim the whole UNCLAIMED BOM subtree without checking skills for the sub-tasks; (3) add_corporate_token never requests esi-contracts.read_corporation_contracts.v1, which buyback_poll_contracts needs. Decision (user): members may SEE everything but may only CLAIM what their main can build, including every sub-task that would be claimed along with it; if any is not buildable, the top-level claim is refused. A skill-lookup failure (no token / ESI error) must block, not allow.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 bulk_claim_tasks refuses a task whose item the main character lacks skills for
- [x] #2 claim_task refuses the claim when any UNCLAIMED BOM sub-task that would be claimed with it fails the skill check
- [x] #3 bulk_claim_tasks skips (with a warning naming the item) a task whose BOM subtree contains a non-buildable sub-task
- [x] #4 Skill lookup failure (empty skill map) blocks skill-gated claims; docstring matches this fail-closed behaviour
- [x] #5 add_corporate_token requests esi-contracts.read_corporation_contracts.v1; README scope list matches the scopes the code uses
- [x] #6 Tests cover each of the above; full suite green
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
New skill_service.check_claim_tree_eligibility() walks the same subtree claim_recursive claims (descends through every BOM child, checks only UNCLAIMED ones) using one skill lookup per claim. Used by claim_task, bulk_claim_tasks and claim_task_preview. Partial claims run the same check up front. Fail-closed was already the actual behaviour (empty skill map = nothing trained); only the docstring claimed otherwise. Added esi-contracts.read_corporation_contracts.v1 to add_corporate_token; existing corp tokens must be re-added once. Guard test test_every_scope_the_code_uses_is_requested_by_a_token_view fails if code filters tokens on a scope no token view requests. 366 tests green.
<!-- SECTION:NOTES:END -->
