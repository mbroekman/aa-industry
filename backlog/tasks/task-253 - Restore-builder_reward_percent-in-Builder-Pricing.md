---
id: TASK-253
title: Restore builder_reward_percent in Builder Pricing
status: Done
assignee:
  - >-
    builder_reward_percent restored on CorpPricingConfig model and migration
    0078 created
  - builder_reward_percent restored in CorpPricingConfigForm
  - Value % column restored in Builder Pricing tab in director_config.html
  - pricing_engine restored to calculate value incentive in hybrid formula
  - All tests pass
created_date: '2026-10-21 12:18'
updated_date: '2026-10-21 12:22'
labels: []
dependencies: []
ordinal: 427000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Revert the removal of builder_reward_percent: restore model field, forms, templates, pricing calculation, tests, and generate forward migration 0078.
<!-- SECTION:DESCRIPTION:END -->
