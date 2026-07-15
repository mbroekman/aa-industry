# Calculating Material Requirements ("The EVE Truth")

This document outlines how the **Alliance Auth Industry** application calculates the Bill of Materials (BOM) for manufacturing jobs. The calculation logic in our engine is specifically designed to replicate the "EVE Truth"—the exact math used by the EVE Online game client in the Industry window.

The core calculation logic can be found in `industry_reforged/utils/bom_engine.py`.

## 1. Blueprint ME (`product_me`)

The **Material Efficiency (ME)** of a blueprint is resolved by the `get_blueprint_me()` function. It determines the ME value in the following order of precedence:

1. **Order Override:** Has the buyer manually specified a different ME for this item in their order?
1. **Corporation Setting:** Is there a fixed ME configured for this specific item in the admin panel via `CorpItemConfig`?
1. **Defaults:** If nothing is configured, the code checks if the item is Tech 1 or Tech 2. By default, T1 receives **10% ME**, and T2 receives **2% ME** (these defaults can also be changed in the corporation pricing settings).

## 2. Facility & Rig Bonuses (`facility_me_multiplier`)

This is the combined ME bonus provided by the Structure (Hull) and any installed Rigs.
In EVE, the mathematical impact of Rigs depends on the 'Security Space'. A T1 Rig provides its base bonus in Highsec, a x1.9 multiplier in Lowsec, and a x2.1 multiplier in Nullsec/Wormhole space.

In `calculate_facility_me_multiplier()`, the final multiplier is calculated as:
`Facility Multiplier = (1 - HullBonus) * (1 - (RigBonus * SecMultiplier))`

## 3. The Final Formula

Everything comes together in the `calculate_order_bom()` function (around line 211). In EVE Online, material reductions are calculated based on **1 run**, and only then multiplied by the total number of runs.

This is the exact mathematical sequence used in the code:

```python
run_cost = round(base_qty * ((100.0 - product_me) / 100.0) * facility_me_multiplier, 2)
required_qty = max(runs, math.ceil(run_cost * runs))
```

### How this works in practice:

1. Take the **Base Quantity** from the SDE (the standard material requirement without any bonuses).
1. Multiply this by the **Blueprint ME** (e.g., 10% ME = `* 0.90`).
1. Multiply this by the **Facility Multiplier**.
1. **EVE Specific:** Mathematically round this cost for 1 single run to **2 decimal places** (`round(..., 2)`).
1. Multiply this rounded cost by the **Total Runs** (`* runs`).
1. Always round this final amount **up** to a whole number (`math.ceil`), because you cannot insert 0.5 Tritanium into a factory line.
1. **EVE Specific:** Compare this final number against the total runs using `max(runs, ...)`. In EVE, the unbreakable rule is: *"1 run always costs at least 1 unit of a required material"*. Even if all bonuses reduce the math to 0.1, this check ensures that running a 10-run job will still cost 10 materials, not 1.

This logic guarantees that our calculations align almost perfectly with what the EVE client shows when installing a job. Minor differences (usually by exactly 1 unit) are often caused by the in-game blueprint actually being ME 9 while our app assumes a perfect ME 10, or due to slight fluctuations in the System Cost Index.

## 4. BPC Max Runs (Job Chunking)

A crucial nuance in EVE Online's math is that the final `math.ceil` is applied **per job**, not globally across all items ever built. If you build 1000 items using a BPO (1 job of 1000 runs), the math is calculated once: `math.ceil(run_cost * 1000)`.

However, if you build 1000 items using Blueprint Copies (BPCs) that have a maximum of 10 runs each, you are mathematically running 100 separate jobs of 10 runs each. EVE applies the rounding UP to each 10-run job individually, which usually results in a significantly higher raw material cost.

To simulate this "EVE Truth", our engine applies **Job Chunking**:

1. When a `max_runs` override is set (e.g. 10 runs), the engine calculates how many "full jobs" are needed (e.g. `1000 // 10 = 100 jobs`).
1. It calculates the material cost for exactly 1 full job: `cost_for_job = max(10, math.ceil(run_cost * 10))`.
1. It multiplies this cost by the number of full jobs: `cost_for_job * 100`.
1. If there are remaining runs (e.g. you needed 1005 items, leaving a remainder of 5 runs), it does the ceiling math for that one final smaller job of 5 runs, and adds it to the total.

This ensures that the BOM accurately predicts the exact material usage as if the user submitted these BPCs sequentially in the EVE client.
