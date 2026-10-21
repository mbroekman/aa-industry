---
id: TASK-249
title: >-
  Implement Hybrid Builder Reward Model 2 with slot duration, caps, and priority
  multipliers
status: Done
assignee: []
created_date: '2026-10-21 09:17'
updated_date: '2026-10-21 09:32'
labels:
  - rewards
  - pricing
  - orders
  - industrialists
  - gamification
dependencies: []
priority: high
type: feature
ordinal: 423000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Hybrid Builder Reward Model 2 in aa-industry (industry_reforged). Replaces the legacy flat percentage reward with a balanced formula: Base Fee + (Slot Duration Hours * Hourly Rate) + (Item Value * Value %), bounded by a configurable Minimum Floor and Maximum Cap, and scaled by task Priority Multipliers.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add hybrid reward configuration fields to CorpPricingConfig and estimated duration to ProductionTask
- [x] #2 Create database migration and update CorpPricingConfigForm with validation
- [x] #3 Implement blueprint duration lookup and hybrid reward calculation with caching in pricing_engine
- [x] #4 Integrate hybrid reward calculation into quotes.py, director.py, and inventory tasks
- [x] #5 Update Director pricing settings UI and Industrialist job market UI with duration badge and tooltip
- [x] #6 Add comprehensive pytest unit tests for calculation, clamping, and multipliers
- [x] #7 Deploy and verify on devauth
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Successfully implemented Hybrid Builder Reward Model 2 in aa-industry (industry_reforged). Added configurable base install fee, slot hourly rate, value incentive percentage, minimum floor (2.5M ISK default), and maximum cap (75M ISK default) with priority multipliers. Integrated deterministic duration lookup with django-eveuniverse activity durations and updated quotes, director manual tasks, and inventory tasks. Verified all 282 tests pass and deployed live to devauth.
<!-- SECTION:FINAL_SUMMARY:END -->
