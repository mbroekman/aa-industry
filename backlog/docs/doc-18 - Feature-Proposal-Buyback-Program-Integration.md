---
id: doc-18
title: 'Feature Proposal: Buyback Program Integration'
type: specification
created_date: '2026-10-13 08:19'
updated_date: '2026-10-13 08:19'
---

# Feature Proposal: Buyback Program Integration

**Date:** October 13, 2026
**Type:** Code Review + Integration Proposal
**Status:** Proposed
**Source analyzed:** `C:\Users\mbroe\Downloads\allianceauth-buyback-program-master` (third-party plugin, app label `buybackprogram`, no git history included in the download)

## 1. Executive Summary

The downloaded project is a mature, feature-rich Alliance Auth plugin that lets a corp/alliance buy items from members (and, in its newer "reverse" mode, sell hangar stock to members) via in-game item-exchange contracts, with automatic ESI contract matching, a pricing/tax engine, abuse detection, and Discord notifications.

It is **not drop-in mergeable** — its dependency surface (`django-eveuniverse`, `django-esi`) is compatible with `aa-industry`, and its menu/permission pattern is trivial to copy, but its own `Owner` model carries ~2000 lines of ESI logic, and its pricing engine (`helpers.py`) is the most duplicated and least-tested part of the codebase. Recommendation: **port the concept, not the code** — rebuild the feature as a new `aa-industry` sub-module (`models/buyback.py`, `views/buyback.py`, `tasks/buyback.py`) that reuses `aa-industry`'s existing `IndustryFacility`, `KnownLocation`, `LedgerTransaction`, and `TaxConfig`/pricing infrastructure, rather than importing the third-party app's models wholesale.

Two items need resolving **before** any work starts on this:

1. The source repo ships a committed `alliance_auth.sqlite3` (~1.8 MB) at its root, not covered by `.gitignore`. Contents weren't inspected (untrusted file). **Do not import/run this file.** If the upstream repo's own git history is ever cloned, check it for leaked credentials before trusting it.
2. `aa-industry` already has an undeclared, referenced-but-never-defined `director_access` permission bug (see §4.1) that any new admin-tier permission decision should avoid repeating.

## 2. What the Source Project Does

- **Normal buyback**: member pastes an in-game inventory list into a calculator, gets an instant appraisal + tracking number, creates an item-exchange contract; a Celery task polls ESI contracts every 30 min, matches by tracking number in the title, and flags mismatches (wrong item, wrong price, wrong structure, wrong receiver, title tampering, scam/no-tracking contracts).
- **Reverse buyback** (newer, large feature): corp syncs hangar stock from ESI, members browse available stock + price and submit a buy request; same contract-matching/notification machinery mirrored for the other direction, with live stock reservation and TTL-based auto-purge of abandoned requests.
- **Pricing engine**: raw/compressed/refined ore pricing (best-of), static per-item prices, NPC buy prices for loot/bonds, T1/meta scrap-value reprocessing valuation, hauling fuel cost, a "price density" tax for bulky low-value items, per-item/per-market-group tax overrides, and a manual-review watchlist. Prices sourced from Fuzzwork or Janice APIs.
- **Discord notifications** for new/accepted/rejected contracts (via `aadiscordbot` or `discordproxy`).
- **Stats/leaderboards** and a monthly performance dashboard.
- Supports **public (unauthenticated) access** per-program, alongside normal state/group restriction.
- Entirely **frontend-configurable** (managers create/edit programs, pricing, watchlists through in-app forms) — Django admin is a secondary/debug surface only, which is a good sign for this workspace's admin-vs-frontend standard (ADR-006).

## 3. Code Quality & Improvement Recommendations (on the source project itself)

These apply regardless of whether the feature is ported or kept standalone — useful as a checklist either for improving the upstream project or for what to deliberately *not* carry forward into the port.

### 3.1 Architecture

