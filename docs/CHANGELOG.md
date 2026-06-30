# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [In Development] - Unreleased

## [0.1.0b10] - Unreleased

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
