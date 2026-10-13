---
id: TASK-245
title: Fix 7 Starlette CVEs in ai-forecasting service via FastAPI bump
status: Done
assignee: []
created_date: '2026-10-13 13:45'
updated_date: '2026-10-13 13:47'
labels: []
dependencies: []
ordinal: 421000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ai-forecasting/pyproject.toml pins fastapi = "^0.110.0", which (per poetry's caret rules for 0.x versions) restricts installs to the 0.110.x line. FastAPI 0.110.x requires starlette<0.37.0,>=0.36.3 internally (no explicit starlette pin in this project), which is vulnerable to 7 separate GHSA advisories (GHSA-3qf3-8w2g-rqmx not included -- that's python-jose/ecdsa, unrelated). No poetry.lock exists for this sub-project (confirmed via Dockerfile: only pyproject.toml is copied, 'poetry install --no-root --only main' resolves fresh at build time), so bumping the fastapi constraint is the entire fix -- no lock regeneration needed. fastapi>=0.135.0 requires starlette>=0.46.0 with no upper bound, which resolves to the latest starlette (1.8.0), clearing all 7 CVEs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 fastapi dependency bumped to a version requiring starlette>=1.3.1 (e.g. ^0.135.0 or later)
- [ ] #2 All 7 open Starlette Dependabot alerts on aa-industry dismissed as fixed, or confirmed resolved once Dependabot rescans
- [ ] #3 ai-forecasting service still builds/imports successfully with the bumped dependency (verified via poetry install + a basic import/smoke check, since no automated test suite covers this sub-project)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed: bumped fastapi ^0.110.0 -> ^0.135.0 in ai-forecasting/pyproject.toml (no poetry.lock exists for this sub-project, Dockerfile confirms fresh resolution at build time via 'poetry install --no-root --only main', so the version bump is the complete fix). fastapi>=0.135.0 requires starlette>=0.46.0 with no upper bound, resolving to latest starlette 1.8.0 -- clears all 7 Starlette CVEs. Verified via isolated venv: full dependency set installs cleanly (starlette==1.8.0 confirmed resolved) and 'import ai_forecasting.main' succeeds with the new FastAPI. The other 2 alerts (ecdsa, python-jose) have no fix available -- dismissed as tolerable_risk, same reasoning as aa-kanban TASK-86 (identical allianceauth -> django-esi -> python-jose -> ecdsa transitive chain, confirmed via uv.lock).
<!-- SECTION:NOTES:END -->
