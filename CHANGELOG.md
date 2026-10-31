# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)

## Unreleased

### Added

- **stock locations**: Material tables now show under Corp Stock how much lies in each structure, with the build facility first in green. A pick-up list per structure shows what to bring to the build facility before the jobs can run: only what the facility lacks, largest piles first. It appears on the order page (BOM tab), the industrialist Missing Materials tab and the shopping list, when all jobs are built in one structure. The director's deficit list shows the locations only (TASK-285).

### Changed

- **director dashboard**: The "Active Member Orders" tab is now "Orders" and opens on orders In Production; "All Statuses" is still in the filter. Next to the filter, clickable badges count new orders, quotes not yet accepted, orders in production and unpaid orders. A click filters the table without reloading the page, and so does Apply Filter (TASK-284).
- **director dashboard**: The Production Tasks tab gets the same quick-filter badges (Unclaimed, In Production, Completed) and opens on In Production; "All Statuses" is still in the filter. Its filter also works without a page reload (TASK-284).
- **orders**: The "Payment: Unpaid" filter only lists Ready and Delivered orders. Payment is not due yet while an order is still being built (TASK-284).
- **production tasks**: Hovering the Order badge of a task shows the order number (the main order for a split order).
- **job market**: The note on a released sub-job now reads "Released: you can't build the parent item yourself". The old text ("a skill most members lack") was wrong: the check uses the viewer's own skills.

### Docs

- **buyback**: The user manual now has a Buyback chapter for members (1.3) and for directors (3.8), plus the buyback webhook and background check; the README feature list covers all buyback options.

### Fix

- **orders**: Orders now reach In Production. No code ever set this status, so the filter was always empty. An Accepted order moves to In Production as soon as one of its jobs is claimed or completed or a buy item is marked bought, and back to Accepted when all claims are released. A migration moves existing orders with work in progress (TASK-284).
- **inventory**: Stock in a corporation-owned structure is filed under that structure again, not under its solar system (TASK-283). Since the change, orders never deducted stock at their facility and stock checks saw 0 there. The facility sync had the same problem. Stock moves back to the structure on the next inventory sync.
- **claimed jobs**: A claimed order job now shows "N spare in stock" when its facility holds more of the item than open orders have already made, so the builder can build fewer (TASK-283).
- **discord**: Discord messages no longer mix languages depending on who triggered them (TASK-281). Webhook posts use the language chosen per corporation (Director Configurations -> Global Pricing -> Discord Messages, migration 0092), falling back to the new `DISCORD_MESSAGE_LANGUAGE` setting and then `LANGUAGE_CODE`. Direct messages and Auth notifications use the recipient's own Alliance Auth language. All Discord texts (orders, quotes, blueprints, jobs, PI, wallets, inventory, AI tasks, buyback) are now translatable, with Dutch translations.
- **buyback**: Item icons on the contract page: in the item list, the sell-or-reprocess table and the material list.
- **buyback**: The calculator shows the calculation (base value, modifier, hauling, donation, what you receive) and the confirm button above the item list instead of below it, so long appraisals no longer need scrolling.
- **buyback**: The "one rule per item or market group" and "one watchlist entry per item group" checks are now real database constraints on MariaDB/MySQL too (migration 0089). Before, MariaDB skipped them with warning `models.W036`.
- **buyback**: The contract page now shows a separate "Create this contract in EVE" block while a contract is pending: who to make it out to, the exact ISK to ask, the title (tracking number) and the drop-off location, each with a copy button, plus the contract type and the deadline.
- **ui**: Inactive tabs and grey (secondary) buttons now have a visible background, border and readable text, also in the dark theme; disabled buttons are less washed out.

### Feat

- **buyback**: Build materials and four clear groups (TASK-280). Directors keep a list of items and market groups as **build material** (Buyback tab); the contract advice now sorts every item into **Sell**, **Reprocess**, **Build material** or **To be sorted** (no Jita price, sell and reprocess about equal, or slow to sell), each with its own colour, totals and icon. Reprocessed build materials are kept and valued at what buying them would cost; the material list is split into *Keep as build material* and *Sell after reprocessing*. The review queue shows the count per group (migration 0091).
- **buyback**: "Sell or reprocess?" advice per contract for the program's directors (TASK-279). Per item: the value sold straight to Jita buy orders or through a sell order (after broker fee and sales tax), and the same for its reprocessed materials (after reprocessing tax, whole batches only); advice Sell, Reprocess or Either way with the ISK difference. Materials the corporation is short of (low-stock targets) count as used in-house. Totals, gain over selling everything, a copyable material list, and an *Advice* column in the review queue. Settings per corporation in "Selling or reprocessing" on the Buyback tab (migration 0090).

- **buyback**: Statistics from the original buyback plugin (TASK-277, phase 5):
  - **Monthly leaderboard** (Statistics → Monthly leaderboard): sellers ranked by ISK paid out per month, with donations and contract count, and a program and month picker. Only programs you may use are shown.
  - **Performance page** per program for its directors (Statistics or the chart icon on the Buyback tab): 12 months of submitted contracts by status, ISK paid out and donations, with a chart, plus the top item groups and items of the last 3 months.
  - **CSV export** of every paid contract line (tracking number, dates, seller, item, group, quantity, price) for the program's directors.
  - **Wallet balance**: choose the corporation wallet division that funds a program; its balance (from the existing wallet sync) shows on the performance page.

- **buyback**: Pages for members (TASK-276, phase 4):
  - **Rules and prices** page per program (click the program name on the Buyback dashboard): how items are valued, what is accepted, item rules, fixed prices, drop-off, recipient and deadline. The program's own directors also see its watchlist there.
  - **FAQ** with a built-in "How it works" and questions each corporation's directors manage on the Buyback tab (no Django admin needed). Members see the FAQ of every corporation whose program they may use.
  - **Check contracts now** button in the review queue, instead of waiting up to 15 minutes for the next poll.

- **buyback**: Contract handling and notifications from the original buyback plugin (TASK-275, phase 3):
  - Sellers can add a note for the buyer; it shows on the contract page, in the review queue and in the Discord post.
  - A contract asking more than the quote is flagged; asking less is only noted, since the seller only shortchanges themselves.
  - **Suspicious contracts**: an in-game contract to the program's recipient that uses its tracking prefix, but a tracking number that was never issued, is recorded once, posted to Discord and listed in the review queue until a director dismisses it.
  - Per program: post every new contract to the buyback webhook (flagged ones always), optionally with the item list, and DM a manager character for each new contract.
  - Sellers now also get an Alliance Auth notification next to the Discord DM, and can turn both off with the bell on the Buyback dashboard.
  - The contract page compares the appraisal with the items of the in-game contract and highlights missing items and quantity differences.
  - Watchlist entries for a whole item group now also send matching contracts to review.

