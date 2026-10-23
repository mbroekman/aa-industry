# Architecture Overview — aa-industry (`industry_reforged`)

> **Status:** Current as of 2026-10-23, app version 0.15.7 (pending release - TASK-260/261/262 shipped on `main`, not yet tagged).
> **Scope:** Whole-plugin architectural reference. For deep dives on specific subsystems, see the cross-references at the end of each section and the index in §9.

## 1. What this plugin is

`industry_reforged` ("Industry Reforged") is an Alliance Auth plugin that runs a corp/alliance's entire manufacturing economy inside AA: personal and corporate ESI industry-job tracking, a member "buy from the corp" ordering system with quoting and builder payouts, a claimable Job Market for industrialists, Planetary Interaction tracking, a corp Blueprint Library, a Buyback Program (members sell items *to* the corp), an AI Market Manager that restocks/arbitrages automatically, and a Director Control Panel that ties it all together with wallet/ledger reconciliation.

It registers with Alliance Auth as a single Django app (`IndustryConfig`, `apps.py`), mounted under `/industry/` via one `UrlHook`, with **9 menu items** gated by permission (`auth_hooks.py`). All ESI access goes through one shared client (`tasks/utils.py`'s `IndustryESIProvider`), and nearly all state-changing logic is reachable from the frontend — Django admin is reserved for technical/debug views only (workspace-wide **ADR-006**, see §8).

## 2. App integration

- **AppConfig**: `IndustryConfig` — `name="industry_reforged"`, `label="industry_reforged"`. On `ready()`, connects a `post_migrate` signal that auto-queues 6 bootstrap Celery tasks on a *fresh install only* (detected via an empty `TaskExecutionLog` table), so the System Health tab isn't empty on day one.
- **Menu items** (`auth_hooks.py`, all `MenuItemHook`, gate shown in parens):
  1. Personal Industry (`basic_access`) → personal dashboard
  2. Corporate Industry (`corp_access`) → corporate dashboard
  3. Member Orders (`basic_access`) → orders dashboard
  4. Buyback Program (`basic_access`) → buyback dashboard
  5. Industrialist Dash (`industrialist_access`) → claimable Job Market
  6. Director CP (`corp_access`) → Director Control Panel; also injects a floating "System Error!" alert if any `TaskExecutionLog` row has `status=FAILED`
  7. Industry Leaderboard (`basic_access`)
  8. Corp Blueprint Library (`basic_access`)
  9. AI Market Manager (`director_access` **OR** `corp_access` — see known issue in §8)
- **URL hook**: everything lives under `r"^industry/"`.
- **Required ESI scopes** (8): character/corp industry jobs, PI planets manage, corp assets read, universe structures read, corp structures read, corp wallets read, corp contracts read.
- **Optional integration**: a separate FastAPI/LightGBM "AI Forecasting" microservice (`ai-forecasting/`, deployed as its own container) that the AI Market Manager calls for demand forecasts, with a graceful fallback to static 30-day historical averages if unreachable.

## 3. Data model

Models live under `industry_reforged/models/`, one file per subsystem, all re-exported through `models/__init__.py`. Grouped by concern:

| Area | File | Key models |
|---|---|---|
| Core/permissions | `core.py` | `General` (permission holder, no table), `TaskExecutionLog` (System Health backing store) |
| Facilities | `facilities.py` | `IndustryFacility`, `IndustryRig`, `IndustryFacilityRig`, `KnownLocation` |
| ESI jobs | `jobs.py` | `CharacterIndustryJob`, `CorporationIndustryJob`, `TaskJobLink` |
| Blueprints | `blueprints.py` | `CorpBlueprint`, `BlueprintRequest` |
| Member orders & production | `orders.py` | `CorpPricingConfig`, `CorpTypeDiscount`, `OutputLocation`, `MemberOrder`, `OrderItem`, `OrderFit`, `BuilderPayoutBatch`, `ProductionTask`, `CorpItemConfig`, `OrderBlueprintOverride`, `CorpBuyOrder` |
| Wallet/ledger | `wallet.py` | `WalletJournalSyncState`, `TaxConfig`, `CorpWalletDivision`, `CorpWalletJournal`, `LedgerTransaction` |
| Buyback | `buyback.py` | `BuybackProgram`, `BuybackWatchlistItem`, `BuybackContract`, `BuybackContractItem` |
| Director/corp config | `config.py` | `CorporationSyncConfig`, `CorporationWebhookConfig`, `CorpMOTD`, `CorporationPricingConfig`, `JobTrackingConfig` (overdue-alert grace/reminder buffer, TASK-262) |
| Inventory | `inventory.py` | `CorpInventory` |
| AI Market Manager | `ai_manager.py` | `Basket`, `BasketItem`, `AIMarketLog`, `MarketOpportunity`, `OpportunityScanner`, `OpportunityScannerLog`, `MissingBlueprintOpportunity` |
| Planetary Interaction | `pi.py` | `UserPIConfig`, `CharacterPlanet`, `PlanetPin`, `PISchematic` (+ Input/Output) |

### Central model: `ProductionTask`

The "Job Market" claimable unit. Carries `status` (UNCLAIMED → IN_PRODUCTION → COMPLETED), `priority`, and an `origin` tag (MANUAL / MEMBER_ORDER / BASKET / BOM / BLUEPRINT) recording which subsystem spawned it. A self-FK `bom_parent` lets a BOM explosion build a tree of sub-tasks. `gamification_value`/`builder_reward` drive payout; `payout_batch` links to `BuilderPayoutBatch` once settled. `assigned_at`/`estimated_duration_seconds` (pre-existing) plus `last_overdue_notified_at` (TASK-262) drive the ETA/overdue-alert system in `utils/eta_service.py` - see §6.

**Job Market visibility is a one-hop, per-row rule, not a tree-walk** (TASK-260/261): a task is directly claimable in the Job Market if `bom_parent is None`, OR `bom_parent.is_claimable == False` (the pre-existing static admin flag, `CorpItemConfig.is_unclaimable_parent`, baked in once at creation time in `quotes.py:accept_quote`), OR `bom_parent` is skill-ineligible for the viewing user (`utils/skill_service.py`, computed live, per-viewer). The third clause cascades to arbitrary depth for free, since a released child that's itself skill-gated passes the same test against its own children next render. `dt_director_tasks` (`views/datatables.py`) and `industrialist_dashboard` (`views/industrialist.py`) both implement this rule independently against the same `skill_service`/`eta_service` helpers.

### Central model: `MemberOrder`

The member-facing "buy from the corp" workflow: `REQUESTED → QUOTED → ACCEPTED → IN_PRODUCTION → READY → DELIVERED` (or `REJECTED`). Supports order splitting via a self-FK `parent_order` (status propagates between parent/children in `save()`), PLEX-denominated upfront payments (`remaining_balance` resolves live PLEX market price), and per-order ME/runs overrides via `OrderBlueprintOverride`.

### Central model: `LedgerTransaction`

The unified internal ledger shown on the Director Dashboard. One `transaction_type` enum (`INCOME` / `PAYOUT` / `PROCUREMENT` / `BUYBACK_PAYOUT`) with nullable FKs out to whichever source record it corresponds to (`member_order`, `payout_batch`, `buyback_contract`) — the single place that correlates real wallet activity to internal events, regardless of which subsystem generated it.

### Buyback subsystem (newest feature)

`BuybackProgram` (director-configured drop-off + pricing modifiers) → member submits inventory → `BuybackContract` (tracking number `BB-XXXXXXXX`, 6 independent boolean mismatch flags for item/price/structure/receiver/title/no-tracking, so abuse is diagnosable rather than one opaque status) → `BuybackContractItem` lines, each carrying both the final `unit_price` and the pre-modifier `base_unit_price` for an auditable appraisal breakdown. See `doc-18` for the full design rationale (built by porting the *concept* of a third-party plugin, not its code, specifically to fix known pricing-duplication and unconstrained-contract-ID bugs in the source project).

## 4. URL & view layer

`urls.py` is a single flat `urlpatterns` list (`app_name="industry_reforged"`, no `include()` sub-namespacing) importing view modules `ai_manager, api, blueprints, buyback, dashboard, datatables, director, facilities, industrialist, orders`.

| Path prefix | View module(s) | Audience |
|---|---|---|
| `/`, `personal/`, `corporate/`, `orders/` | `dashboard.py` | member/director landing pages |
| `ai-manager/...` | `ai_manager.py` | director (Basket/Scanner CRUD, run triggers, audit log) |
| `add-*-token/`, `*/sync*` | `api.py` | mixed — AJAX token callbacks + manual sync triggers |
| `orders/create`, `orders/<id>/...` | `views/orders/` package (`create`, `quotes`, `shopping`, `splitting`, `management`, `notifications`) | member (create/view/accept/reject) + director (provide quote) |
| `industrialist/...` | `industrialist.py` | industrialist (claim/unclaim/complete) + member (leaderboard) |
| `director/...` | `director.py` (**largest view module, ~1200 lines**) | director — orders/tasks/buy-orders, payout batches, inventory, full config suite, wallets |
| `director/api/...`, `*/api/...` | `datatables.py` (~900 lines) | director-facing server-side DataTables JSON sources |
| `director/facilities/...` | `facilities.py` | director |
| `blueprints/...`, `director/blueprints/requests/...` | `blueprints.py` | member (browse/request) + director (resolve requests) |
| `buyback/...`, `director/buyback/...` | `views/buyback/` package (`member`, `director`, `stats`) | member (calculator, dashboard, contract detail) + director (program config, review queue) |

Design pattern worth naming: feature areas with clearly separable member vs. director concerns (`orders`, `buyback`) get their own sub-package with one file per audience; smaller/single-audience areas (`facilities`, `blueprints`, `industrialist`) stay as one flat module.

## 5. Celery task layer

All ESI access funnels through one shared client in `tasks/utils.py`:

- **`IndustryESIProvider`** (singleton `esi`) — declares every ESI operation the app uses up front; every task module imports this one object rather than building its own client.
- **`log_task_execution(task_name)`** — decorator wrapping every scheduled task, writing start/success/failure/duration to `TaskExecutionLog` (feeds System Health + the Director-menu failure alert).
- **`resolve_unknown_locations(location_ids=None)`** — a *helper* task with a required parameter; deliberately **not** in `CELERYBEAT_SCHEDULE` per this plugin's own `AGENTS.md` convention (periodic tasks take no required args).

**Scheduled tasks** (`README.md`'s `CELERYBEAT_SCHEDULE`, 16 entries — the authoritative list; any new periodic task must be added here in the same commit):

| Task | Schedule | File |
|---|---|---|
| `update_character_jobs` | `*/30` min | `tasks/jobs.py` |
| `update_corporation_jobs` | `*/30` min | `tasks/jobs.py` |
| `link_orphaned_jobs_to_tasks` | `*/30` min | `tasks/jobs.py` |
| `update_character_pi` | hourly (`:00`) | `tasks/pi.py` |
| `task_notify_expired_extractors` | `:15,:45` | `tasks/pi.py` |
| `task_sync_corp_inventory` | `*/15` min | `tasks/inventory.py` |
| `task_sync_corp_blueprints` | every 2h | `tasks/blueprints.py` |
| `task_pull_market_data` | 11:30 daily (pre-downtime) | `tasks/orders.py` |
| `task_sync_corp_wallets` | `*/30` min | `tasks/wallets.py` |
| `update_industry_facilities` | every 4h | `tasks/facilities.py` |
| `task_sync_all_rigs` | every 6h | `tasks/facilities.py` |
| `run_all_active_baskets` | hourly | `tasks/ai_manager.py` |
| `run_all_active_scanners` | hourly | `tasks/ai_manager.py` |
| `sync_market_data_to_ml_service` | every 12h | `tasks/ai_manager.py` |
| `buyback_poll_contracts` | `*/15` min | `tasks/buyback.py` |
| `buyback_purge_stale_contracts` | 12:30 daily | `tasks/buyback.py` |
| `check_overdue_production_tasks` | `*/30` min | `tasks/job_tracking.py` |

Note: `tasks/pi.py` also defines `update_pi_schematics_from_sde()`, which is **not** in the README's schedule table — likely intentionally manual (SDE-triggered), but worth confirming it isn't a forgotten-to-document periodic task next time `pi.py` is touched.

Per-file one-line summaries: `ai_manager.py` (basket/scanner evaluation + ML sync), `blueprints.py` (corp blueprint sync), `buyback.py` (contract polling/matching/expiry), `facilities.py` (facility names + rig detection), `inventory.py` (corp asset sync), `jobs.py` (ESI job sync + orphan reconciliation), `job_tracking.py` (overdue-claim detection + claimant/director notifications, TASK-262), `orders.py` (market pre-warm + BOM explosion), `pi.py` (PI sync + expiry notifications), `wallets.py` (wallet/journal sync + payment matching).

## 6. Business logic layer (`utils/`)

Pure logic deliberately kept out of views and tasks so it can be unit-tested without ESI/DB:

- **`pricing_engine.py`** (615 lines) — the core valuation engine: direct ESI market-order fetch with a 3-tier cache (1hr hit / 60s miss / periodic pre-warm), volume-weighted Jita-5%-sell percentile pricing, `EveMarketPrice` → Fuzzwork two-level fallback, manual `CorpItemConfig` overrides, corp/type discounts. **Authoritative reference: `doc-14`** (supersedes the pricing-source description in `doc-2`, which still predates the ESI-first migration — see §8).
- **`bom_engine.py`** (855 lines) — Bill-of-Materials explosion from SDE industry-activity data (`eveuniverse`), with a legacy fallback. Powers the recursive BOM-tree UI partial.
- **`ai_engine.py`** (241 lines) — market velocity/forecast support for the AI Market Manager's profitability gate.
- **`buyback_matching.py`** (158 lines) — pure, DB/ESI-free contract-matching and abuse-detection (tracking-number extraction, price-tolerance checks); `tasks/buyback.py` is kept as a thin fetch-and-write wrapper around it so the hard logic is independently testable.
- **`buyback_stats.py`** (241 lines) — per-program operational stats (flag/rejection/expiry rates, average turnaround, daily trend) beyond plain leaderboards.
- **`discord.py`** (26 lines) — the one shared `send_discord_webhook()` helper used by every feature's notification call-sites.
- **`skill_service.py`** (TASK-260) — live skill-gated job eligibility: resolves a blueprint's hard skill requirements via `django-eveuniverse`'s `EveIndustryActivitySkill` (EVE SDE, already populated - no new sync infra), compares against character skill levels fetched live via the same raw-ESI anti-304 pattern `slot_service.py` uses for slot counting (shared fetch, one ESI call per character serves both). `check_user_eligibility` scopes to characters in the same corp as the user's main (`get_user_industry_characters`); `check_character_eligibility` checks one specific character (the claim-time hard-stop).
- **`eta_service.py`** (TASK-262) — `get_task_eta()` prefers a claimed task's linked EVE industry job's real ESI `end_date` (via `TaskJobLink`) over the claim-time estimate (`assigned_at + estimated_duration_seconds`), returning `None` ("unknown") rather than guessing when neither is available. `is_overdue()`/`get_corp_buffer_hours()` apply the per-corp `JobTrackingConfig.completion_buffer_hours` grace/reminder interval.
- **`fit_parser.py`** / **`inventory_parser.py`** — EFT fit text and pasted inventory-list parsing respectively (order creation and buyback calculator).
- **`locations.py`** — hangar/location-flag display formatting.
- **`pi_schematics.py`** — large SDE-derived PI schematic reference dict.

## 7. Templates & frontend

`base.html` extends Alliance Auth's `base-bs5.html`. All interactive tables use AA's bundled **DataTables** (`bundles/datatables-css-bs5.html`) with server-side pagination sources in `views/datatables.py`; the Buyback Statistics page uses AA's bundled **Chart.js** for its daily-activity trend chart. Neither library is independently vendored — both ride on Alliance Auth's own bundles.

Structure: top-level pages per dashboard (`personal_dashboard.html`, `director_dashboard.html`, etc.), feature subdirectories `ai_manager/`, `blueprints/`, `buyback/`, and a `partials/` directory holding ~20 small DataTables cell-renderer fragments (`dt_isk.html`, `dt_order_status.html`, …) plus the recursive `bom_tree_node.html`.

## 8. Conventions, ADRs, and known issues

### Workspace-wide convention: ADR-006

Defined at the workspace root (`.agent/memory.md`), applied consistently here: **Django admin is for technical/debug config only; functional business configuration lives in the frontend** (director-facing forms). Confirmed in `admin.py`: only 9 models are registered, mostly read/debug views (synced jobs, inventory, audit logs) or genuinely technical config (sync character, webhook URLs). Nearly everything else — all of `buyback.py`, `config.py`, `wallet.py`, `pi.py` — is frontend-only by design.

### Known issues worth tracking

1. **Undeclared `director_access` permission.** Referenced in `auth_hooks.py` (AI Market Manager menu OR-clause) and `views/orders/notifications.py` (notification-recipient lookup), but never declared in `models/core.py`'s permission list (only `basic_access`, `corp_access`, `industrialist_access` exist). The AI Manager menu item only ever shows via its `corp_access` OR-clause in practice, and the "director" notification-recipient query silently matches nobody. Already flagged in `doc-18` §4.1; worth a small cleanup task (either declare the permission properly or remove the dead reference).
2. **`doc-2` is partially stale.** Its payout/discount logic (builder reward %, corp discounts) is still accurate, but its description of pricing as Fuzzwork-first predates the ESI-first migration (TASK-123). **`doc-14` is the current, authoritative pricing-architecture reference** — prefer it when answering "where do prices come from."
3. **README/code inconsistency on AI Market Manager Baskets.** The README's install instructions say "define Baskets in the Admin panel," but frontend `basket_edit`/`basket_create` views exist under `ai-manager/config/...`. The README text is stale; Basket CRUD is in fact available from the frontend, consistent with ADR-006 (admin registration remains for debug/bulk-edit convenience, not because frontend editing is unavailable).

## 9. Related documents

- `doc-2` — pricing/payout logic (payout half still accurate; pricing-source half superseded by doc-14)
- `doc-14` — **authoritative** direct-ESI market pricing architecture
- `doc-18` — Buyback Program integration proposal (design rationale, source-project anti-patterns avoided)
- `doc-13` — PI dashboard architecture
- `doc-15` — Opportunity Scanner (AI Market Manager)
- `doc-1` / `doc-5` — claimed-task ↔ ESI-job linking design (`TaskJobLink`)
- `doc-6` — original Transaction Ledger proposal (now implemented as `LedgerTransaction`)
