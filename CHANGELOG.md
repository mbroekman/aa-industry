# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.3.11] - 18-08-2026

### Fixed

- **Industrialist Dashboard**: The "My Corporate Jobs" and "Corporate Jobs Overview" tabs now strictly filter jobs. They will only display EVE jobs that are successfully linked to an active `IN_PRODUCTION` claimed task. Unrelated jobs, personal jobs, or jobs linked to completed tasks will no longer clutter the view (TASK-79).

## [0.3.10] - 18-08-2026

### Fixed

- **Industrialist Dashboard**: Fixed an issue where fully completed tasks were still showing up in the "Build Steps" view and artificially absorbing unrelated active EVE jobs. The Build Steps now strictly only show items that have pending `IN_PRODUCTION` tasks (TASK-78).

## [0.3.9] - 18-08-2026

### Fixed

- **Task Job Linking**: Fixed an issue where old, previously completed EVE jobs were incorrectly linked to newly claimed production tasks. Jobs are now strictly filtered and will only link if their expected completion time (`end_date`) is strictly *after* the exact moment the task was claimed (TASK-77).

## [0.3.8] - 17-08-2026

### Fixed

- **ESI Syncing (Hotfix)**: Fixed a bug where the aggressive ESI cleanup logic would fail to run if the application received a `304 Not Modified` cached response or if a user genuinely had zero jobs. The sync task now tracks successful HTTP requests instead of list size to safely run the cleanup (TASK-76).

## [0.3.7] - 16-08-2026

### Added

- **Industrialist Dashboard**: Added a new "My Corporate Jobs" tab to specifically track EVE jobs installed by the user's characters (TASK-70).
- **Industrialist Dashboard**: Upgraded the general "Corporate Jobs Overview" tab to include the same advanced filtering (Active, Ready, Delivered, etc.) and visual status indicators as the "My Corporate Jobs" tab (TASK-74).
- **Industrialist Dashboard**: Enhanced the "Build Steps" tab to split "EVE In Progress" into "EVE Active" and "EVE Ready", providing better insight into which jobs are ready to deliver. A "Ready" option was also added to the filter dropdown (TASK-71).

### Fixed

- **ESI Syncing**: Fixed a critical synchronization bug where ESI caching caused delivered/cancelled jobs to be ignored in favor of stale "active" statuses. Implemented a self-healing cleanup mechanism that automatically updates active/ready jobs to "delivered" if they inexplicably drop off the ESI response. Jobs that were delivered in-game will now properly update in the app after a data refresh (TASK-75).
- **DataTables Sorting**: Fixed an issue where the "End Date" column (which includes HTML countdown text) sorted alphabetically instead of chronologically across the Industrialist and Personal dashboards (TASK-72).

## [0.3.6] - 15-08-2026

### Fixed

- **BOM Engine**: Fixed a critical bug in the recursive BOM calculation for Reactions and PI materials (e.g., Tungsten Carbide) where missing blueprint data caused the system to hardcode the yield quantity to 1 instead of its proper output size (e.g., 10,000). This caused wildly inflated required material quantities and build times.
- **DataTables Sorting**: Fixed an issue across all dashboards (Orders, Tasks, Leaderboard) where columns formatted with the `eve_isk` filter sorted alphabetically rather than numerically (TASK-68).

## [0.3.5] - 13-08-2026

### Added

- **Director Dashboard**: Added a "Ledger Transactions" tab to track all internal payouts and payments.
- **Personal Dashboard**: Added a dedicated "Research & Invention" tab that groups research jobs (ME/TE/Copying/Invention) per character.
- **Personal Dashboard**: Added a "Character" column to the Manufacturing Jobs tables.
- **UI Dashboard**: Added an Activity filter dropdown to both the Corporate and Personal Industry Jobs dashboards (TASK-66).

### Fixed

- **ESI Sync**: Fixed a major bug where active long-running jobs (like Titans) disappeared from the corporate dashboard due to ESI dropping them after 90 days. Added pagination, double-fetching, and safer cleanup logic (TASK-65).
- **Database**: Added data migration `0043` to automatically restore active jobs that were falsely marked as `delivered` by the old sync logic.

## [0.3.4] - 11-08-2026

### Fixed

- **UI Dashboard**: Restored `bom_parent__isnull=True` filter to the Job Market to prevent excessive subtaks and restored Claim functionality.
- **UI Dashboard**: Fixed missing DataTables "Items Per Page" dropdown on the initial load of the Claimed Jobs page.

## [0.3.3] - 09-08-2026

### Added

- **UI Dashboard**: Added a search bar to the "Build Steps" summary tab.
- **UI Dashboard**: Added a legend to the active tasks list to clarify the behavior of the blue and yellow "Complete" buttons.
- **UI Dashboard**: Added copy-to-clipboard icons for item names in the Build Steps tab, and for ISK amounts/references in the Director Payouts tab to easily paste values in-game.

### Changed

- **UI Dashboard**: Flattened the production tasks lists in the Claimed Jobs tab; hierarchical tree views and indentations have been removed for better overview.
- **UI Dashboard**: Replaced "Order Progress" text with "Material Progress".
- **UI Dashboard**: The Material Progress badge now tracks actual "Available" materials, accurately deducting completed materials that have already been consumed by downstream tasks in production.
- **UI Dashboard**: In the Build Steps summary, renamed the "To Build" column to "Claimed" and updated the "Remaining" formula to subtract "EVE In Progress" amounts as well.

