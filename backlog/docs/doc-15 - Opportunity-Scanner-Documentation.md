---
id: doc-15
title: 'Opportunity Scanner Documentation'
type: guide
created_date: '2026-09-12 09:02'
updated_date: '2026-09-12 09:02'
---

# Opportunity Scanner

## Overview

The Opportunity Scanner is a feature within the AI Market Manager module of Industry Reforged. Its purpose is to **automatically discover profitable manufacturing opportunities** for a corporation by analyzing real-time market data from EVE Online's ESI API.

Rather than requiring directors to manually browse the market and compare prices against build costs, the scanner does this at scale — evaluating every item the corporation is capable of building and surfacing only those that meet configurable profitability and volume thresholds.

---

## What the Scanner Does

### 1. Identifies Buildable Items

The scanner starts by determining which items the corporation can manufacture. It does this by:

1. Fetching all **Corporate Blueprints** (`CorpBlueprint`) owned by the corporation.
2. Cross-referencing those blueprints with the EVE SDE (`EveIndustryActivityProduct`) to find which product types they produce (Manufacturing activity 1 and Reaction activity 11).
3. Filtering the resulting product types against the **item categories** selected in the scanner configuration (e.g., Ships, Modules, Drones, Charges).

This yields a list of **candidate items** — products the corporation can build and that fall within the scanner's category scope.

### 2. Excludes Items Already in Baskets

Any item that already exists as a `BasketItem` in one of the corporation's active Baskets is excluded. This prevents the scanner from re-surfacing items that are already being actively managed by the AI Market Manager's basket evaluation system.

### 3. Evaluates Market Velocity

For each candidate item, the scanner calls the ESI Market History endpoint for the configured region to calculate the **Average Daily Volume (ADV)** over the last 30 days.

Items with an ADV below the scanner's `min_velocity` threshold are discarded. This ensures the scanner only surfaces items with proven, sustained demand — avoiding capital lockup in slow-moving inventory.

### 4. Evaluates Profitability

For items that pass the velocity check, the scanner calculates the **estimated profit margin**:

- **Sell Price**: The current Jita sell price (or the configured target market price) is fetched via the pricing engine.
- **Build Cost**: Estimated using the EVE-adjusted price from `EveMarketPrice`. If unavailable, a fallback of 80% of the sell price is used.
- **Margin**: `((Sell Price - Build Cost) / Build Cost) × 100%`

Items with a margin below the scanner's `min_profit_margin` threshold are discarded.

### 5. Records Opportunities

Items that pass both the velocity and profitability checks are stored as `MarketOpportunity` records in the database. Each record captures:

| Field | Description |
|-------|-------------|
| `corporation` | The corporation the opportunity belongs to |
| `eve_type` | The specific item type |
| `region_id` | The market region that was scanned |
| `target_hub` | The specific structure/station, if configured |
| `velocity` | Average Daily Volume (30-day) |
| `margin` | Estimated profit margin percentage |

Old opportunity records for the same items/region/hub are replaced with fresh data on each scan.

---

## What Happens When an Opportunity Is Found

When the scanner discovers an item that meets all thresholds, two things can happen depending on the scanner's configuration:

### Scenario A: Passive Discovery (No Auto-Add Basket)

If the scanner does **not** have an `auto_add_basket` configured, discovered opportunities are simply stored in the `MarketOpportunity` table. Directors can then:

- View them on the **Opportunities** page (`/industry/ai/opportunities/`)
- Sort by margin and velocity to identify the most promising items
- Manually copy item names and add them to a Basket

This is a **read-only, advisory mode** — the scanner surfaces data but takes no automated action.

### Scenario B: Automated Basket Injection (Auto-Add Basket)

If the scanner has an `auto_add_basket` configured (linked to an existing Basket), the scanner **automatically creates a new `BasketItem`** in that basket for each discovered opportunity. The process:

1. **Target Stock Level** is calculated: `velocity × target_stock_days` (rounded up, minimum 1). For example, if an item sells 5 units/day and `target_stock_days` is 7, the target stock is set to 35.

2. **Batch Size** is calculated: `velocity × (target_stock_days / 2)` (rounded up, minimum 1). This provides a reasonable reorder quantity.

3. A `BasketItem` is created linking the item to the target basket with the calculated stock level and batch size.

4. The system checks current **corporation inventory** and **in-flight production tasks** for this item and logs the current state.

5. An `AIMarketLog` entry is created with the action `"Auto-Added by Scanner"`, recording the margin, current stock, and the reasoning.

Once the item is in a Basket, the standard **Basket Evaluation** process takes over on its next scheduled run. The basket evaluator will:

- Check if current stock (inventory + in-flight) is below the target stock level
- Re-verify profitability at the time of evaluation
- If stock is low and margin is acceptable, generate a **Production Task** for industrialists to claim
- Post a **Discord webhook notification** if configured

This creates a fully automated pipeline: **Scanner discovers → Basket manages → Production tasks are generated → Builders claim and manufacture**.

---

## Missing Blueprint Report

If the `scan_missing_blueprints` option is enabled, the scanner performs an additional analysis:

1. It identifies all items in the selected categories that **could** be manufactured (blueprints exist in the game) but for which the corporation **does not own** the required blueprint.
2. These items are evaluated with the same velocity and profitability checks.
3. Qualifying items are stored as `MissingBlueprintOpportunity` records.

