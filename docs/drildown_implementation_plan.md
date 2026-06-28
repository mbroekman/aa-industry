# Goal: Multi-level BOM (Bill of Materials) Drill-down

Currently, the `industry_reforged` plugin calculates a "Level 1" Bill of Materials. If a user orders a Tech 2 ship, the system calculates the immediate components required (e.g., the Tech 1 hull and the Tech 2 intermediate components).

The goal of this new feature is to provide a **Recursive BOM Drill-down**. This means breaking down those intermediate components into *their* components, all the way down to base "Raw Materials" (Minerals, Planetary Interaction materials, Moon Goo, etc.).

## 1. Backend (`industry_reforged/utils/bom_engine.py`)

We will introduce a recursive engine that traverses the production chain.

- **`get_recursive_bom_tree(type_id, quantity, corp_me)`**:
  A recursive function that queries Fuzzwork for a `type_id`. If Fuzzwork returns materials, it checks each material to see if it *also* has a blueprint. It builds a hierarchical JSON/dict tree structure representing the full manufacturing chain.
- **`get_flat_raw_materials(type_id, quantity, corp_me)`**:
  A function that uses the tree above but flattens it, giving the director/industrialist a single, aggregated "Shopping List" of purely raw materials needed to build the entire order from scratch.
- **Base Material Detection**:
  To prevent infinite loops and unnecessary API calls, we will identify raw materials. If Fuzzwork returns an empty manufacturing array, we know we've hit a base material.

### Caching Strategy (No Quality Loss)

To keep the plugin lightning-fast without sacrificing accuracy:

- The Fuzzwork API responses for Blueprints will be cached in the Django cache for 30 days. EVE Online blueprint base materials are static and only change during major CCP expansions. By caching the exact response from Fuzzwork, we guarantee 100% accuracy while eliminating the 500ms network delay for every single intermediate component.

## 2. Frontend (Views & Templates)

We need to visualize this drill-down for the Builders (Industrialists) and Directors.

#### Permissions & Access Control

- The drill-down view will be protected and **only** visible to users who have the `industry_reforged.industrialist_access` (or `corp_access`) permission. Basic users will only see the top-level quote, keeping their interface simple.

#### [MODIFY] `industry_reforged/templates/industry_reforged/view_quote.html`

- **New Tab: "Full Production Tree"**: We will add a tab alongside the current BOM that displays the hierarchical tree, wrapped in a permission check `{% if perms.industry_reforged.industrialist_access %}`.
- **Interactive Accordions**: We will use Bootstrap 5 accordions or a nested list with collapse toggles (`data-bs-toggle="collapse"`) so the builder can expand a component (e.g., "Capital Armor Plate") to see its underlying minerals.

#### [NEW] `industry_reforged/templates/industry_reforged/partials/bom_tree_node.html`

- We will create a recursive Django template snippet. This snippet will render a material row, and if that material has `sub_materials`, it will recursively `{% include %}` itself to render the children.

## 3. Verification Plan

### Automated Tests

- Mock the Fuzzwork API responses for a known Tech 2 item (e.g., Paladin) and verify that the `get_recursive_bom_tree` correctly identifies the T1 hull and the T2 components, and then breaks the T2 components down into Moon Materials.

### Manual Verification

1. Create a request for a complex item (e.g., a Tech 2 module).
1. Log in as a user with `basic_access` and verify the drilldown tab is **hidden**.
1. Log in as a user with `industrialist_access` (or Director).
1. Open the Order Details -> View Quote.
1. Verify that the "Full Production Tree" tab is visible.
1. Click through the nested tree to ensure intermediate components expand correctly into raw minerals and PI.
