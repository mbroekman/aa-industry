# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## v0.4.1 (2026-08-25)

### Feat

- split job linking to fix overdelivery and add expected output to dashboard (Fixes #36, Fixes #33)

### Fix

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

- allow over-delivery on task claims and accurately track EVE delivered runs

## v0.3.12 (2026-08-18)

## v0.3.9 (2026-08-18)

## v0.3.8 (2026-08-17)

### Fix

- Ensure ESI aggressive cleanup triggers correctly on 0 jobs and handles 304 cache properly

## v0.3.7 (2026-08-17)

## v0.3.6 (2026-08-15)

### Fix

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

- improve PI notification planet names and update wipe_industry_data command to include payout batches

### Refactor

- replace percentage symbols with text in field help labels and add locale compilation script
- implement comprehensive test suite, modularize orders views, update dashboards, and expand internationalization support
- modularize views and tasks for improved organization and maintainability

## v0.1.0b15 (2026-07-10)

### Feat

- add facility management and production task control improvements with updated documentation

### Fix

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

- resolve PI product naming mismatches in tasks and address UI collapse/expand stability, plus bump version and add diagnostic scripts
- add duplicate validation for config/discount forms and update discount table display
- resolve display bugs in order quotes by adding original price calculation and updating UI elements

### Refactor

- migrate tests and coverage settings to industry_reforged and add eveuniverse to installed apps
- rename package to industry_reforged, add corporate wallet tracking, and implement BOM engine for material calculations
