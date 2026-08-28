---
id: TASK-99
title: Blueprint Request System
status: Done
assignee:
created_date: '2026-08-27 09:38'
updated_date: '2026-08-27 13:22'
labels: []
dependencies: []
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

A feature for integrating the blueprints of the corp so members can request copies. Includes functions for request accepted, request processed, and notifications via Discord and direct DMs.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Corp blueprints are visible to members
- [x] #2 Members can request copies of blueprints
- [x] #3 Requests can be accepted and processed
- [x] #4 Notifications are sent via Discord and direct DMs for status changes
- [x] #5 Approved requests automatically create a ProductionTask (Copying) for industrialists
- [x] #6 Request form allows specifying both quantity of copies and runs per copy
- [x] #7 Blueprint Library gets its own separate menu item next to Personal Industry
- [x] #8 Uses a separate discord webhook setting for blueprint requests

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed ESI model attribute parsing (aiopenapi3 pydantic objects vs dicts) and resolved blueprint cache refresh on empty DB.

<!-- SECTION:NOTES:END -->
