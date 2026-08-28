---
name: release
description: Gebruik deze skill om een nieuwe release van het project te maken via Commitizen en de GitHub Actions workflows.
---

# Release Instructies

Gebruik deze skill ALTIJD wanneer de gebruiker vraagt om een nieuwe versie of release te maken voor dit project.

## Workflow

Voer de volgende stappen uit in exacte volgorde:

1. **Status Validatie:**

   - Controleer via `git status` of de working directory schoon is (geen ongecommitte wijzigingen, met uitzondering van wijzigingen die nog in de release mee moeten).
   - Als er nog niet-gecommitteerde wijzigingen zijn die wél mee moeten, commit deze dan met een geldige conventional commit message voordat je verder gaat.

1. **Commitizen (Versie bump & Changelog):**

   - Voer het commando `cz bump` uit.
   - *Let op:* Dit commando berekent automatisch de nieuwe versie op basis van de git geschiedenis, maakt de `CHANGELOG.md` aan, update de versie in `pyproject.toml` en `__init__.py`, en creëert direct de git commit en tag.

1. **Remote Publicatie:**

   - Push de nieuwe commit en de tag naar GitHub via:
     ```bash
     git push && git push --tags
     ```

1. **GitHub Actions Overdracht:**

   - Informeer de gebruiker dat de stappen succesvol zijn afgerond en dat GitHub Actions (de `release.yml` workflow) nu de rest overneemt.
   - De CI pipeline zal de `.po` vertalingen compileren, de package bouwen en het resultaat publiceren naar PyPI, evenals een GitHub Release met notes aanmaken.
