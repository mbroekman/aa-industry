---
id: doc-10
title: 'Feature Proposal: AI Market Manager'
type: specification
created_date: '2026-08-25 16:38'
updated_date: '2026-08-25 16:38'
---

# Feature Proposal: AI Market Manager

**Date:** August 25, 2026
**Type:** Feature Specification / Proposal
**Status:** Proposed

## 1. Executive Summary

As corporations and alliances scale their industrial operations, manually identifying profitable items, calculating build margins, and generating production orders becomes a massive administrative bottleneck.

This document proposes the development of an **"AI Market Manager"** module for the Industry Reforged tool. This system will allow Directors to define a "basket of goods" (e.g., specific ships, modules, or doctrine fits). The Market Manager will then automatically analyze real-time market data (velocity, profitability, availability) and autonomously inject production orders into the Corporate Build System when predetermined thresholds are met.

## 2. Core Capabilities

The AI Market Manager will operate autonomously based on three main pillars: **Market Velocity**, **Profitability Analysis**, and **Stock Availability**.

### 2.1 The "Basket of Goods"

- **Definition:** Directors can create configurable groups of items (Baskets) that the corporation intends to keep stocked in specific markets (e.g., staging systems, trade hubs).
- **Target Configurations:** For each item in the basket, Directors set:
  - `Target Stock Level`: The minimum quantity the market should always have available.
  - `Restock Threshold`: The stock level that triggers an automatic reorder.
  - `Target Market`: The specific ESI Location ID (station or citadel) to monitor.

### 2.2 Intelligent Market Metrics

Instead of blindly building items, the system evaluates the following before generating an order:

1. **Market Velocity (Volume & Movement):**

   - How fast is the item selling in the target market?
   - The AI will analyze the 14-day or 30-day ESI market history to determine average daily volume (ADV). If velocity drops below a certain threshold, the system may delay restocking to prevent capital lockup.

1. **Profitability (Margin & Costing):**

   - Calculates the exact build cost (using the local corporate Blueprint, ME/TE, Rig setups, and raw material replacement costs).
   - Compares the build cost against the current Jita Sell or Local Sell price.
   - If the `Profit Margin %` is below the Director-defined threshold (e.g., < 15%), the system aborts the build order and alerts the Director of the unprofitability.

1. **Availability (Current Stock & In-Flight):**

   - Scans existing corporate hangars and active market sell orders posted by the corporation.
   - Cross-references existing open Production Tasks (in-flight builds). If 50 items are required but 30 are already queued in the build system, it will only order the remaining 20.

### 2.3 Automated Order Injection

Once an item passes all checks (Stock is low, Velocity is acceptable, Profitability is confirmed), the AI Market Manager generates a **Production Task** inside the Industry Reforged tool.

- **Smart Routing:** The generated order is automatically flagged with the optimal facility (based on corp blueprint location and structure rig bonuses).
- **Notification:** Posts a Webhook (Discord) notification: *"AI Market Manager: Authorized 50x Muninn builds for staging. Expected Margin: 22%."*

______________________________________________________________________

## 3. Workflow & Technical Implementation

### Step-by-Step Execution (Celery Beat Task)

1. **Scheduled Trigger:** A daily or hourly Celery task triggers the `MarketManager.evaluate()` function.
1. **Data Ingestion:**
   - Pulls local active Sell Orders via ESI to check current availability.
   - Fetches ESI Market History for velocity calculations.
   - Runs the `pricing_engine` to determine current raw material costs.
1. **Evaluation Loop:** Iterates through every item in every active Basket.
1. **Decision Matrix:** Applies the logic checks (Stock vs Target, Margin > Min Margin, Velocity > Min Velocity).
1. **Action:** Generates standard `ProductionTask` models and commits them to the database for industrial players to claim.

### Data Requirements & APIs

- **ESI Market Orders endpoint:** To check competitor prices and current corporate listings.
- **ESI Market History endpoint:** Crucial for calculating daily market volume (velocity).
- **Internal Pricing Engine (Fuzzwork/SDE):** To calculate the accurate Bill of Materials replacement cost.

______________________________________________________________________

## 4. User Interface

The module will introduce a new Director-level dashboard:

1. **Basket Manager:** A simple CRUD interface to add/remove items to baskets and set thresholds.
1. **AI Audit Log:** A historical ledger explaining *why* the AI did or didn't create an order.
   - *Example:* "Skipped Paladin. Margin: -2% (Requires 10%)."
   - *Example:* "Ordered 10,000x Scorch M. Stock: 2k, Target: 15k."
1. **Opportunity Scanner:** A proactive view where the AI suggests items to add to the basket based on high local velocity and high build margins across the region.

## 5. Next Steps

1. Review and refine the logical thresholds required for the decision matrix.
1. Ensure ESI tokens for the corporation have the necessary scopes (`esi-markets.read_corporation_orders.v1`, `esi-markets.structure_markets.v1`).
1. Prototype the velocity tracking against the ESI History API to ensure rate limits are respected.
