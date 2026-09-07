---
id: TASK-127
title: Hub selection based on corp and alliance rights
status: Done
assignee: []
created_date: '2026-09-05 16:23'
updated_date: '2026-09-06 10:57'
labels: []
dependencies: []
ordinal: 122000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Update BasketForm and AIManagerForm to allow selecting a hub (target_hub) based on the rights of the corporation and alliance, rather than just the user's corporations.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 1. target_hub queryset includes structures owned by user's corps

2. target_hub queryset includes structures owned by corps in the same alliance as the user's corps
1. target_hub dropdown displays correctly in AI manager/Basket

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented native KnownLocation model to track distinct asset locations from ESI, avoiding the need for full CorpAsset sync or corptools dependencies. Added celery task to resolve names dynamically.

<!-- SECTION:NOTES:END -->
