---
id: TASK-144
title: Fix auto-refresh session timeout
status: Done
assignee: []
created_date: '2026-09-08 14:29'
updated_date: '2026-09-08 14:31'
labels: []
dependencies: []
ordinal: 186000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Automatic refresh causes session timeouts because Django does not extend session expiry on standard GET requests unless modified. Add request.session.modified = True to dashboard views to keep the session alive.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Session stays alive while auto-refreshing dashboard pages
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added request.session.modified = True to the main dashboard views (Personal, Corporate, Industrialist, AI Manager) to ensure the Django session expiry is extended whenever the auto-refresh script reloads the page.
<!-- SECTION:NOTES:END -->
