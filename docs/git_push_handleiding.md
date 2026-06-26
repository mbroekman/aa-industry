# Git Push & Release Handleiding

Deze handleiding beschrijft de vaste stappen die je moet nemen wanneer je klaar bent om een nieuwe versie van de **Industry Reforged** plugin te publiceren. Omdat we nu een geautomatiseerde GitHub Actions pijplijn hebben voor PyPI en we met taalbestanden werken, is de juiste volgorde belangrijk.

## Stappenplan voor een Release

### 1. Versie verhogen

Voordat je iets doet, moet je de versie van het project verhogen.

- Open `industry_reforged/__init__.py`
- Pas `__version__ = "X.X.X"` aan naar de nieuwe versie (bijv. `0.1.0b4`).

### 2. Vertalingen bijwerken (Indien nodig)

Heb je nieuwe vertalingen toegevoegd of gewijzigd?

- Draai het commando om de bestanden klaar te zetten (kan eventueel ook via `make translations` als je Makefile goed is geconfigureerd):
  ```bash
  django-admin makemessages -a
  ```
- *Let op: de GitHub pipeline compileert de vertalingen automatisch tijdens de release, maar de `.mo` en `.po` bestanden die lokaal zijn aangemaakt moeten wel mee in de commit!*

### 3. Bestanden toevoegen (Staging)

Voeg alle gewijzigde en nieuwe bestanden toe aan Git. Je kunt specifieke bestanden toevoegen:

```bash
git add industry_reforged/__init__.py
git add industry_reforged/locale/nl/LC_MESSAGES/django.po
git add industry_reforged/locale/nl/LC_MESSAGES/django.mo
```

Of je kunt in één keer alles toevoegen wat is gewijzigd (kijk wel altijd even goed uit wat er mee gaat met `git status`):

```bash
git add .
```

### 4. Controleren

Controleer altijd even wat er in je commit komt te staan:

```bash
git status
```

*Alles wat groen is, gaat mee in de commit.*

### 5. De Commit

Maak de commit aan en voorzie deze van een duidelijke en beschrijvende tekst:

```bash
git commit -m "Bump versie naar 0.1.0b4 en voeg nieuwe functionaliteit X toe"
```

### 6. Pushen naar GitHub

Stuur je wijzigingen naar GitHub:

```bash
git push
```

*(Op dit moment gaat GitHub Actions de code controleren met automatische tests en pre-commit checks).*

### 7. Een Release publiceren (PyPI)

Zodra de code op GitHub staat en je tests succesvol zijn afgerond, kun je het pakket naar PyPI sturen:

1. Ga naar je repository op GitHub.
1. Ga aan de rechterkant naar **Releases** en klik op **Draft a new release**.
1. Maak een nieuwe tag aan die precies overeenkomt met je versie (bijv. `v0.1.0b4`).
1. Geef de release een titel en omschrijving.
1. Klik op **Publish release**.

**Resultaat:** Zodra je op Publish klikt, start er een GitHub Action (`release.yml`). Deze installeert de benodigdheden, compileert automatisch voor de zekerheid de vertalingen via `django-admin compilemessages`, bouwt het pakket (`python -m build`) en stuurt de nieuwe versie veilig via *Trusted Publishing* naar PyPI!
