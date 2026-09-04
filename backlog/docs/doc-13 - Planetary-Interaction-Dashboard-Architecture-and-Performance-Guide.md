---
id: doc-13
title: Planetary Interaction & Dashboard Architecture and Performance Guide
type: guide
created_date: '2026-09-04 11:05'
---

# Planetary Interaction (PI) & Dashboard Architecture Guide

This document outlines the architecture, data structures, caching mechanics, and user interface features of the Planetary Interaction (PI) module and dashboard auto-refresh system in **Alliance Auth Industry Reforged**.

______________________________________________________________________

## 1. Planetary Interaction (PI) Architecture

### Data Models

- **`CharacterPlanet`**:
  Represents a planet managed by a character via EVE ESI.
  - Links to `EveCharacter`, `EvePlanet`, `EveSolarSystem`, `EveType` (planet type).
  - Tracks synchronization metadata: `last_update`, `factory_baseline_time`.
- **`PlanetPin`**:
  Represents an individual structure/pin placed on the planet surface.
  - **Extractors**: `install_time`, `expiry_time`, `cycle_time`, `extraction_yield`, `product_type`.
  - **Factories**: `schematic_id`, `last_cycle_start` (supports Basic, Advanced, and High-Tech factories).
  - **Storage**: `contents_volume`, `capacity`, `contents` JSON field (Launchpads, Storage Facilities, Command Centers).
- **`PISchematic` / `PISchematicInput` / `PISchematicOutput`**:
  Represents the 68 standard EVE Online planetary production schematics.
- **`UserPIConfig`**:
  User-specific preferences, including `storage_warning_threshold` (default 75%) and `extraction_deficit_threshold_percent` (default 100%).

______________________________________________________________________

## 2. Dynamic Simulation & Calculations

### Production & Depletion Simulation

- **Hourly Consumption / Production Rates**:
  Calculated per planet based on installed factory pins and their active schematics.
- **Extraction Deficit & Supply/Demand Graph**:
  Compares hourly extraction rates against hourly consumption rates.
  - Generates `deficit_graph_data` displaying consumed resources, current supply, extraction percentage, and deficit amounts.
- **Factory Depletion Time (`factory_depletion_time`)**:
  Calculates when stored input resources on storage pins and launchpads will run out, excluding inputs that are continuously replenished by active extractors.
- **Dynamic Pin Contents (`categorized_contents`)**:
  Simulates live factory output and raw resource consumption between ESI sync intervals so storage pins reflect estimated produced items and remaining inputs.

______________________________________________________________________

## 3. Schematics Auto-Bootstrapping (TASK-119)

To ensure seamless installation and migration without requiring manual CLI data imports, schematic data is automatically populated from SDE mirrors:

- **Data Sources**: `https://sde.zzeve.com/planetSchematics.json` & `planetSchematicsTypeMap.json`.
- **Automatic Triggers**:
  1. **ESI Background Sync (`update_character_pi`)**: Checks `if not PISchematic.objects.exists()` before processing character planets.
  1. **Manual Sync Trigger (`trigger_pi_sync`)**: Spawns `update_pi_schematics_from_sde.delay()` if the table is empty.
  1. **Dashboard Load (`personal_dashboard`)**: Verifies schematic presence and queues a background update if missing.

______________________________________________________________________

## 4. In-Memory Schematics Caching & Query Optimization (TASK-121)

### The N+1 Query Problem & Solution

- **Problem**: Previously, evaluating pins across multiple planets performed hundreds of separate database queries to `PISchematic`, `PISchematicInput`, `PISchematicOutput`, and `EveType`. This caused database connection spikes and `(1040, 'Too many connections')` errors during concurrent requests or auto-refresh cycles.
- **In-Memory Cache (`get_all_schematics_dict`)**:
  - Pre-caches all 68 schematics and their inputs/outputs in a memory dictionary in Python process memory.
  - Automatically invalidates via `clear_schematics_cache()` on `PISchematic.save()`, `PISchematic.delete()`, or SDE sync.
  - Zero SQL queries needed per factory pin during dashboard rendering.
- **Bulk `EveType` Lookups**:
  - Resource type names in `deficit_graph_data` are resolved in a single batch query (`EveType.objects.filter(id__in=active_type_ids)`).
- **Result**: Reduced SQL queries per dashboard load from >1,000 to \<5 queries.

______________________________________________________________________

## 5. Dashboard Auto-Refresh & Tab State Persistence (TASK-120)

### Configurable Auto-Refresh Control

- **Available Intervals**: `Off`, `5 minutes`, `10 minutes`, `15 minutes`, `25 minutes`, and `30 minutes`.
- **Integrated Pages**:
  - **Personal Dashboard** (`/industry/personal/`)
  - **Corporate Dashboard** (`/industry/corporate/`)
  - **Industrialist Dashboard** (`/industry/industrialist/`)
- **Key Capabilities**:
  1. **LocalStorage Persistence**: Stores the selected interval per URL path so refresh intervals persist across page loads.
  1. **Live Countdown Badge**: Displays remaining time with visual cues (`btn-outline-info` when off, `btn-success` with live countdown when active).
  1. **Global Tab State Persistence**:
     - Listens to Bootstrap `shown.bs.tab` events and records active tab panes in `sessionStorage` and browser URL hash history (`history.replaceState`).
     - Automatically restores the active tab (*Manufacturing*, *Research*, *Planetary Interaction*, *History*, *Build Steps*, etc.) after a page refresh.
  1. **PI Character/Planet View Persistence**:
     - Remembers which character's planets are currently open in the PI dashboard.
  1. **Modal Pause Logic**:
     - Automatically suspends countdown execution when a Bootstrap modal (`.modal.show`) or dialog is open, preventing disruption during user editing.
