---
id: TASK-111
title: Fix Tatara/Fortizar mapping in forms.py
status: Done
assignee: []
created_date: '2026-08-31 09:23'
updated_date: '2026-08-31 09:45'
labels: []
dependencies: []
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

GitHub Issue #42: The tatara is shown as a fortizar in the CP configuration page. Although TASK-5 fixed the mapping in models/facilities.py, the mapping in forms.py is still swapped (35833 is mapped to Tatara instead of Fortizar, and 35836 to Fortizar instead of Tatara).

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 The mapping in forms.py correctly associates 35833 with Fortizar and 35836 with Tatara.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Swapped names for 35833 and 35836 in industry_reforged/forms.py

<!-- SECTION:NOTES:END -->
