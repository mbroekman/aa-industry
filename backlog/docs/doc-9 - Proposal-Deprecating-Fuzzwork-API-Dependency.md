---
id: doc-9
title: 'Proposal: Deprecating Fuzzwork API Dependency'
type: specification
created_date: '2026-08-25 16:36'
updated_date: '2026-09-04 13:39'
---

# Proposal: Deprecating Fuzzwork API Dependency

**Date:** August 25, 2026 (Updated: September 4, 2026)
**Topic:** Alternatives for replacing the third-party Fuzzwork API dependency for market pricing and Bill of Materials (BOM) logic within the Industry Reforged tool.
**Status:** Accepted & Implemented (Option 1 - Direct ESI API Integration via TASK-123)

## 1. Background

Historically, the application relied on the third-party Fuzzwork API (`https://market.fuzzwork.co.uk/aggregates/`) to fetch real-time "Jita 5% Sell" prices for materials (PI, Moon goo, Minerals, etc.) and to process Bill of Materials fallback options.

While Fuzzwork was convenient because it aggregated official EVE Online (ESI) market data and allowed bulk querying, it introduced an external third-party point of failure.

______________________________________________________________________

## 2. Decision & Implementation: Option 1 (Direct ESI API Integration)

As part of **TASK-123**, **Option 1** was selected and implemented:

- **Direct ESI Client**: The `pricing_engine.py` communicates directly with the official CCP ESI API (`/markets/10000002/orders/?order_type=sell&type_id=XXX`).
- **Jita 5% Sell Percentile**: Filters sell orders at Jita IV - Moon 4 Navy Assembly Plant (`location_id=60003760`), sorts by price ascending, and calculates the true volume-weighted 5th percentile price.
- **Concurrent ThreadPoolExecutor**: Resolves the N-material network latency problem by querying missing material prices in parallel (max 15 threads) with HTTP connection pooling.
- **Multi-tiered Caching**: 1-hour Django cache TTL for positive market prices, 60s TTL for transient empty results, and periodic Celery background pre-warming (`task_pull_market_data`).
- **Resilient Fallback**: Automatically falls back to `EveMarketPrice` (daily adjusted/average prices from `django-eveuniverse`) if ESI is unreachable.

______________________________________________________________________

## 3. Evaluated Options

### Option 1: Direct ESI API Integration (Selected)

- **Pros:** 100% first-party official data, exact percentile control, no third-party downtime risk.
- **Cons:** Requires batching & threading for multi-item quotes (resolved via ThreadPoolExecutor + connection pooling).

### Option 2: Local Database (EVE Universe Daily Averages)

- **Pros:** Extremely fast, zero network calls during quotes.
- **Cons:** Less accurate in fast-moving volatile markets (used as secondary fallback).

### Option 3: Manual Pricing Exclusivity

- **Pros:** Complete fixed corporate financial control.
- **Cons:** High administrative maintenance burden on Directors.
