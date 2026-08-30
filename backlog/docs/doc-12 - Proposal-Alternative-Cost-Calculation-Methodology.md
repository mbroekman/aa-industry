---
id: doc-12
title: 'Proposal: Alternative Cost Calculation Methodology'
type: other
created_date: '2026-08-30 11:13'
updated_date: '2026-08-30 11:13'
---

# Proposal: Alternative Cost Calculation Methodology (BOM-Based Pricing)

## Executive Summary

Currently, the Alliance Auth Industry Reforged module determines the order price and builder payouts based primarily on the Fuzzwork Jita 5% Sell price of the **end product**. While this method is simple and easy to understand for buyers, it poses significant risks: it does not reflect the actual cost of manufacturing. If the Jita market for a specific ship or module crashes below its material cost, the corporation or builder manufactures at a net loss.

This document proposes transitioning to (or integrating) a **Bottom-Up Bill of Materials (BOM) Cost Model** to calculate the "True Cost" of manufacturing.

## Current Methodology & Risks

Based on the current implementation (`pricing_engine.py` and `doc-2`):

- **Quote / Buyer Price:** `Jita Sell * (1 - Corp Discount)`
- **Builder Payout:** `Jita Sell * Builder Reward %`
- **Risk:** Profit margins are entirely dependent on the volatility of the Jita market. For many items in EVE Online (especially T1 ships), the Jita sell price is often lower than the raw material cost due to veteran players building with perfect skills/structures or liquidating assets. If a buyer orders a doctrine ship priced below its material cost, the corporation subsidizes the loss.

## Proposed Alternatives

### 1. The True Material Cost (BOM-Based) Model

Calculate the exact cost to build an item from the bottom up, using the raw materials.

**How it works:**

1. Generate the exact material requirements using the existing `bom_engine.py` (which already perfectly accounts for ME, Rigs, and Job Chunking).
1. For each required material, determine its Unit Price. This can be:
   - **Fuzzwork Jita Buy Price:** Reflects the cost to instantly sell the minerals in Jita, representing the opportunity cost.
   - **Corporate Buyback Program Price:** E.g., Jita Buy - 10%. This reflects the actual internal cost of acquiring the minerals from corp members.
1. Sum the material costs: `Total Material Cost = Sum(Material Qty * Unit Price)`.
1. Add manufacturing overhead: Include estimated or actual Job Installation Fees (System Cost Index).
1. **Final True Cost = Total Material Cost + Installation Fees.**

**Pros:** Guarantees the corporation never builds at a loss. Margin is fixed and mathematically verifiable.
**Cons:** The calculated price might sometimes be higher than Jita sell for heavily over-supplied items.

### 2. The Hybrid "Safe Margin" Model

Combines the best of both worlds by protecting the corporation from taking losses while offering market-competitive prices when profitable.

**How it works:**

- Calculate the **True Material Cost** (Model 1).
- Calculate the **Jita Sell Quote** (Current Method).
- The final price charged to the buyer is `MAX(True Material Cost + Minimum Margin, Jita Sell - Discount)`.
- **Pros:** Offers members a discount on highly profitable items, but automatically enforces a price floor to prevent the corporation from bleeding ISK on unprofitable builds.

### 3. "Value-Added" Builder Payouts

Instead of paying builders a flat percentage of the final product's value, pay them based on the actual value they created (the profit margin).

**How it works:**

- `Added Value = Jita Sell Value - True Material Cost`
- `Builder Payout = Added Value * Reward %`
- **Pros:** Incentivizes builders to optimize their ME/TE and facility usage. Strongly discourages building items with a negative margin.
- **Cons:** If an item is critical for the alliance (e.g. doctrine) but has a negative margin, builders won't claim the job unless a manual bounty is added.

## Recommendation

It is highly recommended to implement the **True Material Cost (BOM-Based) Model** as the baseline metric for all internal accounting.

**Next Steps for Implementation:**

1. **Extend `pricing_engine.py`:** Create a new function `calculate_bom_cost(order_id)` that iterates through the output of `bom_engine.py`.
1. **Material Valuation:** Introduce a configuration setting to determine how raw materials are valued (e.g., "Use Jita Buy", "Use Jita Sell", or "Use Corp Manual Price").
1. **UI Updates:** Expose this "True Cost" on the Director Dashboard alongside the Jita Value so directors can instantly see the profit margin (or loss) of an order before accepting it.
1. **Transition to Hybrid:** Once the BOM cost is reliably calculating, introduce an option to set a "Minimum Margin Floor" to automatically protect against negative-margin orders.
