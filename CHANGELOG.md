# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)

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
