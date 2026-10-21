---
id: TASK-246
title: 'Buyback: fix refining-rate, price-type, and contract-recipient gaps'
status: Done
assignee: []
created_date: '2026-10-16 08:49'
updated_date: '2026-10-16 08:49'
labels: []
dependencies: []
ordinal: 422000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Comparing BuybackProgram against the source project (allianceauth-buyback-program, see doc-18) surfaced ~15 missing settings. Most are optional and deferred, but 3 are real correctness/UX defects: (1) reprocessed-value appraisal was hardcoded at 100% refining efficiency with no director control, systematically overpaying for ore/loot valued via that path; (2) the member-facing contract_detail page never told the member which corporation to address the in-game contract to, even though the ESI matching logic already expects a specific receiver; (3) appraisals were always based on Jita sell price with no Buy/Sell/Split option, despite get_market_prices already fully supporting buy-side pricing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 BuybackProgram gets refining_rate (default 90%) and price_type (Buy/Sell/Split, default Sell) fields, exposed in the director config form
- [x] #2 calculate_buyback_quote/get_item_value_variants use refining_rate to scale reprocessed valuations and price_type to pick the market pricing basis
- [x] #3 contract_detail.html shows the drop-off location and contract recipient (corporation) in the create-contract instructions
- [x] #4 New/updated tests cover refining_rate scaling, price_type SELL/BUY/SPLIT, and the pre-existing round-trip test; full suite green
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented via migration 0075. Full gap list vs. the source project documented in this task's description; NPC loot price overrides, allow_unpacked_items, per-item allowlist, wallet FK, tracking_prefill, hauling_fuel_cost, Discord per-program config, and group/state visibility restrictions were explicitly scoped out this round (user chose 'correctness only') and remain candidates for a follow-up task.
<!-- SECTION:NOTES:END -->