- **buyback**: Item rules and pricing options from the original buyback plugin (TASK-274, phase 2):
  - **Item rules**: raise, lower or block the price of one item or a whole market group (a group rule covers the groups below it; the most specific rule wins). An allowlist mode accepts only items that have a rule.
  - **Fixed prices** per item, without any modifier, rule or density tax.
  - **Watchlist** entries can now cover a whole item group.
  - **Ore, ice and moon ore**: raw, compressed and refined value can each be switched on or off; the highest enabled value is paid.
  - **T1 scrap value**: ships, modules, charges, drones and subsystems up to meta level 4 can also be valued as scrap minerals, at their own yield.
  - **NPC prices** for Sleeper Components, Triglavian Survey Databases, Overseer's Personal Effects and SCC Encrypted Bonds (each its own switch; the original's bonds switch read the wrong setting).
  - **Hauling cost** per m³, optionally on compressed ore volume, shown separately in the calculator and on the contract.
  - Assembled items are refused unless allowed, blueprints are always refused, and a program can refuse the whole appraisal when any item isn't accepted.
  - The calculator explains each price (which valuation won, which rule applied, density tax).
  - The EVE data these options need (reprocessing yields, meta levels, market groups) is fetched per item on first use; directors load all market groups once with a button.
  - **Behaviour change**: items other than ore are no longer compared against their reprocessed value by default; that's now the opt-in T1 scrap option. Ore keeps using the higher of market and refined value.

- **buyback**: Access and visibility options from the original buyback plugin (TASK-273, phase 1):
  - Programs can be limited to Alliance Auth groups and/or states. This is enforced everywhere: dashboard, calculator (including a direct POST), statistics and contract pages. Directors always see their own corporation's programs, and directors of another corporation can no longer open a contract's page.
  - A program can be made public: its calculator then works without logging in, and the visitor gets a private status page through the tracking number. Requires `APPS_WITH_PUBLIC_VIEWS = ["industry_reforged"]` in `local.py`; without it a login is still required.
  - A program can have several drop-off locations (structures and other locations); any of them passes the location check. Existing programs keep their current drop-off.
  - Contracts can go to a specific character instead of the corporation; that character's contracts are then polled (new scope `esi-contracts.read_character_contracts.v1` via Add Personal Token).
  - Each program sets its own tracking number prefix (default `BB`, so existing tracking numbers keep working).

- **claims**: Claimed-job ETA tracking, overview and overdue alerting (TASK-262):
  - `utils/eta_service.py`: estimates when a claimed job should be done, preferring the real ESI-reported `end_date` of the linked EVE industry job once one exists, falling back to `assigned_at + estimated_duration_seconds`, and treating an unknown ETA (no claim timestamp, or a build duration that was never successfully computed) as "unknown" rather than guessing.
  - New `JobTrackingConfig` per-corp setting (`completion_buffer_hours`, frontend-editable from a new "Job Alerts" card on Director Configuration): the grace period after the estimated completion before a job is flagged overdue, and also the interval between repeat reminders while it stays overdue.
  - The Director Dashboard's existing "Production Tasks" table gains Claimed At and Estimated Done columns (ESI-confirmed vs. estimated badge, red highlight once overdue) instead of a duplicate new tab - filtering it to `IN_PRODUCTION` already gives the "who's got what and when" overview.
  - New periodic Celery task `check_overdue_production_tasks` (every 30 min): notifies the claimant individually (AA in-app notification + Discord DM) on first overdue and again each time the buffer interval re-elapses while still overdue, plus one batched `directors_webhook` embed per corp per run.
  - `last_overdue_notified_at` resets whenever a task is unclaimed, so a reclaimed job starts its overdue clock fresh.
- **claims**: Surface buildable BOM sub-components for skill-gated jobs (TASK-261):
  - When a parent task is skill-gated and unbuildable for the viewing user, its already-persisted BOM child `ProductionTask` rows (created recursively at order acceptance) now become independently visible/claimable in the Job Market, even though the parent's static `is_claimable` admin flag stays unchanged - purely additive, per-viewer visibility.
  - Cascades to arbitrary depth automatically: if a released child is itself skill-gated for this viewer, its own children are released in turn, with no new admin configuration per BOM level.
  - A skilled corpmate still sees and can claim the parent directly as before; this never changes what's claimable, only what's additionally visible for members who can't do the parent themselves.
  - Released rows show a small "Released: parent needs a skill most members lack" note.
  - `skill_service.py`: new `check_eligibility_with_levels` so the dashboard fetches each viewer's skill levels once per page load instead of once per task.