- **`Owner` model is a god object** (`models.py`, ~2000 of 2900 lines): ESI fetch/parse logic for contracts, wallets, hangar divisions, hangar assets, container sync, and structure-name resolution all live as methods on one class, and it imports `notification.py` directly (model layer importing presentation/integration code — a layering inversion). A service/manager layer split by concern (contracts, wallets, hangars) would be far more testable.
- **Pricing logic in `helpers.py` is deeply duplicated**: `get_item_values` repeats the same ~25-line raw/refined/compressed/NPC pattern four times with copy-pasted variable names instead of one parameterized helper. This has already produced at least one real inconsistency (the NPC-price density calc divides by `item_type.volume` while the other three variants divide by `packaged_volume`, apparently unintentionally).
- Comments like `"# CRITICAL FIX:"` and `"# FIX: Added math.floor()..."` left in production code, plus 50+ pervasive typos baked into DB field names (`price_dencity_modifier` for "density") that can no longer be fixed without a breaking migration — signs of repeated firefighting rather than refactoring.
- A plain `raise f"Unknown pricing method: ..."` (`helpers.py:156`) is invalid Python — raising a string is not valid exception semantics and **will throw `TypeError` at runtime** if that branch is ever hit. This is a live latent bug.
- `max([raw_item["value"], refined["value"], compressed["value"]])` relies on `False == 0` Python coercion (unused values default to `False`, not `0`) — fragile, would silently break if someone "cleaned up" a default to `None`.
- A double-stacked `@fetch_token_for_owner(...)` decorator on `update_wallets_esi` with two different scope lists looks like dead/leftover code (the inner one is effectively shadowed).
- `program_add` makes a **synchronous ESI call inline in a GET/POST view** to "smart-sync wallets before loading the form" — a request-blocking ESI round trip on page load, guarded only by a generic `except Exception`.
- `program_calculate`'s inventory-paste parser (hand-rolled tab-delimited parsing, stripping `*`, filtering digits out of localized quantity strings) lives directly in the view instead of a parser/form layer, and has **no direct unit tests** — it's the single highest-risk piece of user-facing logic in the app (any EVE client locale/format change could silently break pasting).
- The app maintains **two parallel price caches** — its own `ItemPrices` table and `eveuniverse`'s native `EveMarketPrice` (which it also writes to) — for no documented reason.

### 3.2 Testing gaps

Reasonably strong model tests and a genuinely thorough reverse-buyback notification test suite (474 lines covering price/item/location/receiver/title/donation/public-submission cases individually) — but:

- **Zero tests for the pricing engine** (`get_item_prices`, `get_item_values`, reprocessing valuation) — the most complex, most duplicated, and bug-history-laden code has no coverage at all.
- Zero tests for `views/special_taxes.py` (program item/market-group/watchlist CRUD).
- Zero tests for `views/stats.py` beyond smoke checks.
- Zero tests for the **original/normal**-program contract-notification matrix (only the newer reverse-buyback path is tested).
- Zero tests for `notification.py` (Discord dispatch) or price-fetching (`get_bulk_prices`, Fuzzwork/Janice HTTP calls — no mocked HTTP at all).

### 3.3 Operational risks

