---
name: release
description: Gebruik deze skill om een nieuwe release van het project te maken, te taggen, te pushen en te publiceren via GitHub Releases.
---

# Release Instructies

Gebruik deze skill ALTIJD wanneer de gebruiker vraagt om een nieuwe versie of release te maken voor dit project.

## Workflow

Voer de volgende stappen uit in exacte volgorde:

1. **Status Validatie & Pre-commit:**

   - Controleer via `git status` of de working directory schoon is (of commit de openstaande wijzigingen met een conventional commit).
   - Zorg dat alle pre-commit hooks en unit tests slagen.

1. **Versie bump & Changelog:**

   - Werk `CHANGELOG.md` bij met de nieuwe release-sectie en release-notes.
   - Bump het versienummer in `industry_reforged/__init__.py` en `pyproject.toml`.
   - Of gebruik `cz bump` indien geconfigureerd.

1. **Git Commit & Tag:**

   - Commit de wijzigingen op `main` met een duidelijke release commit message (bijv. `chore: bump version to X.Y.Z`).
   - Maak een annotated git tag aan: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.

1. **Remote Publicatie:**

   - Push zowel de branch als de tag naar GitHub:
     ```bash
     git push origin main && git push origin vX.Y.Z
     ```

1. **GitHub Release Aanmaken (Verplicht):**

   - Maak direct een officiële release aan op GitHub via de GitHub CLI (`gh`):
     ```bash
     gh release create vX.Y.Z --title "Release vX.Y.Z" --notes "<Release Notes uit CHANGELOG.md>"
     ```
   - Verifieer dat de release succesvol is aangemaakt via `gh release view vX.Y.Z`.

1. **Rapportage:**

   - Toon de gebruiker de release URL, het versienummer en een overzicht van de meegeleverde wijzigingen.