- **claims**: Implemented skill-gated job eligibility in the Job Market (TASK-260):
  - Added `skill_service.py`: checks real EVE blueprint skill requirements (django-eveuniverse's `EveIndustryActivitySkill`, sourced from the EVE SDE, already populated) against character skill levels, independent of slot availability - capital/supercapital/T3/advanced-reaction blueprints are hard-gated behind specific skills that pure slot counts don't capture.
  - `slot_service.py` refactored to source skill levels from the new shared `get_character_skill_levels` instead of its own embedded ESI fetch - one raw-ESI call per character now serves both slot counting and skill eligibility.
  - Job Market disables (not hides) any unclaimed task no character the user owns could ever build, with a tooltip naming the missing skill(s); `claim_task` adds a server-side hard-stop checking the specific claiming character (main character) even if a qualifying alt exists on the account.
  - Fix: both the skill-eligibility check and the slot count itself now only consider characters in the same corp as the user's main character (`get_user_industry_characters`) - an alt sitting in an unrelated corp has no access to this corp's hangars/facilities and was previously inflating both numbers.
  - Fix: the Claim modal's "Your Live Detected Available Slots" badge showed the generic account-wide slot total for every item, which still looked like "too many slots" for skill-gated items most of the account can't actually build. `get_user_available_slots` now takes an optional `item_type_id` to restrict the count to corp + skill-eligible characters only; `claim_task_preview` returns this scoped number and the modal updates the badge, the "All Free" preset, and the slots input's max once the preview response lands.
- **claims**: Implemented Interactive Slot-Based Partial Claiming and Task Splitting (TASK-255):
  - Created `slot_service.py` to calculate available industry slots live from ESI character skills (Mass Production, Advanced Mass Production, Mass Reactions, Advanced Mass Reactions, Laboratory Operation, Advanced Laboratory Operation) and `CharacterIndustryJob` across all user-owned characters without Corptools dependency, with 24-hour Django caching.
  - Added `allocated_slots` field to `ProductionTask` model (migration `0080`) and `portion_size` property.
  - Upgraded `claim_task` view with support for partial quantity claiming and automatic task splitting:
    - Claimed portion is assigned to the builder in `IN_PRODUCTION` with allocated slots recorded and its builder reward / estimated duration dynamically calculated.
    - Remaining quantity stays on the Job Market as `UNCLAIMED` with its builder reward and duration accurately recalculated.
  - Added `claim_task_preview` AJAX endpoint for real-time live preview of claim metrics (runs per slot, wall-clock duration, claimed reward, and remaining reward).
  - Enhanced Job Market UI in `industrialist_dashboard.html`:
    - Displayed live available manufacturing and reaction slot indicators in the Job Market card header.
    - Added `#claimTaskModal` with interactive slots-to-dedicate and quantity-to-claim inputs, quick preset buttons (24h Batch, 48h Batch, Claim All, 1 Run), and dynamic live batch metrics panel with wall-clock duration and reward previews.
    - Displayed allocated slots badge on `#active-production-table`.
  - Added unit test suite `test_partial_claiming.py` covering live slot determination, active job subtractions, caching, full claims, partial claims with task splitting, boundary clamping, and preview API.
- **tasks**: Implemented Production Task Priority Controls and Multiplier Visualization (TASK-254):
  - Added `URGENT` to `ProductionTask.PRIORITY_CHOICES` (migration `0079`) for rush jobs.
  - Added single (`set_task_priority`) and bulk (`bulk_set_task_priority`) priority management endpoints with automatic `builder_reward` and `estimated_duration_seconds` recalculation using configured corporate multipliers (`builder_urgent_multiplier`, `builder_high_multiplier`, `builder_low_multiplier`).
  - Added priority selector when directors spawn manual restock jobs in `director_inventory.html`.
  - Added Priority column to Job Market (`#jobmarket-table`) and Active Production (`#active-production-table`) in `industrialist_dashboard.html`:
    - Directors can change task priorities inline via dropdown or in bulk via "Set Priority" toolbar dropdown.
    - Added rich priority badges with icons for Urgent (danger/bolt), High (warning/angle-double-up), Normal (primary), and Low (secondary/angle-down).
    - Unclaimed tasks on Job Market are ordered with Urgent and High priorities appearing first.
  - Added unit test suite `test_task_priority.py` covering single/bulk priority updates, reward recalculations, permission gates, restock spawning, and priority sorting.
- **rewards**: Restored `builder_reward_percent` in Builder Pricing (TASK-253):
  - Re-added `builder_reward_percent` field to `CorpPricingConfig` (migration `0078`), restoring the optional value incentive component in builder compensation configurations.
  - Restored "Value %" column and inputs in `director_config.html` and `CorpPricingConfigForm`.
  - Restored `pricing_engine.calculate_task_builder_reward` to include the output value incentive in the hybrid formula: Base Fee + (Slot Duration Hours * Hourly Rate) + (Output Market Value * Value %).
- **rewards**: Removed deprecated `builder_reward_percent` from Builder Pricing model, forms, templates, and calculation (TASK-252):
  - Removed `builder_reward_percent` field from `CorpPricingConfig` (migration `0077`). Builder compensation is now cleanly focused on slot-duration hours and flat base fee, bounded by configurable floor and cap values.
  - Removed "Value %" column and inputs from `director_config.html` and `CorpPricingConfigForm`.
  - Updated `pricing_engine.calculate_task_builder_reward` to omit value incentive, computing reward as Base Fee + (Slot Duration Hours * Hourly Rate), bounded by floor and cap and adjusted by priority multipliers.
- **config**: Separated Builder Pricing into a dedicated tab in Director Configurations (TASK-251):
  - Created a dedicated "Builder Pricing" tab in `director_config.html` displaying all aspects of the Hybrid Builder Reward Model: Base Fee, Hourly Rate, Value Incentive %, Safety Bounds (Floor & Cap), and Priority Multipliers.
  - Streamlined the "Global Pricing" tab to focus strictly on customer pricing defaults (discount % and ME defaults), material valuation methods and margin floors, and system taxes.
  - Updated `director_config_pricing_edit` view to redirect to `#builder-pricing` upon saving and set back navigation to `#builder-pricing`.
- **config**: Added dynamic live formatted ISK preview in director configuration forms and improved ISK overview tables (TASK-250):
  - Added live ISK preview badges (`isk-live-preview`) beneath numeric inputs in `director_config_form.html`, formatting raw numbers with standard comma separators and EVE shorthand (e.g. `75,000,000 ISK (75.00M ISK)`) in real-time as users type.
  - Added `.isk-input` CSS class to `CorpPricingConfigForm` (`builder_base_fee`, `builder_hourly_rate`, `builder_min_reward`, `builder_max_reward`), `CorpItemConfigForm` (`manual_price`), and `BuybackProgramForm` (`price_density_threshold`).
  - Updated `director_config.html` Corporate Pricing Configurations table to display the configured `builder_min_reward` (Floor) alongside Base fee and Cap.
  - Formatted `price_density_threshold` with `|eve_isk` in the Buyback Programs table and replaced low-contrast `btn-outline-secondary` buttons with `btn-outline-primary`.
- **rewards**: Implemented Hybrid Builder Reward Model 2 with slot duration, safety bounds, and priority multipliers (TASK-249):
  - Replaced legacy flat percentage reward model with a balanced hybrid formula: Base Fee + (Slot Duration Hours * Hourly Rate) + (Output Market Value * Value Incentive %).
  - Bounded rewards with configurable `builder_min_reward` (floor, default 2.5M ISK) and `builder_max_reward` (ceiling, default 75M ISK), preventing trivial payouts on consumables and multi-billion wallet drains on Titans/Supercapitals.
  - Added priority scaling multipliers: `URGENT` (1.5x / +50%), `HIGH` (1.25x / +25%), `NORMAL` (1.0x), and `LOW` (0.8x / -20%).
  - Added `get_item_production_details` in `pricing_engine.py` with Django caching, retrieving deterministic blueprint base durations from `django-eveuniverse` `EveIndustryActivityDuration` and factoring in typical Engineering Complex TE rig/skill efficiency.
  - Added `estimated_duration_seconds` and `estimated_duration_hours` to `ProductionTask` model.
  - Added `format_duration` template filter in `industry_tags.py` to format seconds into EVE industry format (e.g. `104d 4h`, `3h 20m`, `10m`).
  - Updated Director pricing configuration form and views to configure base fee, hourly rate, value %, floor, cap, and multipliers.
  - Updated Industrialist job market and in-progress task lists to display estimated duration clock badges alongside rewards.
  - Added comprehensive test suite `test_hybrid_builder_rewards.py` with 100% passing tests.
- **pricing**: Implemented structure job installation costs and corp blueprint ownership rules for orders (TASK-248):
  - Added `fetch_system_cost_indices(solar_system_id)` with 1-hour Django cache TTL, fetching live ESI system cost indices across manufacturing, reactions, copying, and invention.
  - Added `calculate_structure_job_costs(parsed_items_or_trees, target_facility, corporation)` calculating official EVE Online industry job installation fees: Estimated Item Value (EIV) $\times$ System Cost Index (SCI) $\times (1 + \text{Facility/Corp Tax Rate})$.
  - Implemented the corporation blueprint ownership rule across `calculate_bom_cost`, `view_quote`, and `htmx_update_quote_facility`: any blueprint owned by the corporation in `CorpBlueprint` (as BPO or BPC) costs 0 ISK; only unowned/missing blueprints represent an acquisition cost.
  - Included structure job installation fees in `order.true_cost` and `view_quote` estimated build cost.
  - Added explicit Structure Installation Fees breakdown row and displayed Gross Profit Margin % on revenue (`profit_margin_percent`) alongside ISK profit margin in `view_quote.html` (Option A).
  - Added "Corp Owned" vs "Unowned" badges and 0.00 ISK formatting for blueprints in `quote_bom_panes.html`.

### Feat

- **buyback**: Added a Buyback Program sub-feature (TASK-243): members paste an in-game inventory list to get an instant appraisal (market price vs. reprocessing value, whichever is higher, with a configurable price modifier and a bulky-item price-density tax) and a tracking number, then create an in-game item-exchange contract; a background task polls ESI corporation contracts every 15 minutes, matches by tracking number, and flags item/price/structure/receiver mismatches or title tampering for director review before payout (recorded as a `LedgerTransaction`). Directors configure drop-off locations (`IndustryFacility`/`KnownLocation`), the price modifier, and a per-item watchlist (block or flag) entirely from a new "Buyback" tab on the Director Configurations page; a separate review queue lists flagged/matched contracts awaiting a pay/reject decision. Member access reuses the existing `basic_access` permission, manager access reuses `corp_access` - no new permissions were added. Ported the concept (not the code) of a third-party `allianceauth-buyback-program` plugin per the research/integration proposal in `backlog/docs/doc-18`; reverse buyback (corp selling hangar stock to members) and public/anonymous program access are explicitly deferred to a future task.
- **buyback**: Members can now donate part of their buyback payout back to the corp, entered as either a fixed ISK amount or a percentage of the appraisal, on the calculator before confirming. The donated amount is deducted up front (`BuybackContract.quoted_price` is already net of it - what the member should put on the in-game contract and what gets paid out), with the gross appraisal and donation shown separately on the contract detail page. Donations clamp to the appraisal total (never negative, never more than 100%). Tracked per program on the Statistics page (total donated + a Top Donors leaderboard).
- **buyback**: Fixed two visibility gaps - the contract detail page now shows who submitted the contract ("Submitted By"), and the ISK impact of the program's price modifier/bulk-item tax is now shown as an actual amount (not just the program's `-5%`-style badge). `BuybackContractItem.base_unit_price` persists each item's pre-modifier appraised value alongside the final `unit_price`, so the breakdown (base market value -> modifier/tax adjustment -> appraisal subtotal) stays accurate and auditable later, rather than being recomputed against (possibly since-changed) live market prices. Shown on both the calculator's preview and the contract detail page via new `BuybackContract.base_appraisal_total`/`modifier_impact` properties.
- **buyback**: Added a per-program Statistics page (`/industry/buyback/stats/`), going beyond the source project's plain stats/leaderboards with operational-health insights: flag/rejection/expiry rates and average submission-to-resolution turnaround, alongside ISK/item leaderboards (top sellers, top items) and a daily activity trend chart (contracts submitted vs. ISK paid out, 7/30/90-day windows) rendered with Alliance Auth's bundled Chart.js. Linked from both the member Buyback dashboard and the director's Buyback config tab.

