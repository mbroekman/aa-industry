---
id: TASK-260
title: >-
  Skill-gated job eligibility in the Job Market (disable jobs no owned character
  can build)
status: Done
assignee: []
created_date: '2026-10-23 06:31'
updated_date: '2026-10-23 09:43'
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

Follow-up fix (user reported after live test): characters not in the same corp as the user's main were being counted both for skill-eligibility AND for the raw slot total (84 slots included alts in unrelated corps with no access to this corp's hangars/facilities). Added get_user_industry_characters(user) in skill_service.py - filters to character_ownerships where corporation_id matches the main character's corp - and wired it into both get_user_skill_levels and slot_service.get_user_available_slots. 2 new regression tests added. Also clarified for the user: the header's slot badge is a global per-account total, not scoped to a specific task - the per-row disabled Claim button/tooltip is what reflects per-task skill eligibility. 312/312 tests passing, ruff clean. Redeployed to devauth via sandbox-sync.ps1.

Second follow-up (user still saw 'too many slots' after the corp-membership fix): confirmed live that was two separate things being conflated. (1) Eligibility boolean was correct - at least one of Maddog's 28 in-corp characters has Capital Ship Construction IV against a level-1 requirement, so the task is genuinely claimable. (2) The Claim modal's slot badge was showing the generic account-wide total (69, after the corp fix) for every item regardless of that item's skill gate - confusing for items only a few toons can actually build. Added an optional item_type_id param to get_user_available_slots that restricts the count to corp+skill-eligible characters only; claim_task_preview now returns this scoped number (eligible_available_slots, eligible_character_count) and the modal JS updates the badge/preset/max once the AJAX response lands, replacing the initial generic estimate. User confirmed via AskUserQuestion this should live in the Claim modal only, not as an extra Job Market column. 313/313 tests passing (1 new regression test), ruff clean.

Third follow-up: the item-scoped badge text was correct ('10 free (1 eligible toon)') but the prominent 'Slots to Dedicate' stepper itself stayed at the stale generic estimate (69) from modal-open time, never corrected - that's what looked like 'no difference' in the screenshot. Fixed: the AJAX preview handler now pulls the slots input down to the real eligible count when it's lower than the initial guess (via the existing setClaimSlots helper), not just the badge/preset/max. Also attempted a server-side allocated_slots clamp in claim_task using the same scoped lookup, but reverted it immediately - it introduced a live ESI call into the hard claim path for EVERY claim (even plain non-skill-gated items), and broke 3 existing tests by falling back to the 1-slot ESI-failure default whenever a token was invalid/cold-cache in test envs. Not worth that risk for what was a pure display bug - the UI fix alone fully addresses what was reported. 313/313 tests passing, ruff clean.
<!-- SECTION:NOTES:END -->
