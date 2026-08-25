---
id: TASK-95
title: Investigate missing reaction jobs on My Corporate Jobs tab
status: Done
assignee: []
created_date: '2026-08-25 14:11'
updated_date: '2026-08-25 14:19'
labels: []
dependencies: []
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Reopened issue #37. Jobs might be executed in a different structure/facility than where the main production happens. The system currently might only be filtering or showing jobs for the primary structure, ignoring jobs from secondary structures.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 - Reaction jobs from other known structures are visible in the My Corporate Jobs tab.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Investigated job visibility logic. The system does not filter jobs by structure/facility for ESI syncing or for displaying on the My Corporate Jobs tab. Standalone jobs were being hidden if they were unlinked and the user had no active claimed tasks (due to oldest_claim_date being None). Fixed this by ensuring all active and ready jobs bypass the date filter and are always shown on the My Corporate Jobs tab.

<!-- SECTION:NOTES:END -->
