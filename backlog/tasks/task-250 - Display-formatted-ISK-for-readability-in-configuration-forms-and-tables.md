---
id: TASK-250
title: Display formatted ISK for readability in configuration forms and tables
status: Done
assignee: []
created_date: '2026-10-21 10:26'
updated_date: '2026-10-21 10:38'
labels: []
dependencies: []
priority: medium
type: enhancement
ordinal: 424000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add dynamic formatted ISK preview badges under numeric input fields in director configuration forms and ensure ISK configuration tables cleanly display formatted ISK values to improve readability and avoid zero-counting errors.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dynamic live preview helper displays formatted ISK (with commas and human-readable abbreviations like K, M, B) below ISK input fields in director config forms
- [x] #2 Director pricing configuration table shows all ISK values cleanly formatted including hourly rate, base fee, min reward floor, and max reward cap
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented dynamic formatted ISK live preview in director configuration forms (director_config_form.html) with .isk-input widgets in forms.py, updated pricing table in director_config.html to display Floor alongside Base and Cap, and verified with 285 passing pytest tests.
<!-- SECTION:FINAL_SUMMARY:END -->
