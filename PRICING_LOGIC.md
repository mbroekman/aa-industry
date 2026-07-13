# Industry Reforged: Pricing & Payout Logic

This document serves as a reference for how initial order quotes, Bill of Materials (BOM) values, and builder payouts are calculated within the Alliance Auth Industry Reforged plugin.

## 1. Initial Order Pricing (What the Buyer Pays)

When a corporate member requests an order (e.g., via a Multibuy paste or Fit import), the system calculates the "Quote" as follows:

1. **Base Market Price (`pricing_engine.py`)**
   The system makes a live call to the **Fuzzwork Market API** to fetch the Jita Sell price for each item. Specifically, it uses the 5% percentile sell price (Jita Station ID `60003760`). This provides a stable, realistic Jita sell value that ignores extreme outliers.

1. **Manual Price Overrides**
   If a Director has configured a manual price for a specific item in the **Corp Item Config** (Corporate Configurations -> Items), the system will completely bypass the Fuzzwork API for that item and use the configured manual price as the Base Price instead.

1. **Discounts**
   The base price is then subjected to Corporate Discounts defined in the `CorpPricingConfig`:

   - **Specific Type Discounts**: The system first checks if a specific discount applies to the requested item type (e.g., a custom 20% discount on Drakes).
   - **Default Corporate Discount**: If no specific discount exists, it falls back to the default discount percentage applied to the entire corporation.

1. **Final Line Total**
   The final price for the buyer is calculated as:
   `Final Line Total = (Base Price * (1 - Discount Percentage)) * Quantity`

______________________________________________________________________

## 2. BOM Prices & Gamification (What the Builder Earns)

Once an order is accepted by a Director, it is broken down into a Bill of Materials (BOM) represented as `ProductionTasks`. The pricing logic operates differently here to facilitate the builder ecosystem.

1. **Gamification Value (Task Value)**
   During the BOM generation, the system assigns a `gamification_value` to every individual Production Task. This value represents the total ISK value of the end-product of that specific task.

   - The system fetches the Jita Fuzzwork price (or the Director's manual override) for the exact item being built.
   - `Gamification Value = Item Value * Task Quantity`

1. **Builder Reward (Payouts)**
   The actual payout a builder receives is determined at the exact moment they **claim** the task from the Job Market.

   - The system checks the `builder_reward_percent` configured by the Directors in the Corporate Pricing Configuration.
   - It calculates the reward: `Builder Reward = Gamification Value * (Builder Reward %)`
   - For example: If a task produces items worth 100 million ISK (Gamification Value), and the Builder Reward is set to 5%, the builder will earn **5 million ISK**.
   - This 5 million ISK is registered to the builder's pending `BuilderPayoutBatch`. Once the builder completes the task, it becomes eligible for payout by the Directors.

### Summary

- **Buyer** pays: `Jita Value - Corporate Discount`
- **Builder** earns: `Jita Value * Builder Reward Percentage`
