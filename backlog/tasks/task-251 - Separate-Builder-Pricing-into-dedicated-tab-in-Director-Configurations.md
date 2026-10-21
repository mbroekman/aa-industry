---
id: TASK-251
title: Separate Builder Pricing into dedicated tab in Director Configurations
status: Done
assignee: []
created_date: '2026-10-21 10:52'
updated_date: '2026-10-21 10:56'
labels: []
dependencies: []
priority: medium
type: enhancement
ordinal: 425000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Separate builder reward / pricing configurations from global customer pricing into a dedicated 'Builder Pricing' tab in director_config.html. Update navigation, tables, and back_hash redirects accordingly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dedicated 'Builder Pricing' tab exists in director_config.html with detailed columns for Base Fee, Hourly Rate, Value Incentive %, Floor, Cap, and Priority Multipliers
- [x] #2 'Global Pricing' tab focuses strictly on customer pricing, valuation methods, margin floors, and system taxes
- [x] #3 Editing builder pricing configuration redirects back to #builder-pricing tab
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Separated Builder Pricing from Global Pricing into its own dedicated tab in director_config.html with complete overview of Base Fee, Hourly Rate, Value Incentive %, Safety Bounds (Floor/Cap), and Priority Multipliers, and updated view redirect and back links to #builder-pricing.
<!-- SECTION:FINAL_SUMMARY:END -->