### Fix

- **buyback**: Reprocessing yields are now divided by the item's portion size. EVE lists ore yields per 100 units, so refined ore would have been valued about 100x too high once reprocessing data was present.
- **buyback**: Closed gaps in the Buyback Program (TASK-272, phase 0 of bringing it level with the original plugin):
  - Directors can now only see, edit, delete and resolve programs, watchlist entries and contracts of their own corporation. Before, the review queue showed every corporation's contracts and any program could be edited or deleted by id. Deleting now requires a POST, and a program that already has contracts can't be deleted (it previously crashed); deactivate it instead.
  - The in-game contract status is now followed: when the receiver accepts the contract in EVE it's marked Paid with one payout ledger entry (shared with the director's Pay button, so it's never recorded twice), rejected in EVE becomes Rejected, an outstanding contract past its in-game expiry becomes Expired, and a contract the seller deletes goes back to Pending so a corrected contract with the same tracking number can still match. Members get a DM when they're paid.
  - A contract is now matched once, when first seen. Before, it was re-matched every 15 minutes and a flagged contract re-posted its Discord alert on every poll.
  - Watchlist items in flag mode now actually send the contract to director review (they previously only showed a badge in the calculator).
  - The program's accepted categories are now enforced; items outside them are shown as "Not accepted" with the reason.
  - Reprocessed materials are valued at the program's price type (buy/sell/split); they were always valued at sell.
  - Removed the unused "Accepted" contract status; contract items are marked as verified when they match the in-game contract.
