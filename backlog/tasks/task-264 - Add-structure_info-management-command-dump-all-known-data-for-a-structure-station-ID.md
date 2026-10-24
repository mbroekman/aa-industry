---
id: TASK-264
title: >-
  Add structure_info management command (dump all known data for a
  structure/station ID)
status: Done
assignee: []
created_date: '2026-10-24 06:04'
updated_date: '2026-10-24 06:38'
labels: []
dependencies: []
modified_files:
  - industry_reforged/management/commands/structure_info.py
priority: low
type: chore
ordinal: 438000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Diagnostic script for directors/devs: given an Upwell structure ID or NPC station ID, print everything the plugin can learn about it - the basic ESI universe/structures or universe/stations lookup (name, type, system, owner, security), the richer per-corp structures endpoint when a usable token exists (services, fuel expiry, reinforcement state/timers), and whatever's already cached locally in IndustryFacility/IndustryFacilityRig. Reuses the exact ESI token/endpoint patterns already in tasks/facilities.py (CorporationSyncConfig sync_character tokens, esi-universe.read_structures.v1 / esi-corporations.read_structures.v1 scopes).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 manage.py structure_info <id> works for both NPC stations (<100000000, public endpoint) and Upwell structures (authenticated, tries every corp's sync token)
- [x] #2 Prints name, type name, solar system name + security class, owner corp name, position when available
- [x] #3 For Upwell structures where a corp structures-endpoint token is available: also prints services, fuel_expires, state, reinforce_hour, state timers
- [x] #4 Prints any locally cached IndustryFacility row and its installed IndustryFacilityRig entries
- [x] #5 Clear error message (not a traceback) when the structure is inaccessible with every available token
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Reuses the exact ESI token/endpoint patterns from tasks/facilities.py (CorporationSyncConfig sync_character tokens, esi-universe.read_structures.v1 for the basic lookup, esi-corporations.read_structures.v1 for services/fuel/reinforcement detail). Name resolution mirrors tasks/utils.py's existing helpers (_get_security_space, EveType.get_or_create_esi, EveSolarSystem local-then-ESI-fallback). ruff clean, full suite still 338/338 (new file doesn't affect app loading). No unit tests added - consistent with the existing ops-script precedent (test_inventory.py/wipe_industry_data.py), verified live on devauth instead.

Follow-up: inaccessible-structure errors used to raise CommandError, which aborted before ever reaching the local-cache fallback - meaning the one thing that still mattered (which solar system it's in, from a past successful sync) was never shown. Fixed: every failure path (no sync configs, failed NPC station lookup, failed Upwell live lookup) now warns and falls through to the cached IndustryFacility data instead of aborting, and the cached-facility output now actually prints Solar System/Type/Owner (it previously only showed flags/timestamps, not the fields the user actually asked for). Also: the corp-structures-endpoint detail (director-role permission, separate from docking-based universe/structures access) now prints its own Solar System/Type too, since that endpoint can succeed even when the public-ish structure lookup 403s. Verified live on devauth against the same real NOT-PUBLIC structure that previously hard-failed.

Follow-up (user feedback: the script was looking at "our corp" only, not what we can actually retrieve): both the basic universe/structures lookup and the richer corp-structures detail were hardcoded to CorporationSyncConfig's own designated sync character(s) - a background-sync convenience never meant to gate an ad-hoc lookup. Replaced with _find_tokens(scope_name, corporation_id=None), which searches ANY character anywhere in this Alliance Auth install that holds a token with the needed scope (esi-universe.read_structures.v1 / esi-corporations.read_structures.v1), not just the plugin's own sync character(s). When the structure was seen before, its cached owner corp's characters are tried first (most likely to still have access), then every other available character as a fallback, so an arbitrary structure belonging to any corp - including ones we have no sync config for - can still resolve if any member anywhere has visibility into it. The corp-detail step now also derives its target corporation from the live lookup's own owner_id (or the cache) rather than looping every CorporationSyncConfig row.
<!-- SECTION:NOTES:END -->