### Fixed

- **UI Dashboard**: Fixed a styling issue in the Darkly theme where the `bg-dark-subtle` class resulted in unreadable white text on a light gray background.
- **Payouts**: Tasks with a reward of 0 are now filtered out from the Recent Completed Tasks list.
- **Payouts**: Fixed missing ISK formatting on reward amounts in the ledger.
- **Backend**: Resolved a `TypeError` (`unsupported operand type(s) for +: "QuerySet" and "list"`) in the industrialist dashboard view.
- **Backend**: Resolved row displacement bugs in DataTables caused by residual tree-rendering javascript.

## [0.3.2] - 06-08-2026

### Fixed

- **BOM Engine**: Fixed a `TypeError` in `get_blueprint_me` where missing `manual_me` values on blueprint overrides returned `None` instead of properly falling back to the default Material Efficiency.
- **BOM Engine**: Excluded non-researchable blueprints (such as Faction or Storyline) and reactions from Material Efficiency calculations (defaulting to 0), without skipping their `max_runs` override logic.
- **BOM Engine**: Fixed a `FieldError` on the Shopping List where it incorrectly queried `activity_id` on `EveIndustryActivity` instead of `EveIndustryActivityDuration`.
- **Wallets**: Fixed an `ImportError` where the background task `task_process_wallet_payments` failed due to a missing core Alliance Auth import for `EveCorporationInfo`.
- **Payouts**: Fixed an `ImportError` in `generate_payout_batch` caused by an incorrect import path for `EveCharacter`.
- **UI Dashboard**: Added a notification popup (alert) on the Director Dashboard for failed background jobs, linking to the execution logs.
- **UI Dashboard**: Fixed an issue on the Industrialist Dashboard where `Remaining` amount was incorrectly subtracting EVE jobs in progress, and ensured EVE jobs are correctly filtered by both `product_type_id` and `activity_id`.

### Changed

- **UI Dashboard**: The Job Market (Unclaimed Tasks) is now sorted so the oldest orders always appear at the top.
- **UI Dashboard**: All pages containing lists now display pagination controls both at the top and the bottom of the table to prevent unnecessary scrolling.

## [0.3.1] - 05-08-2026

### Fixed

- **PI Sync**: Fixed an issue where Planetary Interaction planet names were missing in the dashboard due to ESI 304 Not Modified responses skipping the `EvePlanet` creation step.
- **Translations**: Resolved a gettext `python-format` compilation error caused by percentage signs in `help_text` strings.
- **Job Market**: Fixed an issue where root jobs in the Job Market were incorrectly rendered with folding buttons and indentation if they shared an ID with parents in the Active Production table.
- **CI / Testing (TASK-17)**: Fixed Python 3.13 test failures and Codecov upload issues in GitHub Actions.

## [0.3.0] - 04-08-2026

### Added

- **Order Creation**: Added a "Quantity (Multiplier)" field to the Create Order page. This allows users to easily multiply the quantities of an entire EFT fit or bulk text input without needing to edit the raw text.

- **PI Location Tracking**: Planetary Interaction dashboards now explicitly display the Solar System and specific Planet Name (e.g., `Jita » Jita IV`) instead of just the generic planet type.

- **PI Notifications**: Added unified Alliance Auth and direct Discord DM notifications for PI events. Users are automatically notified when an extractor stops.

- **Configurable PI Storage Thresholds**: Users can now configure the percentage at which they receive full storage/launchpad warnings directly from their Personal Dashboard settings (defaults to 75%).

- **Completed Tasks Summary (TASK-8)**: Added functionality to view a summary of completed production tasks directly from the Industrialist dashboard, with filtering options for Active, Completed, or All tasks.

- **Wallet Division Names**: The system now retrieves and updates dynamic corporation wallet division names directly from EVE ESI instead of using static defaults.

- **Extensive Test Coverage (TASK-1)**: Added extensive unit tests and test coverage across the application to prevent regressions.

### Changed

- **UI Dashboard Enhancements (TASK-15)**: The Build Steps are now intuitively grouped by Activity Type (Manufacturing, Reactions, etc.) with empty groups automatically hidden when filtering.
- **Terminology Update (TASK-10)**: Globally renamed "Assigned To" to "Claimed By" and "Member Tasks" to "Claimed Jobs" for clarity across all tables and views. "Task Summary" is now "Build Steps".
- **Codebase Refactoring (TASK-2, TASK-3)**: Major codebase cleanup including splitting large modules (`views.py`, `urls.py`, `tasks.py`, `models.py`) into smaller domain-specific files, fixing linting errors, and re-enabling Pylint checks.
- **Translation Review (TASK-4)**: Reviewed and updated localization/translation strings across the application.
- **Dutch Translations (TASK-16)**: Translated 474 missing text strings in `django.po` to Dutch and compiled it to `django.mo` for full localization.

### Fixed