This report helps directors make informed blueprint acquisition decisions by showing: *"If you purchased blueprint X, you could manufacture item Y at a Z% margin with W units/day demand."*

Missing blueprint reports are accessible from the scanner's action buttons on the AI Manager Dashboard (the warning triangle icon).

---

## Scanner Configuration

Each scanner is configured with the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `name` | — | A friendly name for the scanner |
| `corporation` | — | The corporation this scanner operates for |
| `is_active` | `true` | Whether the scanner runs on its automatic schedule |
| `target_region_id` | — | ESI Region ID to scan (e.g., 10000002 for The Forge) |
| `target_hub` | — | Optional specific structure/station to focus on |
| `min_profit_margin` | `15.0%` | Minimum acceptable profit margin |
| `min_velocity` | `1.0` | Minimum Average Daily Volume (units/day) |
| `categories` | — | List of EVE item category IDs to scan (Ships, Modules, etc.) |
| `auto_add_basket` | `null` | Optional: automatically add opportunities to this basket |
| `target_stock_days` | `7` | Days of stock to maintain when auto-adding (used with velocity) |
| `run_interval_hours` | `24` | How often the scanner should run automatically |
| `scan_missing_blueprints` | `false` | Also report profitable items without owned blueprints |

Either `target_region_id` or `target_hub` must be set (or both).

---

## Scheduling and Execution

### Automatic Execution

A Celery Beat task (`run_all_active_scanners`) runs every hour. On each run, it checks all active scanners:

- If a scanner has never run, or if enough time has elapsed since its `last_run` (based on `run_interval_hours`), the scan is queued as a background Celery task.
- The scanner's `is_running` flag is set to `true` while executing and reset to `false` upon completion.

### Manual Execution

Directors can trigger a scan immediately from the AI Manager Dashboard by clicking the **Play** button next to a scanner. This queues the scan as a background task regardless of the interval schedule.

### Execution Logs

Every scanner execution produces an `OpportunityScannerLog` entry containing:

- Number of items scanned
- Number of opportunities found
- Number of items auto-added to a basket (if applicable)
- Detailed summary text

Logs are viewable from the scanner's action buttons on the dashboard.

---

## End-to-End Workflow Example

1. **Director creates a scanner**: "Delve Ships Scanner" targeting the Delve region, scanning the Ships category, with a 20% minimum margin and 2 units/day minimum velocity. Auto-add is linked to a basket called "Delve Doctrine Ships".

2. **Scanner runs** (automatically every 24 hours, or manually triggered):
   - Finds 150 ship types the corporation can build
   - Excludes 30 that are already in a basket
   - Evaluates 120 remaining candidates
   - 8 items meet both the velocity and margin thresholds

3. **Opportunities stored**: 8 `MarketOpportunity` records are created/updated.

4. **Auto-add triggers**: For each of the 8 items, a `BasketItem` is created in the "Delve Doctrine Ships" basket with stock levels calibrated to 7 days of demand.

5. **Basket evaluation runs** (on its own schedule):
   - Checks the 8 newly added items
   - Finds that 5 are below their target stock level
   - Re-confirms profitability
   - Creates 5 `ProductionTask` records for builders to claim
   - Sends a Discord notification listing the new production tasks

6. **Builders** see the tasks on their Industrialist Dashboard, claim them, and begin manufacturing.

---

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Corp Blueprints │────▶│  Candidate Items  │────▶│  Velocity Check │
│  (CorpBlueprint) │     │  (filtered by     │     │  (ESI Market    │
│                  │     │   categories)     │     │   History API)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                  Items with ADV ≥ min_velocity
                                                           │
                                                           ▼
                                                 ┌─────────────────┐
                                                 │ Profitability   │
                                                 │ Check (Pricing  │
                                                 │ Engine)         │
                                                 └────────┬────────┘
                                                           │
                                                  Items with margin ≥ min_profit_margin
                                                           │
                                            ┌──────────────┼──────────────┐
                                            ▼                             ▼
                                  ┌─────────────────┐          ┌─────────────────┐
                                  │ MarketOpportunity│          │ Auto-Add to     │
                                  │ (stored for      │          │ Basket          │
                                  │  viewing)        │          │ (if configured) │
                                  └─────────────────┘          └────────┬────────┘
                                                                        │
                                                                        ▼
                                                              ┌─────────────────┐
                                                              │ Basket Evaluator │
                                                              │ (checks stock,  │
                                                              │  re-checks      │
                                                              │  profitability)  │
                                                              └────────┬────────┘
                                                                        │
                                                                        ▼
                                                              ┌─────────────────┐
                                                              │ ProductionTask  │
                                                              │ (for builders   │
                                                              │  to claim)      │
                                                              └────────┬────────┘
                                                                        │
                                                                        ▼
                                                              ┌─────────────────┐
                                                              │ Discord Webhook │
                                                              │ Notification    │
                                                              └─────────────────┘
```

---

## Permissions

The Opportunity Scanner requires one of the following permissions:

- `industry_reforged.director_access`
- `industry_reforged.corp_access`

These are the same permissions required to access the AI Market Manager Dashboard.
