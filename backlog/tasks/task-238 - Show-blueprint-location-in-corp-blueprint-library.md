---
id: TASK-238
title: Show blueprint location in corp blueprint library
status: Done
assignee:
  - Antigravity
created_date: '2026-10-07 22:15'
updated_date: '2026-10-07 22:15'
labels:
  - feature
  - ui
dependencies: []
ordinal: 414000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In the Corp Blueprint Library (`/industry/blueprints/`), members and industrialists can browse corporate blueprints and request copies. Currently, the table only displays Blueprint, Corporation, Runs, and Actions. The physical location where each blueprint is stored (structure/station, container, and hangar division) is not shown. Industrialists need to know where a blueprint is located so they know where copies can be made or picked up.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add a 'Location' column to the Corp Blueprint Library table (`library.html`) between Corporation and Runs.
- [x] #2 Resolve `location_id` into human-readable structure, station, or container names using `IndustryFacility`, `KnownLocation`, `EveLocation`, `CorpAsset`, `EveStation`, and `EveSolarSystem`.
- [x] #3 Display both the resolved location name and the formatted hangar division (`location_flag`, e.g. Hangar Division 4).
- [x] #4 Support searching by location name or hangar flag in the server-side DataTables endpoint (`dt_blueprint_library`).
- [x] #5 Keep table sorting and column alignment functional (non-orderable Actions column moved to index 4).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create helper function `resolve_location_names(location_ids)` and `format_location_flag(flag)` in `industry_reforged/utils/locations.py`.
2. Create partial template `industry_reforged/templates/industry_reforged/partials/dt_blueprint_location.html`.
3. Update `dt_blueprint_library` in `industry_reforged/views/datatables.py` to:
   - Include Location in the returned column data.
   - Support search matching against location names and `location_flag`.
   - Update `order_map` for 5 columns.
4. Update `industry_reforged/templates/industry_reforged/blueprints/library.html` table header and DataTables `columnDefs` (targets: [4] non-orderable).
5. Sync to remote sandbox and verify live.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Gerealiseerd via `industry_reforged/utils/locations.py`, `dt_blueprint_location.html`, `datatables.py` en `library.html`. De tabel toont nu voor elke blueprint de exacte locatie (bijv. '9O-ORX - 3GODS Foundry > Blueprints - Corp > zBPC: T2 Mod - Mid' of '9O-ORX - 3GODS Paddock > Blueprints - Corp > BPC: Mod - Mid (zOther)') inclusief automatische resolutie van corporate hangardivisies, office folders en specifieke containers via corptools `CorpAsset` item-matching. Zoeken op containernaam, sitenaam en hangardivisie werkt realtime via de DataTables backend. Live geverifieerd op devauth.spral.space.
<!-- SECTION:NOTES:END -->