- **orders**: The order page's Missing Blueprints list no longer flags a blueprint as missing when the product is already built or in production in EVE (TASK-270). Previously only tasks marked complete counted as built. A member who had already run the job in EVE, but hadn't marked the task complete yet, used up the BPC runs, so corp stock dropped and the page reported a shortage. Runs of EVE jobs linked to the order's tasks (active, paused, ready, delivered) now count as built; cancelled or reverted jobs don't, because EVE returns the blueprint.
- **claims**: Skill eligibility is now enforced on every claim path (TASK-269). Bulk claim previously skipped the per-task skill hard-stop that a single claim applies, so it could claim jobs the member couldn't build. Both single and bulk claim now also check every unclaimed BOM sub-task that would be claimed along with the job: if the main character can't build any of them, the job isn't claimed (bulk claim skips it with a warning naming the item and missing skills). Members still see every job. The claim-preview modal reports the same verdict. A failed skill lookup (no token or ESI error) blocks skill-gated claims; the misleading "fail open" docstring now describes this.
- **buyback**: The "Add Corporate Token" flow now requests `esi-contracts.read_corporation_contracts.v1`. Without it, `buyback_poll_contracts` never found a usable token and silently matched nothing. Existing corporate tokens must be re-added once. A new test fails if any code path filters tokens on a scope that no token view requests. The README scope list now also documents `read_skills`, `read_divisions`, `read_blueprints` and `structure_markets`.
- **rewards**: Implemented pro-rata reward splitting for partial claims (TASK-259):
  - Updated `claim_task_preview` and `claim_task` endpoints in `views/industrialist.py` to distribute `task.builder_reward` pro-rata based on claimed quantity ratio (`claim_qty / task.quantity`).
  - Resolved issue where partial claims recalculated rewards as independent tasks and consumed the full corporate maximum reward cap (e.g. 75M ISK) on both the claimed batch and the remainder.
  - Conserved total job reward across all partial claims so that `reward_claimed + reward_remaining == original_task.builder_reward`.
  - Added unit regression test verifying pro-rata conservation of capped rewards across partial claims.
- **ui**: Fixed `#claimTaskModal` hidden behind modal backdrop on Job Market (TASK-258):
  - Added missing closing tags (`</div></div></div>`) for `#shoppingListLoadingModal` in `industrialist_dashboard.html`, which had previously caused `#claimTaskModal` to be nested inside the hidden shopping list modal container (`display: none`).
  - Restored proper DOM isolation so the Claim modal appears centered and interactable above the Bootstrap backdrop when industrialists click "Claim".
- **claims**: Fixed 500 Internal Server Error in `claim_task_preview` and `claim_task` endpoints (TASK-257):
  - Fixed `AttributeError: 'MemberOrder' object has no attribute 'corporation'` by accessing corporation through `task.created_from_order.character.corporation` instead of `task.created_from_order.corporation`.
  - Added unit regression test `test_claim_task_preview_with_created_from_order` validating preview calculations when task is linked to a `MemberOrder`.
- **ui**: Fixed DataTables warning TN/18 ("Incorrect column count") on `#active-production-table` in the Industrialist Dashboard (TASK-256):
  - Restored missing Origin `<td>` column (`dt_task_origin.html`) in `#active-production-table` tbody, bringing row column count back to 8 to exactly match the 8 `<th>` columns in `<thead>` and DataTables `columnDefs` targets `[0, 7]`.
  - Safely accessed `task.portion_size` property in `industrialist_dashboard` to eliminate potential `TypeError` on nullable `EveType.portion_size`.
  - Added regression test `test_active_production_table_column_count_matches_thead` verifying matching column counts.
- **pricing**: Fixed severe cost underestimation and distorted margin calculations on orders (TASK-247):
  - In `pricing_engine.py`, added filtering of extreme lowball/troll buy orders (< 25% of highest bid) in `calculate_percentile_price` and sanity validation comparing buy orders to sell market depth in `fetch_single_market_price`, falling back to EveMarketPrice or Jita Sell when buy order books are illiquid or manipulated (resolving 0.01 ISK evaluations on Zydrine, Fullerite, P4 PI commodities, and direct-buy fittings).
  - Added safety fallback in `calculate_bom_cost` ensuring any raw material returning <= 0.05 ISK falls back to current market sell pricing.
  - In `quotes.py`, excluded blueprint purchase/seed costs (`bom_blueprints_list`) from `total_bom_price` and `estimated_build_cost` in `view_quote` and `htmx_update_quote_facility` so BPO ownership doesn't inflate build costs by trillions of ISK.
  - In `quotes.py`, dynamically recalculate and persist `order.true_cost` upon providing or reviewing quotes (`view_quote` and `provide_quote`).
  - In `datatables.py`, aligned the director orders "Margin" column to standard gross profit margin on revenue `((total_price - true_cost) / total_price * 100)` and added markup on cost as a tooltip (`data-bs-toggle="tooltip"`).
