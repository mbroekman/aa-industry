# AA-Industry (Industry Reforged) - AI Agent Guidelines

Dit project maakt integraal onderdeel uit van de Workbench 001 workspace en erft alle bindende richtlijnen van het centrale hoofd-instructiedocument:
👉 **[Centrale AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md)**

Lees tevens altijd eerst [.agent/memory.md](file:///g:/My%20Drive/Workbench%20001/.agent/memory.md) vóór analyse of modificatie (Regel 1 van AGENTS.md).

---

## 1. Project Context & Backlog Directory

- **Plugin:** `aa-industry` (Django App: `industry_reforged`)
- **Backlog Map:** `plugins/aa-industry/backlog/`
- **Directory Context (CRITICAL):** Alle `backlog` CLI commando's en MCP interacties **MOETEN** worden uitgevoerd met de werkmap ingesteld op `plugins/aa-industry` (bijv. `cd plugins/aa-industry` of via de `Cwd` parameter in toolcalls), zodat taken correct in de backlog van `aa-industry` worden geplaatst en beheerd.

---

## 2. Bindende Centrale Regels (Inherited from Master AGENTS.md)

Alle standaarden uit de centrale [AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md) zijn hier onverkort van toepassing:

- **Taakbeheer via Backlog.md:** Eerst taak registreren/WIP zetten in `backlog-md` vóór het schrijven of wijzigen van code. Afronden pas na testen, linting en type-checks.
- **Tooling & Omgeving:** `uv` voor package management, `Ruff` (line-length 120), `mypy` strict met `django-stubs`, `pytest` en `pytest-django`.
- **Alliance Auth UI & Bootstrap 5:** Altijd `{% extends "allianceauth/base-bs5.html" %}`, uitsluitend Bootstrap 5 componenten (`card`, `badge bg-*`, `d-flex`, `btn-sm`). Nooit Bootstrap 3 componenten (`panel`, `label`, `pull-right`). Geen eigen `{% if messages %}` block toevoegen.
- **Pre-Commit Verificatie:** Update `CHANGELOG.md` en user docs (`user_manual_en.md`) vóór taakafronding. Nooit automatische releases of tags.

---

## 3. Project-Specifieke Conventies (Industry Reforged)

### Celery Tasks
- Elke nieuwe `@shared_task` die periodiek draait **moet** in **dezelfde commit** worden toegevoegd aan het `CELERYBEAT_SCHEDULE` blok in `README.md`.
- Taaknamen volgen het patroon `industry_reforged.tasks.<function_name>` (consistent met de `name=` decorator argument).
- **Helper tasks** (zoals `resolve_unknown_locations(location_ids)` met vereiste parameters) mogen **NIET** aan `CELERYBEAT_SCHEDULE` worden toegevoegd.

### Templates & DataTables
- DataTables `colspan` in `{% empty %}` rijen moet exact overeenkomen met het aantal `<th>` kolommen in `<thead>` (voorkomt DataTables fout TN/18).
- DataTables `columnDefs` target indices zijn 0-based; controleer indices na toevoegen of verwijderen van kolommen.
