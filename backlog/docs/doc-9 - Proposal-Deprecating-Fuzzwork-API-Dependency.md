---
id: doc-9
title: 'Proposal: Deprecating Fuzzwork API Dependency'
type: specification
created_date: '2026-08-25 16:36'
updated_date: '2026-08-25 16:39'
---

# Proposal: Deprecating Fuzzwork API Dependency

**Date:** August 25, 2026
**Topic:** Alternatives for replacing the third-party Fuzzwork API dependency for market pricing and Bill of Materials (BOM) logic within the Industry Reforged tool.

## 1. Background

Currently, the application relies on the Fuzzwork API (`https://market.fuzzwork.co.uk/aggregates/`) to fetch real-time "Jita 5% Sell" prices for materials (PI, Moon goo, Minerals, etc.) and to process Bill of Materials fallback options.

While Fuzzwork is highly convenient because it aggregates official EVE Online (ESI) market data and allows bulk querying, it introduces a third-party dependency. If Fuzzwork experiences downtime, our tool's pricing engine will fail or fall back to 0 ISK unless manual prices are set.

This document outlines three viable options for removing the Fuzzwork dependency and transitioning to first-party (CCP ESI) or fully localized data.

______________________________________________________________________

## 2. Options for Replacement

### Option 1: Direct ESI API Integration (First-Party)

Instead of relying on Fuzzwork's aggregated endpoint, we rewrite the `pricing_engine.py` to communicate directly with the official CCP ESI API (`/markets/10000002/orders/?type_id=XXX`).

- **Pros:**
  - 100% official data straight from the source.
  - No third-party dependencies whatsoever.
  - We control the exact percentile calculation (e.g., 5% sell, 10% sell, lowest sell).
- **Cons:**
  - **Performance & Network Overhead:** Fuzzwork allows querying up to 100 items in a single HTTP request. The ESI API strictly requires **1 request per item type**. Calculating a quote for a blueprint with 40 distinct materials requires 40 individual ESI requests.
  - **Implementation Cost:** Requires building local caching, asynchronous fetching, and mathematical aggregation logic (sorting and calculating percentiles) to prevent the user interface from slowing down.

### Option 2: Local Database (EVE Universe Daily Averages)

The plugin is already built on top of `django-eveuniverse`. This package automatically synchronizes daily with the ESI API to fetch the official "Average Price" and "Adjusted Price" for every item in the game and stores it in the local database.

- **Pros:**
  - **Extremely Fast:** Zero network calls are required when loading a quote or evaluating prices; all data is fetched locally from the database.
  - **Resilient:** Unaffected by temporary ESI or third-party outages during the day.
- **Cons:**
  - **Pricing Accuracy:** EVE Universe provides a daily "Market Average", not the precise live "Jita 5% Sell" price. In highly volatile markets, the payout prices may deviate from the actual immediate replacement costs in Jita.

### Option 3: Manual Pricing Exclusivity

We completely disable automated external pricing and enforce that Directors manually assign a base price for all raw materials via the `Corp Item Config` menu.

- **Pros:**
  - Complete financial control for the Corporation/Alliance.
  - Predictable payouts and profit margins that do not fluctuate with external market spikes.
- **Cons:**
  - **High Maintenance:** Directors will bear the administrative burden of monitoring the market and manually updating prices whenever market shifts occur.

______________________________________________________________________

## 3. Recommendation

If the primary goal is to completely remove the Fuzzwork dependency without sacrificing automation:

1. **Short-Term / Low Effort:** Implement **Option 2**. It leverages the existing `django-eveuniverse` ecosystem. This is highly recommended if the corporation leadership is comfortable with using daily average prices rather than exact live Jita sell orders.
1. **Long-Term / High Accuracy:** Implement **Option 1**. This is recommended if the "Jita 5% Sell" accuracy is strictly required. This will necessitate a moderate rewrite of the `pricing_engine.py` to include robust Celery tasks or localized caching to handle the increased volume of ESI requests without impacting user experience.
