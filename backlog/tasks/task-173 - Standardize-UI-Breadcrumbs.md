---
id: TASK-173
title: Standardize UI Breadcrumbs
status: Done
assignee: []
created_date: '2026-09-14 19:48'
updated_date: '2026-09-14 19:52'
labels: []
dependencies: []
ordinal: 349000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update all templates in industry_reforged to use a uniform breadcrumb and header structure matching the ai_manager/scanner/edit template.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Identify all templates, Replace custom headers with standard breadcrumb layout, Verify alignment
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated 20 templates in industry_reforged to replace custom <h3> or <h2> headers with a unified Bootstrap breadcrumb navigation block matching the Opportunity Scanner page. Adjusted margin and verified action buttons align nicely with the page titles. Includes the missed scanner_logs.html.
<!-- SECTION:NOTES:END -->
