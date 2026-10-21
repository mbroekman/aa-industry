---
id: TASK-252
title: Remove builder_reward_percent from Builder Pricing
status: Done
assignee:
  - >-
    builder_reward_percent removed from CorpPricingConfig model and migration
    generated
  - builder_reward_percent removed from CorpPricingConfigForm
  - >-
    builder_reward_percent column removed from Builder Pricing tab in
    director_config.html
  - >-
    pricing_engine calculates reward from base fee + hourly rate clamped to
    floor/cap
  - All tests pass
created_date: '2026-10-21 11:37'
updated_date: '2026-10-21 11:47'
labels: []
dependencies: []
ordinal: 426000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Remove deprecated builder_reward_percent from CorpPricingConfig model, forms, templates, pricing calculation, and tests as builder compensation is now purely based on base fee + slot duration (hours) with floor/cap.
<!-- SECTION:DESCRIPTION:END -->
