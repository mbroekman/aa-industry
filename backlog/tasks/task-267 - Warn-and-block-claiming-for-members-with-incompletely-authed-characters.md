---
id: TASK-267
title: Warn and block claiming for members with incompletely-authed characters
status: Done
assignee: []
created_date: '2026-10-24 14:33'
updated_date: '2026-10-24 14:33'
labels: []
dependencies: []
ordinal: 441000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Detect when a member's same-corp characters are missing the esi-skills.read_skills.v1 ESI scope (this plugin's own add-character flow never requested it, so skill_service/slot_service silently show 0 skills / base 1-slot for that character). Show a dashboard banner naming the character(s) and block claim_task/bulk_claim_tasks until fixed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 New skill_service.get_unauthed_characters(user) helper, DB-only scope-existence check, no live ESI call
- [x] #2 add_personal_token now also requests esi-skills.read_skills.v1 so new/re-auths stop recurring
- [x] #3 Industrialist dashboard shows a dismissible banner naming unauthed character(s) with a link to fix it
- [x] #4 claim_task and bulk_claim_tasks both refuse with a clear message when the user has any unauthed same-corp character
- [x] #5 Full test suite green, ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root cause: views/api.py's add_personal_token only ever requested esi-industry.read_character_jobs.v1 + esi-planets.manage_planets.v1 - never esi-skills.read_skills.v1 - so a character added through this plugin's own UI permanently looked like 0 skills / base 1-slot to skill_service/slot_service, which silently fail open (empty dict) on a missing token/scope by design. New check is a cheap Token.objects.filter(...).exists() DB query (same idiom already used throughout this codebase), deliberately NOT a live ESI call - a prior attempt (TASK-255) to put live ESI checks in the claim path was reverted for exactly that flakiness reason. Updated 3 existing test fixtures (test_skill_eligibility.py x2 classes, test_job_eta_tracking.py) to include a properly-scoped token, since claim_task/bulk_claim_tasks now hard-stop without one. Hit and fixed a related test-authoring pitfall: AllianceAuth's Token post_save signal auto-manages CharacterOwnership.owner_hash and will silently blank out/collide a test's manually-chosen owner_hash values unless each Token.objects.create() in the same test gives its own distinct character_owner_hash.
<!-- SECTION:NOTES:END -->