- **Reactions In Progress Quantity (TASK-14)**: Fixed a bug where the "In Progress" column on the dashboard showed the number of runs instead of the actual produced quantity for Reactions. The system now dynamically fetches the correct `activity_id` from the SDE.
- **ME Application Logic (TASK-6)**: Fixed a bug where Blueprint Material Efficiency (ME) reduction was incorrectly applied to items that are not built from blueprints (like reactions).
- **TypeError in BOM Engine (TASK-13)**: Resolved `TypeError: '>' not supported between instances of 'NoneType' and 'int'` occurring during BOM recursive tree generation when `max_runs` was missing (e.g. for Command Centers).
- **AttributeError in Orders (TASK-9)**: Fixed `AttributeError: 'MemberOrder' object has no attribute 'corporation'`.
- **Structure Type Recognition (TASK-5)**: Fixed a bug where a Fortizar was incorrectly identified as a Tatara type structure.
- **UI Cleanups (TASK-7)**: Removed unnecessary strikethrough text from completed member tasks in the UI to improve readability.

## [0.2.0] - 21-07-2026

### Added

- **Production Summary**: Added a new tab to the Director Control Panel that aggregates all active production (unclaimed, in production, completed) per item type, featuring a stacked visual progress bar.
- **Facility Default Status**: Directors can now mark a specific Production Facility as the "Default" structure. The system automatically ensures only one facility can be default at a time.
- **Auto-select Default Facility**: When a user creates a new order, the system now automatically pre-selects the corporation's default facility for accurate price and BOM quoting out of the box.
- **Dynamic Rig Formsets**: Added an "Add Rig" button to the Facility Edit page, allowing Directors to add multiple rigs dynamically without reloading the page.
- **Procurement Buy Orders**: The automated restocking system now intelligently differentiates between items marked as "Build" and "Buy". "Buy" items automatically generate a `CorpBuyOrder` (instead of a `ProductionTask`), which appears in a new dedicated "Procurement Buy Orders" tab for directors to track purchases (Open, In Progress, Fulfilled).
- **Master Shopping List**: Added a "Master Shopping List" button to the Restock Needed page, allowing directors to instantly generate a consolidated Jita buy-list for all current stock deficits.
- **Wallet Threshold UI**: The warning threshold configuration for corporate wallets has been moved from the admin panel to the frontend Director Wallets page for easier access, complete with ISK-formatted inputs.
- **EVE Truth Mathematical Accuracy**: The BOM Engine now fully integrates the EVE Online exact material equation: `run_cost = round(base_qty * ((100 - ME)/100) * facility_me_multiplier, 2)` followed by `math.ceil()`.
- **Modifier UI Badges**: The "Production Tree" (sitemap) view now explicitly displays a badge per node showing the Blueprint ME, Rig bonus, Structure bonus, and Facility Name used to calculate that component's requirements.
- **EVE Industry Documentation**: Added a comprehensive `calculating_material.md` reference document explaining the EVE Truth formulas and how the engine replicates them.

### Changed

- **UI/UX DataTables**: Removed double horizontal and vertical scrollbars across the app by standardizing `w-100` and `autoWidth: false` on all DataTables, removing artificial height constraints on the Production Tree, and moving pagination controls to the top of the tables.
- **ME Overrides Tab**: Renamed the "ME Overrides" tab to "ME & BPC Overrides" to clarify that users can also adjust BPC `max_runs` there for job chunking.
- **Global Rigs**: Rigs that have no specific EveGroup or EveCategory restrictions in the database are now treated as "Global" rigs and correctly apply their bonus to all items produced in that facility.

### Fixed

- **Fuzzwork API Caching**: Added aggressive Django caching to the Fuzzwork pricing engine to prevent 30s+ UI hanging (infinite loading) when spawning jobs while the external API is slow or unresponsive.
- **Infinite Loading Fix**: Resolved a logic loop where the "Restock Needed" alerts list did not account for jobs already in progress. The UI now subtracts active jobs/orders from the deficit and instantly removes the item from the alerts list once fully procured.
- **Corporate Jobs ESI Sync**: Fixed a critical bug where the Celery task for syncing corporate jobs would crash due to "Task not found" or `aiopenapi3` formatting issues. The tasks now correctly parse the ESI paginated `.results()`.
- **Corporate Facilities ESI Sync**: Overhauled the structure discovery logic. Previously, empty corporate structures or those without active jobs were invisible. The system now directly queries the `esi-corporations.read_structures.v1` endpoint to automatically sync and list ALL Upwell structures belonging to registered corporations.
- **Facility NoneTypeError**: Fixed a `TypeError: cannot unpack non-iterable float object` crash that occurred when opening a shopping list without a specific target facility selected.
- **Rig Application Math**: Rigs correctly stack and pick the highest applicable bonus per facility, preventing issues where empty rig configurations nullified bonuses.

## [0.1.0b18.post1] - 16-07-2026

### Added

- **Access Controls**: Implemented strict `permission_required("industry_reforged.corp_access")` and `login_required` decorators across all view endpoints.
- **BPC Max Runs (Job Chunking)**: Added the ability to specify the maximum number of runs per blueprint copy. The BOM engine now chunks massive orders into smaller "jobs" before applying the EVE Online rounding formula (`math.ceil`) per job, ensuring 100% accurate raw material quotes when building from limited-run BPCs.

### Fixed

