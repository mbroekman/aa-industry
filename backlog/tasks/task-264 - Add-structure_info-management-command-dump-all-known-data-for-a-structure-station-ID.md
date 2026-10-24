---
id: TASK-264
title: >-
  Add structure_info management command (dump all known data for a
  structure/station ID)
status: Done
assignee: []
created_date: '2026-10-24 06:04'
updated_date: '2026-10-24 06:07'
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
<!-- SECTION:NOTES:END -->
