---
title: Investigation Report - DataTables Pagination Visibility
date: '2026-08-11'
author: Agent
---

# Investigation Report: DataTables Pagination ("Items per page")

## Problem Statement

The "items per page" (Show X entries) dropdown was missing on the initial load of the "Claimed Jobs" page (and other dashboard tables), but appeared unexpectedly after navigating to a subsequent page or interacting with the table.

## Root Cause Analysis

During the investigation of the frontend and template logic, the following was discovered:

1. On the **Industrialist Dashboard** (which includes the Claimed Jobs table), as well as the **Director Dashboard** and **Director Wallets**, there was specific JavaScript/CSS logic that forcefully hid the length menu (`dataTables_length`) during the initial load. This was likely originally done to keep the layout "cleaner".
1. However, the global `base.html` contains standard DataTables initialization and event handling. This global logic includes a check that automatically displays the length menu if the total number of records exceeds 10.
1. Because the forced hide only applied on the initial page load, any subsequent redraw of the DataTable (such as clicking to the next page, or searching) triggered the global logic in `base.html`, which then made the dropdown visible again. This resulted in the inconsistent UI behavior.

## Solution Implemented

To resolve this inconsistency, the code that forcefully hid the dropdown on initial load was removed.

**Result**:

- The "items per page" selection is now consistently visible right from the initial page load, provided the table contains more than 10 items (which matches the default DataTable behavior configured in the project).
- This applies to the Industrialist Dashboard, Director Dashboard, and Director Wallets.

## Related

- Fix applied in version `0.3.4` (see `CHANGELOG.md`).