- **BOM Tree Chunking Crash**: Fixed a `TypeError: unsupported operand type(s) for -: 'float' and 'tuple'` crash caused by the new BPC `max_runs` tuple return value not being unpacked when viewing the Production Tree UI.
- **BOM Tree UI Accuracy**: Added the missing `max_runs` Job Chunking calculation directly into the visual Production Tree so that the required quantities displayed in the UI perfectly match the quantities calculated by the background job calculator.
- **Missing Blueprint Icons**: Fixed an issue where the EVE Image Server would return broken/generic fallback icons for Invention, Copying, and Research jobs because blueprints do not have standard `/icon` images. The dashboards now dynamically fallback to the correct `/bp` endpoint.

## [0.1.0b18] - 15-07-2026

### Changed

- **Code Architecture**: Completely refactored `views.py` and `tasks.py` into their respective modular packages (`views/` and `tasks/`) for better maintainability and organization.
- **Task Imports**: Resolved broken celery task imports resulting from the modularization of the tasks module.

## [0.1.0b17] - 13-07-2026

### Added

- **Order Splitting (Sub-orders)**: Directors can now split an order into multiple sub-orders. This includes the ability to select specific ordered items to split off into a separate child order, as well as the ability to click on any sub-component in the BOM tree and spawn a dedicated sub-order for its production (e.g., manufacturing components at a different facility).
- **Facility Rigs Auto-Seeding**: Added a data migration to automatically seed the database with the most common Upwell Structure rigs (e.g. Standup Ship/Equipment Manufacturing) so they are immediately available for external facility configuration.
- **Discord Order Deletion Webhook**: When a user explicitly deletes an order, a notification is now sent to the corporation's designated Discord Webhook channel, allowing directors to be instantly informed of canceled orders.

### Changed

- **Director Order Deletion**: Directors can now delete an order from the Corporate Panel at any stage (even if it has already been accepted). Doing so will now also explicitly delete and clean up all associated `ProductionTask` items generated for that order.
- **Frontend Configurations**: All corporate business rules (Global Pricing, Type Discounts, Item Configs, System Taxes) have been completely removed from the Django Admin interface. They are now fully manageable directly from the frontend (Director Control Panel).
- **Multi-Corporation Support**: The Director Control Panel now supports configuring business rules and discounts for *all* allied corporations in the system, not just the Director's own corporation.

### Fixed

- **Order Splitting UI for Normal Users**: Fixed a UI issue where split sub-orders were shown as separate technical blocks for normal end-users. The system now automatically merges all sub-order items back into the original Itemized Invoice table visually, providing a seamless experience for end-users while retaining sub-orders for directors.
- **Proportional Custom Quote Pricing**: When a Director provides a custom total price for a quote, the system now automatically scales all individual line items' unit prices and line totals proportionally to match the exact custom total.
- **Quote Validation Corp Scoping**: Fixed multiple bugs where the webhook notification and `calculate_quote` functions were incorrectly scoped to the viewing Director's corporation instead of the ordering Character's corporation.
- **Leaderboard DataTables Error**: Fixed an `Incorrect column count` DataTables crash on the Industrialist Leaderboard that occurred when a user had no history items.

## [0.1.0b16] - 13-07-2026

### Added

- **Material Efficiency (ME) Overrides & Exact EVE Math**: The Order Quote page now supports dynamic Material Efficiency settings, mirroring EVE Online's exact batch savings math. The system calculates requirements using the formula: `run_cost = round(base_qty * ((100 - ME)/100) * facility_me_multiplier, 2)` followed by `required_qty = max(runs, math.ceil(run_cost * runs))`. Directors can override the default T1/T2 ME on a per-blueprint basis during quoting.
- **Recursive Task Completion**: Completing a parent production task in the dashboard now offers a confirmation dialog to recursively complete all of its unfinished child sub-tasks automatically.
- **Excluded Items in BOM**: Excluded modules are no longer completely hidden. They now appear in the Recursive Order Tree as raw material leaf nodes (marked with a red badge), ensuring they are still tracked for corporate inventory deduction but are not tasked to builders.

### Changed

- **Inventory Sync Toggle**: Added a "Sync Inventory" toggle to the Production Facilities configuration tab. Facilities will no longer sync their inventory to the Corporate Stock by default unless explicitly enabled.

### Fixed

- **PI Modal Cross-Contamination**: Fixed a critical HTML ID collision in the PI Dashboard where clicking a factory planet could open the detail modal of another character's colony if they shared the same EVE Universe planet ID, incorrectly displaying extractors.
- **Inventory Cleanup**: Fixed an issue where the Corporate Inventory sync would fail to zero out stale items that were consumed or moved out of a tracked facility.
- **DataTables Column Count**: Fixed a "Incorrect column count" DataTable crash on the Inventory Analysis dashboard caused by malformed empty table placeholders.
- **Private Structure Sync**: Fixed an internal API token configuration bug that caused private structure synchronizations to fail.
- **Rigs Sync Crash**: Resolved a database query exception in the `sync_facility_rigs` background task when evaluating structure ownership.
- **Structure Security Space**: Fixed an issue where newly discovered structures defaulted to Highsec. The background task now dynamically evaluates the correct security status (High/Low/Null/WH).
- **Double Submission Prevention**: Added a loading spinner overlay to the "Apply Overrides" button on the quote page to prevent double-submitting.
- **Template Syntax Error**: Restored a missing block tag on the Quote page that was causing a Django `TemplateSyntaxError`.

