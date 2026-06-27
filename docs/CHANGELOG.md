# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [In Development] - Unreleased

## [0.1.0b5] - 2026-06-27

### Added

- Order deletion functionality for owners and directors (restricted to REQUESTED or QUOTED statuses).
- Replaced native browser confirmation popups with Bootstrap 5 modals for order deletion to match Alliance Auth styling.
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
