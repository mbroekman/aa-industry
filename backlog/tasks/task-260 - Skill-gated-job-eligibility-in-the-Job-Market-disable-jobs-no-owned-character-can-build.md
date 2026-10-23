---
id: TASK-260
title: >-
  Skill-gated job eligibility in the Job Market (disable jobs no owned character
  can build)
status: Done
assignee: []
created_date: '2026-10-23 06:31'
updated_date: '2026-10-23 06:43'
labels: []
dependencies: []
modified_files:
  - industry_reforged/utils/skill_service.py
  - industry_reforged/utils/slot_service.py
  - industry_reforged/views/industrialist.py
  - industry_reforged/templates/industry_reforged/industrialist_dashboard.html
  - industry_reforged/tests/test_skill_eligibility.py
  - industry_reforged/tests/test_partial_claiming.py
priority: high
type: feature
ordinal: 434000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
84 pooled manufacturing slots exist across a member's accounts, but slot count alone doesn't mean a character can run a given job - EVE hard-gates capital/supercapital/T3/advanced-reaction blueprints behind specific skills (Capital Ship Construction, the 4 T3 Engineering skills, higher Reactions tiers) independent of slots. Add a new industry_reforged/utils/skill_service.py that checks real blueprint skill requirements (django-eveuniverse's EveIndustryActivitySkill, already populated - 22,101 rows confirmed live, no new sync needed) against character skill levels (extends slot_service.py's existing raw-ESI anti-304 skills fetch to return the full skill dict instead of just the 6 hardcoded industry skills). Job Market disables (not hides) any task no owned character could ever build; claim_task adds a server-side hard-stop checking the specific claiming character (main_character). Full design in the approved plan: C:\Users\mbroe\.claude\plans\lucky-sparking-cosmos.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 New skill_service.py: get_character_skill_levels (full dict, reusing the existing raw-ESI anti-304 pattern), get_user_skill_levels (max across owned characters), get_required_skills (via EveIndustryActivityProduct -> EveIndustryActivitySkill, cached 24h), check_user_eligibility, check_character_eligibility
- [x] #2 slot_service.py refactored to source skill levels from skill_service.get_character_skill_levels instead of its own embedded fetch - slot-count behavior and cache keys unchanged
- [x] #3 industrialist_dashboard annotates each unclaimed task with buildable/missing_skills (account-wide check); Job Market template disables the checkbox and replaces the Claim button with a disabled+tooltipped one when not buildable, mirroring the existing BOM-lock pattern
- [x] #4 claim_task hard-stops server-side (messages.error + redirect, same pattern as the existing is_claimable/bom_children check) when the claiming main_character specifically lacks a required skill, even if an alt on the account qualifies
- [x] #5 claim_task_preview includes the eligibility result in its JSON response
- [x] #6 New tests/test_skill_eligibility.py covers: eligible/ineligible character, user-level pass via an alt when main lacks it, claim-time block when main lacks it despite a qualifying alt; test_partial_claiming.py mocks updated for the moved fetch; full suite green; ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Confirmed live on devauth before implementing: EveIndustryActivitySkill already has 22,101 rows populated (no new SDE sync needed). New skill_service.py shares the raw-ESI anti-304 skill fetch with slot_service.py (one call per character for both slots and eligibility). Job Market: account-wide check (any owned character) drives the disabled/tooltip UI; claim_task hard-stops on the specific main_character being attributed, even if an alt qualifies - deliberate asymmetry documented in the approved plan (lucky-sparking-cosmos.md). Required-skills lookup short-circuits to 'eligible' with zero DB/ESI cost whenever a blueprint has no hard requirement (the vast majority of items) - no change in behavior or performance for ordinary T1/T2 jobs. Full suite: 310/310 passing. ruff check clean; ruff format clean on all new/changed lines (pre-existing unrelated formatting debt elsewhere in industrialist.py left untouched, not part of this change).
<!-- SECTION:NOTES:END -->