## [0.1.0b15] - 10-07-2026

### Added

- **Dynamic Blueprint Icons**: The Recursive BOM Tree and Raw Materials lists now dynamically display the correct blueprint image (`/bp`) for a component when the standard item icon is not available on the ESI image server.
- **Facility Discovery Workflow**: Overhauled the Corporate Facilities system. The plugin now dynamically discovers corporate Upwell structures and private structures based on jobs and assets, storing them as known locations. Directors can then explicitly configure these discovered structures as active **Production Facilities**, automatically determining their true security space (Highsec, Lowsec, Nullsec).
- **Planetary Interaction Storage**: Added visual progress bars and tooltips to the PI dashboard to track storage utilization (Launchpads and Storage Facilities) for all PI characters.
- **Upwell Structure Names**: The Corporate Facilities list now displays the human-readable Upwell structure name (e.g., Athanor, Raitaru) instead of the raw EVE Type ID.
- **Facility Rigs Auto-Sync**: Added an automated Celery background task (`sync_facility_rigs`) that fetches and syncs installed rigs for registered corporate facilities using ESI assets.
- **Quote Notifications**: Directors providing a quote for an order will now automatically trigger a Discord Direct Message (DM) to the member who requested the order, alerting them that their quote is ready for review.
- **Hangar Search Bar**: Added a quick search bar to the "Discover Corporate Hangars" page for easy filtering of locations and flag IDs.
- **Wait Dialogs**: Added the global "Processing Request" loading overlay to the main dashboard links in the sidebar to prevent confusion during heavy data fetching.
- **Order Options (Parsing)**: The Order Creation page now supports robust Regex parsing for freeform text (e.g. `20 drakes`) and EVE client Multibuy exports (e.g. `Drake 20`). The system also normalizes common English plurals (like "drakes" -> "drake", "batteries" -> "battery") before verifying with ESI to prevent unrecognized item errors.
- **Member Tasks Filter**: Added a dropdown filter (Open Tasks Only / Completed Tasks Only / Show All) to dynamically toggle visibility of active and completed tasks on the Industrialist Dashboard.
- **Order Item Exclusion**: Corp Directors can now configure specific items (e.g. Deadspace/Faction modules) via the Corporate Configuration frontend to be automatically stripped (excluded) from Member Orders. Members receive a customizable warning message explaining why the item was removed from their requested fit. The configuration table has also been upgraded with a search bar and sortable columns.
- **Claimed Tasks Summary View**: Added a dedicated "Task Summary" tab to the Industrialist Dashboard. This view aggregates all claimed tasks by item type and compares them against live ESI industry jobs, showing exactly how many items are "In Progress" in EVE versus how many are still remaining to be started.
- **Leaderboards**: Added DataTables search and sort functionality to the "My Completed Tasks History" table.

### Changed

- **Character Selection**: Removed the manual character selection dropdown from the "Create Order" and "Claim Task" forms. The system now strictly defaults to the user's configured Main Character for all industry requests and job claims.
- **Dashboard UI Improvements**: Unified the "My Active Production" and "My Completed Tasks" tables into a single card container on the Industrialist Dashboard, managed by client-side Javascript to save screen space.
- **PI Storage Warning**: Lowered the threshold for the "Storage Almost Full" PI dashboard warning icon from 90% to 75% utilization to better align with the progress bar warning colors.

### Fixed

- **System Health Logs**: Replaced the small Bootstrap popovers on the System Health tab with centered modals to prevent text clipping of large Python stack traces from failed Celery tasks.
- **Dashboard State Preservation**: Fixed an issue on the Director Dashboard where actions in the Pending Payouts or Orders tabs would redirect the user back to the default tab. The dashboard now correctly uses URL fragments (e.g., `#payouts-pane`) and JavaScript to remember and reload the active tab state after an action.
- **PI Storage Volumes**: Fixed an issue where ESI would return multiple duplicate stacks of the same item type inside a Planetary Storage facility. The tooltip now properly aggregates all identical item stacks before calculating the total volume, ensuring the UI values match the in-game volumes perfectly.
- **ESI Pagination Bug**: Fixed a critical bug in `task_sync_corp_inventory` where only the first 1,000 corporate assets were fetched. It now properly uses pagination to sync all assets.
- **Production Tree Layout**: Fixed a Bootstrap layout bug where the BOM and Details tabs would take up invisible vertical space, causing a large empty white gap above the Recursive Production Tree.
- **PI Character Cards**: Fixed an issue where extraction-only (P0) planets would display an empty card without product icons. The system now correctly falls back to showing the extracted raw materials if no factories are present on a planet.
- **Corptools Import Crash**: Hardened the `corptools` fallback check to use Django's `apps.is_installed()` to prevent 500 Server Errors when the package is installed in the python environment but not active in `INSTALLED_APPS`.
- **Industrialist Dashboard**: Fixed a bug where clicking the "Select All" checkbox in the Job Market would incorrectly select hidden tasks that were filtered out by the search bar. The "Select All" action now correctly applies only to visible tasks.
- **Industrialist Dashboard HTML**: Fixed an issue where the "Corporate Jobs" tab was inadvertently hidden due to a malformed nested `div` wrapper.
- **Template Rendering Crash**: Fixed a Django `TemplateSyntaxError` caused by multi-line template tags resulting from automated HTML formatting tools breaking the template parser.

