---
id: TASK-158
title: Implement ML Data Ingestion
status: Done
assignee: []
created_date: '2026-09-12 13:57'
updated_date: '2026-09-12 14:06'
labels: []
dependencies: []
ordinal: 161000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the stub in sync_market_data_to_ml_service with actual data extraction from Django models to feed the LightGBM model.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 - [ ] Extract relevant transaction/price data from Django\n- [ ] Post JSON payload to /ingest\n- [ ] Trigger /retrain
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented internal MemberOrder extraction and external ESI Market History extraction for the AI forecasting service.
<!-- SECTION:NOTES:END -->
