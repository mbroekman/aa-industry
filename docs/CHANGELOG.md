# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [In Development] - Unreleased

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