## [0.1.0b14] - 05-07-2026

### Fixed

- **BOM Tree Drilldown**: Fixed an HTML ID collision bug in the recursively generated Bill of Materials tree that caused the "Drilldown" and "Expand All" JavaScript functions to break on complex orders with duplicate sub-components.
- **PI ESI Sync**: Fixed a crash in the Planetary Interaction synchronization task caused by `django-esi` upgrading to `aiopenapi3`, completely bypassing the OpenAPI client bug with a direct `requests.post` call.
- **PI Product Badges**: Fixed an edge-case bug where 3 specific PI products ("High-Tech Transmitter", "Ukomi Superconductor", "Transcranial Microcontroller") failed to receive their badges due to an ESI spelling mismatch (singular schematic name vs plural inventory type name).

## [0.1.0b13] - 04-07-2026

### Added

- **PI End Products**: The Planetary Interaction Character cards now visibly display the highest tier end products (T1-T4) produced across all their planets, allowing for an instant overview of what each character is manufacturing.
- **Partial & Upfront Payments**: Added support for upfront payments and partial payments. Directors can now specify an optional upfront payment when quoting an order.
- **Wallet Scanner Enhancements**: The automated ESI wallet scanner now processes partial payments, accumulates the `amount_paid`, and logs every transaction to the order notes. The order automatically transitions to "Paid" once the full amount is reached.
- **Quote & Payment Modals**: Overhauled the manual payment flow and quoting logic. Added a dynamic ISK formatting visual helper (e.g., `100.00m`) that updates instantly as directors type amounts. Quoting an order now allows for appending custom notes, and specifying an upfront payment will automatically register as a completed partial payment, accurately updating the `amount_paid` and `Remaining Balance`.
- **Order Notes Display**: Order Notes are now beautifully rendered directly on the Order Details page (above the Raw Fit block), providing a timeline of partial payments, auto-sync wallet detections, and manual director notes.
- **Order Details Financials**: The order details page now clearly displays the `Amount Paid` and `Remaining Balance`, avoiding duplicate data by removing the confusing "Upfront Reqd" label.
- **Manual Payment Override**: Removed the 100% completion restriction for marking an order as paid manually. Replaced native browser popups with a modern Bootstrap modal that supports custom partial payment amounts and optional notes.
- **Shopping List Loading Modal**: Implemented a global full-screen "Processing" modal with a spinner when generating Shopping Lists from the Member Jobs and Orders Dashboards, improving user feedback during heavy BOM calculations.
- **Shopping List Tree Search**: Added a quick search bar to the Production Tree tab that dynamically filters and auto-expands parent nodes to highlight matched items.
- **Shopping List Treeview**: Upgraded the Consolidated Shopping List page to include a new interactive "Production Tree" tab. Users can now view a fully recursive drill-down tree of all materials across multiple selected orders or tasks.
- **Planetary Interaction Dashboard Redesign**: Completely overhauled the personal PI interface into a clean, 3-level Card and Modal drill-down system. Level 1 groups planets into Character cards. Level 2 lists Planet cards with a live countdown of the most urgent extractor. Level 3 uses a detailed popup modal grouping Extractors (with timers), Factories (categorized by tier T1-T4 and status), and Infrastructure.
- **Reaction & Invention Support (Local SDE)**: Migrated the entire Bill of Materials (BOM) calculation engine from the external Fuzzwork API to the local `eveuniverse` SDE. The system now seamlessly calculates material requirements for Reactions (Activity ID 11) in addition to standard Manufacturing, and relies entirely on local database queries for lightning-fast, highly accurate data.
- **Admin Configuration Settings**: Registered the `CorpPricingConfig`, `CorpItemConfig`, and `TaxConfig` models to the Django Admin panel, allowing administrators to properly configure discounts, rewards, tax rates, and manual item price overrides.

### Changed

- **Prominent Quotes/Notes**: Order Notes (and Director Quotes) are now styled much more prominently as a bright alert block on the Order Details page, positioned above the raw fit to ensure they aren't missed.
- **Flat BOM Optimization**: The "Flat Overview" tab on the Shopping List now recursively aggregates ONLY the base raw materials (minerals, PI, etc.) needed to produce the entire order from scratch. This prevents double-counting costs for intermediate components and provides a highly accurate purchasing list.
- **UI Enhancements**: Made the dynamic motivational slogan on the Industrialist Dashboard larger and more prominent.
- **Confirmation Modals**: Replaced all native browser popups (`window.confirm`) on the Director Dashboard (e.g., Mark Paid, Deliver, Generate Batch) with modern, uniform Bootstrap modals.
- **Admin Optimization**: Added `raw_id_fields` to foreign keys linked to large tables (such as `EveType` and `EveCorporationInfo`) in the Django Admin interface. This prevents the browser from crashing and freezing when attempting to render dropdown menus with over 40,000 items.

### Fixed

