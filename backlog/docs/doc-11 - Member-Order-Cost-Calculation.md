---
id: doc-11
title: Member Order Cost Calculation
type: guide
created_date: '2026-08-28 22:45'
updated_date: '2026-08-28 22:46'
---

# Member Order Cost Price Calculation

The final cost price of a `MemberOrder` is calculated by the pricing engine in `industry_reforged/utils/pricing_engine.py` following a fixed sequence of steps:

## 1. Base Price (Market Price via Fuzzwork API)

By default, the market price in **Jita** (Station ID 60003760) is retrieved for each item using the Fuzzwork API. Specifically, it uses the **5% percentile sell price** as this provides a more stable value than the absolute minimum sell price. This fetched data is cached for one hour to prevent API rate limiting.

## 2. Manual Price Overrides (CorpItemConfig)

If a Corporation has explicitly configured a `manual_price` for a specific item (via `CorpItemConfig`), this fixed price will directly override the fetched Jita market price.

## 3. Discounts (CorpPricingConfig & CorpTypeDiscount)

Once the base price is determined (either via Fuzzwork or manually), the engine applies discounts:

- It first checks if there is a **specific discount** configured for this exact item type (`CorpTypeDiscount`).
- If no specific discount exists, it falls back to the **default discount** of the Corporation (`default_discount_percent` from `CorpPricingConfig`).

## 4. Final Calculation

For each individual item, the price is calculated as:
`Price per unit = (Base Price) * (100% - Discount %)`

The total order price (`total_price` field on `MemberOrder`) is the sum of `(Price per unit * Quantity)` for all items in the order.