- A documented, unfixed production foot-gun: `QueueOnce`-locked Celery tasks can leave a stale lock in cache for up to 2 hours (`BUYBACKPROGRAM_TASKS_TIME_LIMIT`) if a worker restarts mid-task, silently skipping all contract syncs until the lock expires — mitigated only by a manual `redis-cli` flush documented in the README, not fixed in code.
- Heavy reliance on `except Exception: logger.error(...)` with no re-raise and no task-failure signal — a sync can silently fail with no way for a manager to notice short of reading server logs.
- ESI "not modified" detection via string-matching (`"304" in str(e)`) instead of a typed exception check, in ~8 places — fragile if the ESI client's error message format ever changes.
- `update_program_performance` has a classic N+1 (a `TrackingItem` query per `Tracking` inside a loop, with ad-hoc wall-clock logging already added by the original author — a sign they'd already noticed it was slow).

### 3.4 Historical data-integrity scar

Migration `0011_delete_duplicated_contracts.py` is a data-cleanup migration (de-duplicating `Contract` rows with 4 different "which duplicate to keep" heuristics and a hard `exit(1)` safety valve) followed immediately by `0012_make_contract_id_unique.py`, which adds the unique constraint that should have existed from the start. This confirms a real historical production bug — `contract_id` was unconstrained for 10 migrations, almost certainly from a race between overlapping Celery task runs before `QueueOnce` locking existed.

## 4. Integration Plan: Buyback as an `aa-industry` Menu Item

`aa-industry` (`industry_reforged`) is **well-suited to absorb this as a sub-feature** rather than running it as a separate installed app: it already depends on `django-eveuniverse`/`django-esi` at the project level, already has a `tasks/<feature>.py` + `views/<feature>.py` + `models/<feature>.py` per-module convention, and already follows the admin-vs-frontend split this feature needs. Concretely:

### 4.1 Menu item & permissions

`industry_reforged/auth_hooks.py` registers one `MenuItemHook` subclass per sidebar entry (7 today), each with a `render()` override gating on `request.user.has_perm(...)`. The new entry follows the exact same pattern:

```python
class BuybackMenuItem(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Buyback Program"),
            "fas fa-hand-holding-usd fa-fw",
            "industry_reforged:buyback_dashboard",
            navactive=["industry_reforged:buyback_dashboard"],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_buyback_menu():
    return BuybackMenuItem()
```

**This directly answers the "available to members" requirement**: gating on the already-existing `industry_reforged.basic_access` permission (the same one "Personal Industry" and "Member Orders" already use) makes it visible to every regular member immediately, with zero new permission plumbing needed for read/submit access.

For the manager/admin tier (creating buyback programs, editing pricing, reviewing flagged contracts), reuse the existing `industry_reforged.corp_access` permission — that's the de facto "director/admin" permission already used by every other director-config view in this app (`director_config`, `director_config_pricing_edit`, etc.). **Do not reference `director_access`** — it's cited in `auth_hooks.py`, one view, and five test files, but was never declared in `models/core.py`'s `Meta.permissions`, so `Permission.objects.filter(codename="director_access")` silently returns nothing today. This is a pre-existing bug in `aa-industry`, not something to replicate.

No new `UrlHook`/namespace is needed — a `"buyback/..."` prefix added to the existing `urlpatterns` in `urls.py` resolves at `/industry/buyback/...` under the existing `industry_reforged` namespace, exactly like `"orders/..."` and `"director/..."` already do.

### 4.2 What to reuse instead of porting

| Buyback plugin's own model/concept | Reuse this `aa-industry` model instead |
|---|---|
| `Location` (custom structure/system cache) | `IndustryFacility` for configured drop-off structures; `KnownLocation` for ad-hoc contract locations outside configured facilities — `KnownLocation` is explicitly built for exactly this ("locations outside of configured IndustryFacilities") |
| Payout/payment tracking inside `Tracking`/`Contract` | `LedgerTransaction` — already the cross-feature money-movement ledger (`INCOME`/`PAYOUT`/`PROCUREMENT` types, FK'd to `MemberOrder` and `BuilderPayoutBatch`); extend `TRANSACTION_TYPES` with `BUYBACK_PAYOUT` and add a nullable FK rather than building a parallel ledger |
| `Program`'s tax/fee fields | `TaxConfig` (`industry_tax_rate`/`broker_fee_rate` pattern) as the template for where buyback-specific tax/price-modifier config should live |
| Own `ItemPrices` cache + Fuzzwork/Janice integration | Evaluate reusing `utils/pricing_engine.py` (already backs the Member Order pricing flow) before porting a second, parallel pricing engine — the source project itself never reconciled its own two price caches (`ItemPrices` vs `eveuniverse.EveMarketPrice`); don't import that problem along with the feature |
| `Owner.update_contracts_esi()` / `update_wallets_esi()` custom ESI calls | Follow `tasks/jobs.py`'s existing convention: `Token.objects.filter(scopes__name=...)` + `esi.client.<Group>.<Operation>(...)` directly, no abstraction layer — `aa-industry` has no ESI *Contracts* endpoint usage yet, so this is genuinely new surface area, but should be added task-by-task the same way `tasks/jobs.py` and `tasks/wallets.py` already do it |
| Admin-registered config | Keep config in a frontend `director_config`-style form (`forms.py` + a `director_config_buyback_edit` view, same `corp_access` gate), matching how `CorpPricingConfig`/`TaxConfig` are already edited — not in `admin.py` |

### 4.3 What's genuinely new work

- ESI Contracts endpoint polling (`GET /corporations/{corporation_id}/contracts/` + items) — no existing `aa-industry` task does this today.
- The contract-matching/abuse-detection logic (item/price/structure/receiver/title mismatch detection) — this is the single most valuable, well-tested part of the source project (the reverse-buyback notification matrix has 474 lines of dedicated tests) and is worth porting largely as-is, translated onto `aa-industry`'s models.
- The inventory-paste calculator UI and its parser — flagged above as untested and fragile in the source; this is a good opportunity to add proper tests and a dedicated parser function (not a fat view) during the port rather than carrying the risk forward.
- Discord notification wiring — check whether `aa-industry` already has a Discord integration convention (`utils/discord.py` exists per the structure scan) to hook into, rather than importing the source project's own `notification.py` branching logic wholesale.

### 4.4 Suggested module layout (matching existing `aa-industry` conventions)

```
industry_reforged/
  models/buyback.py      # Program, Contract, Tracking, ContractNotification, WatchlistItem
  views/buyback.py        # member calculator + program browsing (or views/buyback/ if it grows, matching views/orders/)
  tasks/buyback.py        # ESI contract polling, price refresh, notification dispatch
  templates/industry_reforged/buyback/*.html   # extends industry_reforged/base.html
```

### 4.5 Permissions to declare

Add to `models/core.py`'s `General.Meta.permissions` (alongside the existing 3):

```python
("buyback_access", "Can access and submit buyback contracts"),  # or just reuse basic_access
```

Given every other member-facing feature in this app gates on plain `basic_access`, the simplest and most consistent choice is to **not** add a new permission at all for member access — reuse `basic_access` — and only reuse `corp_access` for the manager/config tier. A dedicated `buyback_access` permission would only be worth adding if the user wants buyback availability to be independently toggleable per member group, separate from the rest of the app's member features.

## 5. Risks & Effort

- **Medium-high effort**: this is not a copy-paste integration. The pricing engine and `Owner` model both need real rework, not just a namespace change, to fit `aa-industry`'s existing patterns.
- **Low schema risk**: no conflicting models — `aa-industry` has no `Program`/`Contract`/`Tracking` equivalents today, so new tables are purely additive.
- **Shared-dependency tailwind**: `django-eveuniverse` and `django-esi` are already present; no new third-party dependencies needed beyond optionally Fuzzwork/Janice HTTP calls for pricing (or skip those and reuse `utils/pricing_engine.py`/`eveuniverse.EveMarketPrice` instead).
- **Test debt inherited if ported as-is**: the pricing engine, stats views, and normal (non-reverse) contract-notification path have no tests in the source project. Budget time to add tests during the port rather than carrying the gap forward, especially since this feature moves real ISK and the source project's own migration history (§3.4) shows what happens when contract matching has a data-integrity bug.

## 6. Recommendation

1. Do **not** import the third-party app wholesale or install it alongside `aa-industry` as a second app — fold it in as `industry_reforged/{models,views,tasks}/buyback.py`, following the established per-feature-module convention.
2. Gate member access on the existing `industry_reforged.basic_access` permission; gate program/pricing management on the existing `industry_reforged.corp_access` permission — no new permissions required.
3. Reuse `IndustryFacility`/`KnownLocation` for locations, `LedgerTransaction` for payouts, and evaluate reusing `utils/pricing_engine.py` before porting a second pricing engine.
4. Port the contract-matching/abuse-detection logic largely as-is (it's the best-tested, most valuable part of the source project) — translated onto `aa-industry`'s ESI-calling conventions (`tasks/jobs.py` pattern) rather than the source's `Owner`-model-centric approach.
5. Rewrite rather than port: the inventory-paste parser (add real tests), the pricing engine (de-duplicate the 4x-repeated valuation logic), and the double price-cache (pick one).
6. Flag the committed `alliance_auth.sqlite3` to whoever maintains the upstream repo if this is ever contributed back or re-downloaded from a live clone — don't let it enter this workspace's git history.