- **PI Product Sync**: Fixed a synchronization issue where previously fetched Planetary Interaction factories would fail to show their output product (e.g. "No Schematic") due to an ESI 304 cache loop. The background sync now safely resolves all missing products and schematics.
- **MOTD Fallback**: Fixed an issue where clearing or removing the Corp MOTD would unexpectedly show a hardcoded fallback text ("Welcome to the Industrialist Dashboard") instead of just hiding the text.
- **PI Pin ESI Bug Fix**: Implemented a workaround for a known ESI API bug where Planetary Interaction infrastructure pins (such as Basic Industry Facilities or Command Centers) are universally returned as the "Barren" variant. The sync logic now actively intercepts these and correctly remaps them to the appropriate environmental variant (e.g. Lava, Oceanic) based on the target planet.
- **Shopping List (BOM) Error Modal**: Fixed a Javascript bug on the Industrialist Dashboard where clicking the BOM button repeatedly without selecting any tasks would fail to show the error modal the second time.
- **Shopping List Crash Fix**: Resolved a critical backend error where generating a Shopping List (BOM) for individual production tasks would result in an empty treeview or a server crash.

## [0.1.0b12] - 2026-07-01

### Fixed

- **Director Config**: Fixed a bug where creating duplicate Item Configurations or Type Discounts would crash the application with a 500 Server Error (IntegrityError). The form now correctly catches this and displays a user-friendly validation error.
- **Director Config**: Fixed the "Type Discounts" tab template to correctly display the specific item type instead of an empty space, and restored the missing delete button functionality.

## [0.1.0b11] - 2026-06-30

### Added

- **Automated Order Delivery & Payment Tracking**: Orders now automatically track their payment status using a unique `ORD-` reference. A background task (`task_process_wallet_payments`) scans ESI Corporation Wallet Journals to automatically mark orders as "Paid" when the matching ISK and reference are found.
- **Order Delivery Workflow**: Added a "Mark as Delivered" button for Directors to finalize "READY" orders. Doing so triggers an Alliance Auth in-app notification to the buyer that their in-game contract is ready.
- **Industrialist Payout Batches**: Directors can now generate "Payout Batches" for individual builders, bundling all completed unpaid tasks into a single payout with a unique `PAY-` reference.
- **Automated Builder Payouts**: The Wallet Sync background task automatically marks payout batches and their associated tasks as "Paid" when the corporation transfers ISK out to the builder using the correct `PAY-` reference.
- **Automated Notifications & Webhooks**: When all tasks for an order are complete (Order moves to `READY`), all users with `director_access` receive an Alliance Auth in-app notification. If configured, a Discord webhook is also sent containing the price and payment reference.
- **Hierarchical Task Selection**: The Industrialist Dashboard now supports recursive checkbox selection. Selecting a parent task automatically selects all child sub-tasks. Added a "Global Complete" button alongside "Global Claim".
- **Dynamic Slogans**: Added random, industry-themed motivational slogans to the Industrialist Dashboard MOTD section.
- **System Health Monitor**: Added a new "System Health" tab to the Director Configurations page. This provides a clean overview of all Celery background tasks, displaying their latest status, run time, duration, and error traces.

### Changed

- **Task Completion Constraints**: Parent tasks can now only be marked as completed if all of their underlying child tasks are already completed.
- **Dashboard UI Improvements**: "My Active Production" tab now visually groups tasks hierarchically (parent-child relationship) to clarify the build sequence. Improved visibility of Payout amounts and added ISK hover tooltips to payout summaries.

### Fixed

- **Hangar Configuration UI**: Added the missing "Hangar Configurations" tab to the Director Config page so discovered hangars can actually be viewed.
- **Loader Javascript**: Fixed a bug where the loading overlay (`show-loader`) was broken on the Director Config and Wallet pages due to missing template super blocks.

## [Unreleased]

### Added

- **Order Options (Parsing)**: The Order Creation page now supports robust Regex parsing for freeform text (e.g., `20 drakes` or `Drake 20`) and EVE client Multibuy exports in addition to standard EFT/Pyfa fits.
- **DataTables Integration**: Added DataTables search and sorting capabilities to the "My Completed Tasks History" on the Leaderboard page, the "Personal Dashboard" jobs tables, and "Orders" tables.

### Changed

- **Character Selection Workflow**: The system now seamlessly relies entirely on the user's primary "Main Character" designated in their Alliance Auth profile. The legacy character selection dropdowns have been removed from the "Create Order" page and the "Claim Task" modals, vastly streamlining the user experience.

### Fixed

- **Template Tags**: Converted multiline Django template tags across multiple templates to single-line tags to resolve `TemplateSyntaxError` exceptions that were throwing 500 errors on the Industrialist dashboard.
- **Task Filtering**: The "Show only active tasks" toggle on the Industrialist dashboard is now fully functional and properly filters out claimed/completed tasks using client-side JavaScript.

## [0.1.0b10] - 2026-06-30

### Added

