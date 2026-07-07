# Implementation Plan: Automated ME/TE Calculation via Structure Rigs

Currently, the Material Efficiency (ME) and Time Efficiency (TE) per item must be manually configured by a Director in the Admin panel. The goal is to automate this by reading the actual installation (Upwell Structure) and its installed Rigs.

## Challenge: ESI Restrictions

The EVE Swagger Interface (ESI) does **not** provide public information regarding which Rigs are installed in a structure. We can only fetch this data via the API if:

1. The structure is owned by the corporation itself.
1. We use the `esi-assets.read_corporation_assets.v1` scope to search through corporate assets.

If the corporation builds in an allied or public structure, it is **technically impossible** to read the rigs automatically via the API.

## Proposed Solution (Approved)

To robustly solve this, we will build a hybrid system supporting both corporate and external structures.

### 1. Structure Management Interface

We will add a new page for Directors: **"Production Facilities"**.
Here, Directors can manage the structures where the corporation builds items.

- **Corporate Structures:** Can be synchronized with a single click. A background task will search Corporate Assets for the structure, read the Rigs (via `RigSlot0`, `RigSlot1`, etc.), and save the bonuses.
- **External Structures (Manual Fallback):** Directors can manually add an external structure. They will select the hull type (e.g., *Sotiyo* or *Azbel*), the location (Highsec, Lowsec, Nullsec/W-space for the rig multiplier), and manually select the installed Rigs from a dropdown.

### 2. Quoting Flow Updates (Director View)

When a Director is generating a quote, we will add a new dropdown: **"Target Production Facility"**.

- The member placing the order will *not* see this choice.
- The page will use HTMX/JavaScript: when the Director selects a different structure from the dropdown, the ME and the raw cost price will be **recalculated live** and updated on the screen.
- To prevent confusion during the recalculation, a small **loading overlay** will be shown while the server processes the new pricing.

### 3. BOM Engine Update (`bom_engine.py`)

The `calculate_order_bom` function will be expanded to accept the selected *Target Facility* as an optional parameter. The system will apply the official EVE Online mathematics:

1. Base ME of the item.
1. **Structure Hull Bonus** (e.g., Engineering Complexes provide a base bonus).
1. Applicable **Rigs** in the selected facility for the specific item category (e.g., T2 Ship Manufacturing Rig).
1. **Security Space Multiplier** (Nullsec/W-space gives a 2.1x multiplier on the rig bonus, Lowsec 1.9x).

The calculation will check these values and apply the complex ME Formula:
`Base * (1 - HullBonus) * (1 - (RigBonus * SecMultiplier))`

### 4. Visibility & Storage

When the quote is sent to the member, the selected Target Facility is stored in the database (linked to the Order or Task).
On the BOM overviews and in the Quote view for the Director, it will explicitly state: *"Cost price calculated based on: [Structure Name] (x% ME Bonus)"*.
