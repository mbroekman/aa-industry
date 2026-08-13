---
id: TASK-64
title: Hide subitems in Claimed Jobs overview
status: Done
assignee: []
created_date: '2026-08-11'
updated_date: '2026-08-11'
labels: ['bug', 'ui']
dependencies: []
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

In de "Claimed Jobs" overview worden momenteel nog sub-items getoond. Omdat de Job Market recent is aangepast om alleen root items (`bom_parent__isnull=True`) te tonen, en de Build Steps al alle details tonen, is het wenselijk om in het Claimed Jobs overzicht ook alleen de hoofditems te laten zien.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Voeg `bom_parent__isnull=True` toe aan de querie voor actieve ("IN_PRODUCTION") geclaimde taken.
- [x] #2 Voeg `bom_parent__isnull=True` toe aan de querie voor voltooide ("COMPLETED") geclaimde taken, indien van toepassing voor consistency.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added `bom_parent__isnull=True` to both `my_tasks_qs` (IN_PRODUCTION) and `my_completed_tasks` (COMPLETED) queries in `industry_reforged/views/industrialist.py`. This ensures that only the root items are displayed on the Claimed Jobs overview, preventing clutter from all the sub-tasks which are already viewable within the Build Steps tab.

<!-- SECTION:NOTES:END -->
