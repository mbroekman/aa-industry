---
id: TASK-123
title: Implement Direct ESI Market Pricing (Option 1) & Deprecate Fuzzwork
status: Done
assignee: []
created_date: '2026-09-04 13:28'
updated_date: '2026-09-04 13:39'
labels: []
dependencies: []
ordinal: 113000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Implementation plan and execution for replacing the Fuzzwork market API with direct CCP ESI market orders querying (Option 1 from doc-9) with multi-tiered caching, asynchronous batching, and custom percentile calculation.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Complete architecture and implementation plan in implementation_plan.md,Create direct ESI client for market orders (/markets/{region_id}/orders/),Implement local and Redis caching to prevent rate limiting and latency,Implement percentile calculation (5th percentile / lowest sell),Replace all Fuzzwork references across pricing_engine and BOM engine,Ensure unit tests pass with mocked ESI responses

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented direct CCP ESI market orders client in pricing_engine.py using /markets/10000002/orders/?order_type=sell&type_id=X. Added calculate_percentile_price with volume-weighted 5th percentile calculation on Jita 4-4 station (60003760). Integrated concurrent ThreadPoolExecutor for multi-item quotes with connection pooling. Added 1-hour Django caching, EveMarketPrice fallback, Celery background warming task in tasks/orders.py, and cleaned up UI references/tooltips. All 134 test suite tests passing.

<!-- SECTION:NOTES:END -->