- **buyback**: Fixed 3 correctness/UX gaps found by comparing against the third-party source project (TASK-246): reprocessed-value appraisals were hardcoded at 100% refining efficiency with no director control (no real reprocessing setup hits 100%, so items valued via reprocessing were systematically overpaid) - now a per-program `refining_rate` (default 90%) scales it; the appraisal was always based on Jita sell price with no way to use buy or a buy/sell split instead - now a per-program `price_type` (Buy/Sell/Split) controls it; and the contract detail page never told the member which corporation to address the in-game contract to, even though the ESI matching logic already expects a specific receiver - the "create a contract" instructions now show both the drop-off location and the recipient corporation.
- **buyback**: Fixed `BuybackContract.modifier_impact` having its sign backwards - a price-reducing modifier (e.g. a -10% bulk tax) was computed as a *positive* value and rendered in green with a `+`, i.e. shown as a bonus to the member instead of the discount it actually was. Same bug existed in the calculator view's own `modifier_impact` computation. Both now correctly compute `gross_appraisal - base_appraisal_total`, so a discount is negative/red and a bonus is positive/green, matching the template's existing color/sign logic. Caught by two model-property tests that asserted the correct sign and failed against the old, inverted formula.
- **security**: Bumped `fastapi` in `ai-forecasting/pyproject.toml` from `^0.110.0` to `^0.135.0`, resolving 7 Dependabot-flagged Starlette CVEs (transitively pulled in via FastAPI's own `starlette` requirement, which was unpinned in this sub-project). No `poetry.lock` exists for this service, so the version bump is the full fix; verified by installing the full dependency set into an isolated venv and confirming `ai_forecasting.main` still imports cleanly.
- **pi**: Translated hardcoded Dutch text in PI extractor-expired and storage-full notification messages (and the planet-name fallback label) to English, consistent with the Alliance Auth ecosystem's English-only standard.

### Feat

- **orders**: Added ability to mark buy products as bought on order details (`view_quote`), complete with purchaser tracking, instant AJAX status toggle, and progress bar integration.
- **orders**: Display actual production task status (`Completed`, `In Production`, `Unclaimed`, `To Build`) with builder tooltip for manufactured items in order details and child orders instead of static label.

## v0.15.7 (2026-10-07)

### Feat

- **ui**: Added 'Location' column to the Corp Blueprint Library table, resolving structure, station, container, and hangar division paths with full server-side search support.
- **ui**: Support for unclaimable parent tasks in the industrialist dashboard, showing sub-jobs visually nested and delaying claimability until sub-jobs are COMPLETED.

### Fix

- **ui**: Fixed 'Missing Blueprints' tab on order view marking consumed blueprints from completed tasks as missing; consumed blueprints now correctly display as 'Used' with 0 shortage and are omitted from the red shortage counter badge.
- **ui**: Fixed 'My Corporate Jobs' and 'Corporate Jobs' tables hiding ready-to-deliver jobs under the default 'Active' filter, keeping them visible until actually delivered in EVE Online.
- **ui**: Fixed 'To Build' column in Build Steps on the Industrialist Dashboard not deducting 'In Progress' or completed amounts, ensuring 'To Build' accurately reflects remaining items to build.
- **logic**: Fixed an issue where the initial `is_claimable` state lookup failed during quote acceptance due to using the EVE Corporation ID instead of the internal Django Database ID.

## v0.15.6 (2026-10-06)

### Fix

- **ui**: Fixed blueprint images displaying incorrectly (or falling back to a generic icon) in the item rules configuration and quote view tables by adding a fallback to the `/bp` image server endpoint.

## v0.15.5 (2026-10-06)

### Fix

- **logic**: Fixed the check for BPOs in `quotes.py` to also check `runs=-1`, correctly identifying stacked or sync-adjusted Reaction Formulas as owned.

## v0.15.4 (2026-10-06)

### Fix

- **logic**: Fixed hardcoded `activity_id=1` in `quotes.py` and `models/orders.py` which caused Reaction Formulas (`activity_id=11`) to be ignored in blueprint configuration and override logic.

## v0.15.3 (2026-10-06)

### Fix

- **ui**: restored BPO tracking in missing list but flagged as owned so the UI badge shows correctly instead of disappearing

## v0.15.2 (2026-10-06)

### Fix

- **logic**: correctly identify reaction formulas as available blueprints and exclude owned BPOs from shortage list

## v0.15.1 (2026-10-06)

### Fix

- **logic**: Fixed a bug where missing blueprints would evaluate inventory quantity instead of runs, causing false shortage reports for blueprints stored as BPCs.
- **ui**: Replaced the standard CCP Image Server icon endpoint with the blueprint `/bp` endpoint to fix broken missing blueprint icons.
- **ui**: The "Missing Blueprints" table is now a DataTable for easy sorting, and clearly displays both the required amount and actual shortage of runs.
- **ui**: Correctly detect if a missing blueprint is available as a BPO and display a warning badge instead of a missing error.

## v0.15.0 (2026-10-06)

### Feature

- **ui**: Overhauled the 'Required Raw Materials' BOM view. It now uses collapsible DataTables for improved readability and searchability. Materials are automatically mapped into logical EVE categories (Minerals, Moon Goo, Reaction Materials, Planetary Commodities, etc.) instead of obscure standard SDE group names.
- **ui**: The BOM view acts as an accordion, meaning groups are collapsed by default for maximum overview. A real-time red 'Shortage' badge is appended to the group header if any material inside lacks sufficient corporate stock.
- **logic**: Top-level items on an order that are set to "BUY" (i.e. products that are simply bought and delivered rather than built) are now smartly excluded from the Required Raw Materials list.

## v0.14.4 (2026-10-02)

### Fix

- **esi**: resolve infinite loops and memory leaks in pagination caused by endpoints ignoring page parameters, by tracking previously seen IDs.
- **chore**: unified .gitignore files to exclude build, test, and temporary files across repositories.

## v0.14.3 (2026-10-01)

### Fix

- **ui**: update misleading empty inventory text to reference facilities instead of hangars


## v0.14.2 (2026-10-01)

### Fix

- **esi**: bypass ETag cache on paginated ESI requests to prevent early loop abortion and ensure full data synchronization (inventory, facilities, jobs)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Fix

- **bom**: ensure only published blueprints are used for reactions (preventing massive cost inflation for T2 components) (TASK-219).
- **bom**: ensure items configured as BUY are not exploded into raw materials even when requested as the root quote item (TASK-218).

## v0.14.1 (2026-10-01)

### Fix

- **i18n**: Fix invalid control sequences and duplicate message definitions in Dutch translation files causing GitHub Actions compilation failures (TASK-200).

## v0.14.0 (2026-10-01)

### Feat

- **industry**: Add `is_default_reaction` facility configuration to allow setting a default structure for reactions (Activity 11). This ensures reaction calculations accurately include installed structure rigs and bonuses (TASK-3).
- **orders**: Introduce a new 'Profit & Loss' default view for Quotes (REQUESTED and QUOTED status) to improve visibility of material cost, estimated build cost, and profit margins (TASK-4).
- **orders**: Separate manufactured items and "Buy Products" (items without a manufacturing activity) in the Itemized Invoice view for clearer quote details (TASK-191).
- **orders**: Add ability to disable corporation discounts on a per-order basis when providing a quote, dynamically updating the Profit & Loss margins (TASK-192).
- **orders**: Allow specifying upfront payments in PLEX in addition to ISK, including dynamic display of the current Jita PLEX value (TASK-193).
- **ui**: Replace static loading spinners with animated progress bars when opening orders, recalculating quotes, or submitting quotes to improve user experience (TASK-194).
- **orders**: Display missing blueprints required for an order in a dedicated quote tab (TASK-196).
- **orders**: Account for ISK and PLEX upfront payments in the remaining balance display on order details (TASK-198).
- **orders**: Show current PLEX rate directly below upfront PLEX payment requirements (TASK-199).

### Fix

- **bom**: Fix `ValueError: too many values to unpack (expected 2)` during order quote generation due to incorrect tuple unpacking in `bom_engine.py` (TASK-190).
- **ai**: Ensure `check_availability` accounts for active and ready unlinked `CorporationIndustryJob` instances to prevent AI Market Manager from over-ordering when jobs are running natively (TASK-2).
- **inventory**: Fix missing pagination when fetching corporate assets via ESI, ensuring complete stock synchronization for corporations with >1000 assets (TASK-197).


## v0.13.1 (2026-09-27)

### Fix

- **ai**: Prevent application failure by handling cases where the AI Manager model is unavailable (TASK-177).
- **orders**: Show the most expensive line item in order lists to make order identification easier (TASK-178).
- **blueprints**: Fix Blueprint Library visibility by adding a State filter to correctly distinguish between BPOs and BPCs (TASK-179).
- **pricing**: Corrected display formatting by removing percentage signs from absolute ME/TE values (TASK-180).
- **bom**: Fix material calculation fallback behavior to correctly apply configured Material Efficiency (ME) values for T1 blueprints (TASK-181).

## v0.13.0 (2026-09-20)

### Feat

- **ai**: implemented the standalone AI Demand Forecasting Service (LightGBM) with integrated REST API
- **ai**: implemented data ingestion for ESI Market transactions, OpTimer Pings, and Doctrines to predict future alliance demand
- **ai**: integrated ai-forecasting predictions into the Opportunity Scanner and Basket Engine to automatically recommend production based on upcoming doctrines and market trends
- **director**: allow CP users to delete any production task (including basket-generated jobs) individually and in bulk
- **industrialist**: add delete action and bulk delete for CP users on available and active jobs
- **i18n**: fully update and compile Dutch translations (`nl`) covering all features through v0.12.x (AI Market Manager, Basket management, Opportunity Scanners, Blueprints, Ledgers, etc.)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **facilities**: resolve Upwell structure locations from corporate assets container hierarchies into `IndustryFacility` and `KnownLocation`, ensuring alliance structures (such as C-N Keepstar) appear in facilities and hub dropdowns after a fresh install

- **inventory**: prevent premature exit in `task_sync_corp_inventory` when no facility has `sync_inventory=True`, ensuring known locations are always discovered

## v0.12.2 (2026-09-08)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- prevent memory exhaustion from historical jobs in dashboard

## v0.12.1 (2026-09-08)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **views**: prevent session timeout during auto-refresh

## v0.12.0 (2026-09-07)

### Feat

- **ai-manager**: factor in specific corporation stock

## v0.11.0 (2026-09-07)

### Feat

- **ai**: implement Discord Webhook notifications for newly generated AI tasks
- **ai**: configure AI Manager to use `final_price` adjusting for overrides when calculating profitability margins

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **ai**: correct state of generated ProductionTasks to `UNCLAIMED` allowing jobs to properly show up in task lists

- **pricing**: exclude Blueprint/Reaction Formula costs (Activity 5) from `calculate_bom_cost()` recursive materials logic, preventing massive artificial inflation of true material cost floors for Quote calculations

## v0.10.1 (2026-09-04)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **ui**: expose CorporationPricingConfig configuration form in director dashboard so it is accessible to users

## v0.10.0 (2026-09-04)

### Feat

- **pricing**: implement true material cost (BOM-based) pricing and minimum margin floor (TASK-125)

### Docs

- **docs**: update documentation for true material cost and alternative pricing methodology (doc-11, doc-12)

### Chore

- **chore**: finalize implementation and prepare for v0.10.0 release

## v0.9.0 (2026-09-04)

### Feat

- **pricing**: implement direct CCP ESI market pricing (Option 1) and deprecate Fuzzwork

## v0.8.5 (2026-09-04)

### Feat

- **ui**: add configurable page auto-refresh (5m, 10m, 15m, 25m, 30m) with countdown timer and active tab persistence across jobs and PI dashboards (TASK-120)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **perf**: eliminate N+1 database queries in PI rates and depletion calculations with in-memory schematics cache, preventing DB connection exhaustion (TASK-121)

### Docs

- **docs**: translate backlog documentation to English (TASK-122)

### Chore

- **chore**: relocate agent skills to global system level (`~/.gemini/config/skills/`)

## v0.8.4 (2026-09-03)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **industry**: automatically bootstrap PI schematics from SDE during PI sync or dashboard view if table is empty (TASK-119)

## v0.8.3 (2026-09-03)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **industry**: resolve PI factory depletion baseline calculation using pin cycle start timestamp (TASK-118)

- **industry**: prevent extraction planets with active extractors from incorrectly displaying "Out of Resources" (TASK-118)

- **industry**: add dynamic resource consumption deduction on storage and launchpad pins (TASK-117)

- **industry**: add accurate factory running, depleted, and idle status badges on dashboard and modals (TASK-117)

- **industry**: remove flawed cycle start check causing running factory planets to show as stopped (TASK-116)

## v0.8.1 (2026-09-01)

### Feat

- **ui**: redesign PI factory and extractor layout on personal dashboard (TASK-113)
- **ui**: redesign PI extraction deficit display with Supply & Demand graph, configurable threshold, and planet overview indicators (TASK-114)
- **industry**: add factory depletion timers and end product visibility on launchpads (TASK-112)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **industry**: resolve simulated PI production distribution loss (prevent integer truncation "7 items bug") and zero amounts

- **industry**: exclude locally supplied inputs from factory depletion time calculation to prevent premature simulation halting

## v0.8.0 (2026-08-31)

### Feat

- **industry**: add capability to sync rigs (TASK-109) and fix forms mapping (TASK-111)
- **industry**: add capability to sync rigs (TASK-109) and fix forms mapping (TASK-111)
- add task-108 documentation for BOM-based cost calculation research and recommendations

## v0.7.0 (2026-08-28)

### Feat

- **ui**: simplify Build Steps table (#106)
- add commit skill definition for automated git workflow management

## v0.6.0 (2026-08-28)

### Feat

- **ui**: add progress bar to Build Steps (#104)

## v0.5.7 (2026-08-28)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- prevent material overcount on dashboard and rename menu item

## v0.5.5 (2026-08-27)

### Refactor

- move blueprint requests to director dashboard tab

## v0.5.4 (2026-08-27)

### Feat

- blueprint library category filtering added

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- correctly show requested runs on accepted blueprint requests

- fixed invalid image URLs for blueprint originals and copies

- replaced me/te columns with badges in blueprint datatables

## v0.5.3 (2026-08-27)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- resolve ESI cache issue on empty db and properly read pydantic models

## v0.5.2 (2026-08-26)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- round calculated remaining materials to whole numbers

## v0.5.1 (2026-08-26)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- sync version in __init__.py for build system

## v0.5.0 (2026-08-26)

### Feat

- add industry job ownership filtering and fix expected output calculation logic
- improve Build Steps remaining calculation and dashboard UI

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- hide expected_output in UI when equal to runs

## v0.4.2 (2026-08-25)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- mapped ESI reaction activity ID (9) to SDE reaction activity ID (11) for accurate expected output calculation

## v0.4.1 (2026-08-25)

### Feat

- split job linking to fix overdelivery and add expected output to dashboard (Fixes #36, Fixes #33)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- ensure active and ready jobs bypass claim date filter (Fixes #37)

- include eve_delivered in completed column for build steps

## v0.4.0 (2026-08-25)

### Feat

- add corp stock visibility and refine job filtering

## v0.3.13 (2026-08-23)

### Feat

- display corp stock in BOM and shopping list views
- display version number in header

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- allow over-delivery on task claims and accurately track EVE delivered runs

## v0.3.12 (2026-08-18)

## v0.3.9 (2026-08-18)

## v0.3.8 (2026-08-17)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- Ensure ESI aggressive cleanup triggers correctly on 0 jobs and handles 304 cache properly

## v0.3.7 (2026-08-17)

## v0.3.6 (2026-08-15)

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- add datatables countdowns and implement numeric sorting for ISK values

## v0.3.5 (2026-08-13)

### Feat

- release version 0.3.5
- implement server-side DataTables, add transaction ledger, and localize dashboard interface
- add workflow_dispatch trigger to release workflow
- **orders**: Add quantity multiplier for fit imports
- **ui**: Add top and bottom pagination to DataTables
- **ui**: Sort job market by oldest tasks first
- **ui**: Inject global alert for failed background tasks on all auth pages
- **ui**: Add slide-in warning for failed background tasks on director dashboard
- **tasks**: Link claimed tasks to ESI jobs (TASK-12)
- add release 0.3.1 documentation for PI sync, translation, and job market bugfixes

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- restore job market rollup filtering, fix claim UI, and resolve DataTables pagination visibility for v0.3.4 release

- improve faction blueprint ME detection by verifying market group status and invention activity in bom_engine.py

- correct remaining calculation and activity filtering for industrialist dashboard and standardize backlog task frontmatter

- **director**: Fix ImportError for EveCharacter in generate_payout_batch

- **tasks**: Fix CharacterOwnership reverse accessor for EveCharacter

- **models**: Export TaskJobLink to fix celery import error

- **ui**: Fix SafeString escaping for global alert in auth hooks

- **tasks**: Fix EveCorporationInfo import in wallet task

- **bom**: Use EveIndustryActivityDuration instead of EveIndustryActivity

- default ME to 0 for faction blueprints and reactions without skipping overrides

- resolve TypeError in get_blueprint_me where ME value could be None

- isolate task tree folding logic per table to prevent incorrect indentations in job market

### Refactor

- update URL tests to assign response variables and remove unused imports and configuration in pytest.ini
- assign request responses to variables
- **ui**: Remove redundant django messages for failed tasks in favor of global auth warning

## v0.3.1 (2026-08-05)

### Feat

- add docker test script and clean up URL integration tests
- implement ESI-based corporation wallet division name retrieval and update
- enhance director inventory management with build/buy options, in-progress tracking, and cached Fuzzwork pricing.
- implement auto-production/buy orders for low stock, add wallet threshold alerts, and refactor task claiming to recursive logic.
- add access controls to all views, implement BOM chunking logic, and improve blueprint icon rendering.
- implement multi-corporation configuration support and order splitting functionality
- enable director order deletion and implement cascading cleanup of associated production tasks
- replace HTMX facility updates with server-side page reloads and add ME override management for corporate quotes

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- improve PI notification planet names and update wipe_industry_data command to include payout batches

### Refactor

- replace percentage symbols with text in field help labels and add locale compilation script
- implement comprehensive test suite, modularize orders views, update dashboards, and expand internationalization support
- modularize views and tasks for improved organization and maintainability

## v0.1.0b15 (2026-07-10)

### Feat

- add facility management and production task control improvements with updated documentation

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- **ui**: remove character selection, add datatables to dashboard, and improve fit parsing regex

## v0.1.0b14 (2026-07-05)

### Feat

- add upfront payment tracking and redesign the personal dashboard UI while cleaning up legacy documentation
- replace inline deletion prompts with a reusable bootstrap modal for director configuration items
- implement task execution logging, add pagination for industry job syncs, and introduce automated wallet payment processing
- add builder reward system and industrialist dashboard improvements with bulk data management command
- add expand/collapse all functionality to production trees and fix BOM calculation logic for multi-run blueprints.
- implement custom pricing overrides and introduce utility template tag for ISK formatting
- implement recursive production tree drill-down for Bill of Materials and add page restore overlay support.
- bump version to v0.1.0b5 and replace order deletion browser confirms with Bootstrap modals.
- add order deletion capability, move leaderboard to basic access, and update permissions documentation
- update industry director dashboard and synchronize virtual environment dependencies
- implement Amarr Gold glassmorphism theme and update dashboard layouts with refined styling
- implement industrialist dashboard, production task system, and leaderboard with associated UI and management permissions.

### Fix

- **blueprints**: prevent ESI sync task from deleting all corporate blueprints when encountering a 304 Not Modified response

- **ai**: round up AI forecasted target stock to nearest integer to prevent generation of 0-quantity ProductionTasks

- **ai**: correct Opportunity Scanner database query for missing blueprints to use actual corporation id

- **blueprints**: implement missing pagination when fetching corporate blueprints from ESI API

- **blueprints**: fix is_original property to correctly classify BPCs as copies instead of originals

- resolve PI product naming mismatches in tasks and address UI collapse/expand stability, plus bump version and add diagnostic scripts

- add duplicate validation for config/discount forms and update discount table display

- resolve display bugs in order quotes by adding original price calculation and updating UI elements

### Refactor

- migrate tests and coverage settings to industry_reforged and add eveuniverse to installed apps
- rename package to industry_reforged, add corporate wallet tracking, and implement BOM engine for material calculations