- **Builder Reward Percentage**: Introduced a configurable `builder_reward_percent` for Production Tasks. Directors can now set a fixed percentage in the Control Panel that calculates exactly how much ISK an Industrialist earns for building an item. The "Reward Value" column on the Industrialist Dashboard now displays this actual ISK payout, while the `gamification_value` continues to track the full ship value separately for the Top Builders leaderboard.
- **Hierarchical Task Generation**: Re-architected Quote Acceptance. Accepting a quote now dynamically generates a recursive Bill of Materials tree and creates claimable `ProductionTask`s for the top-level item *and every intermediate manufacturable component* (raw materials excluded). This allows multiple industrialists to collaborate on complex build chains (e.g. one builds the Capital Parts, another builds the Hull).
- **Double-Dipping Prevention**: Implemented smart reward nullification when claiming tasks. If an industrialist claims a sub-component task, and later claims the parent task, the reward for the sub-component is automatically reduced to `0.00` ISK to prevent the corporation from double-paying rewards for the same production line.
- **Job Market Search**: Added a real-time, client-side search bar to the Industrialist Dashboard, allowing builders to instantly filter the (now much larger) list of unclaimed hierarchical tasks by item name.
- **Developer Tools**: Added a new management command `python manage.py wipe_industry_data` to safely clear all existing test orders and production tasks during development/beta testing.

## [0.1.0b9] - 2026-06-29

### Fixed

- Fixed a display bug in the Order Details view where corporate discounts were applied correctly to the final price, but the "Original Jita Price" and "Savings" footer incorrectly showed the already discounted total. Individual discounted items now clearly show their original price crossed out next to the discounted price.
- Fixed an issue where the "Provide Quote" input field for Directors was incorrectly empty instead of being pre-filled with the calculated total order price. Added a convenient visual tooltip helper next to the input to quickly read large ISK abbreviations.

## [0.1.0b8] - 2026-06-29

### Changed

- Removed the "View Order BOM" (`+`) magnifying glass icon from the Industrialist Dashboard. Industrialists can generate an item-specific BOM directly using the "Shopping List" functionality.
- Replaced the browser-native confirmation popup for generating Shopping Lists with a consistent, styled Bootstrap modal.
- Hid the "Bill of Materials" tab on the Order View page from standard users (`basic_access`). Only Directors and Industrialists can now view the detailed raw material costs and BOM for an order.
- Improved the Recursive Production Tree (Drilldown) UI on the Order View page: added visual indicators (rotating chevrons) to show expanded/collapsed states, and introduced a single "Toggle All Drilldowns" button to easily expand or collapse the entire tree at once.

### Fixed

- Fixed a major calculation error in the BOM engine where the `productQuantity` (blueprint output yield) was ignored. This caused items that produce in batches (like ammunition, rockets, and drones) to wildly over-calculate the required raw materials and BOM cost by up to 100x.
- Fixed a broken HTML layout in the Industrialist Leaderboard where the right column (Top Builders by ISK) overlapped the left column due to an unclosed HTML tag.

## [0.1.0b7] - 2026-06-28

### Added

- **Functional Separation of Configurations**: Moved all corporate item configurations, global pricing, type discounts, and tax configurations out of the restricted Django Admin into the Director Control Panel.
- **EveType Smart Resolution**: Adding items to configurations now allows typing the item name (e.g., "Aeon") instead of selecting from a list of thousands of IDs.
- **Dynamic Quotes**: When a Director or User views a Quote in the "REQUESTED" state, the system now dynamically recalculates the price on the fly to immediately reflect any new corporate pricing configurations or overrides.
- **ISK Abbreviation Tooltips**: Created a new `eve_isk` template filter that automatically adds a hover tooltip to large ISK amounts, instantly translating numbers like "14,000,000,000.00 ISK" to "14.00B ISK" (K, M, B, T).

### Fixed

- Fixed an issue where manual price overrides (`CorpItemConfig.manual_price`) were ignored when generating a Quote or calculating Shopping List totals.

## [0.1.0b6] - 2026-06-27

### Added

- Replaced native browser confirmation popups with Bootstrap 5 modals for order deletion to match Alliance Auth styling.
- Persisted active tab state across page reloads on the Industrialist dashboard (you no longer get sent back to the first tab when completing a task).
- Implemented a recursive BOM (Bill of Materials) Drilldown feature in the order Quote view for Industrialists and Directors.
- Added Component Sourcing to the Drilldown tree, allowing users to generate a specific EVE Multibuy Shopping List for any intermediate material.
- Added dynamic MOTD (Message of the Day) stats to the Industrialist Dashboard, displaying real-time metrics (Orders in Production, Open Tasks, Active Corp Jobs, Value in Progress).
- Attached the loading spinner overlay to the "View Quote" buttons for a smoother user experience when calculating large orders.

### Fixed

- Fixed an issue where the loading spinner overlay would remain visible after clicking the browser's Back button (BFCache persistence fix).

## [0.1.0b5] - 2026-06-27

### Added

- Order deletion functionality for owners and directors (restricted to REQUESTED or QUOTED statuses).
- Global sidebar menu item for the Industry Leaderboard.
- Loading overlay during order quote generation to improve UX.
- Comprehensive group permissions proposal documentation.

### Changed

- Lowered Leaderboard permission requirement from `industrialist_access` to `basic_access` so all members can view top builders.
- Updated GitHub Actions CI/CD workflows to compile translations (`gettext`) before building PyPI packages.
- Updated `tox.ini` to use the native Django test runner instead of a custom script.

### Fixed

- Test suite failures by adding `eveuniverse` to the local test environment `INSTALLED_APPS`.
- Fixed coverage reporting by correcting the source path to `industry_reforged` in `.coveragerc`.
- Removed dynamic version number from app `verbose_name` to keep Django Admin permission names clean and static.
