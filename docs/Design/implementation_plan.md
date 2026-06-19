# Voorstel: Modern UI/UX Design voor Alliance Auth Industry

Dit voorstel beschrijft de aanpak om alle schermen van de Industry plugin een strakkere, modernere "look and feel" te geven. We stappen af van de standaard "platte" Bootstrap 5 look en introduceren een premium design dat perfect past in de sci-fi / EVE Online sfeer, met behoud van de overzichtelijkheid die Alliance Auth vereist.

## User Review Required

> [!IMPORTANT]
> Graag je feedback op de onderstaande design keuzes. Zodra je akkoord bent met deze visie, ga ik de wijzigingen doorvoeren op alle templates en de centrale CSS file aanmaken.

## Open Questions

> [!WARNING]
> Wil je een specifiek kleurenschema aanhouden? (Bijv. Caldari Blue, Amarr Gold, of neutraal donkergrijs/neon blauw?)
> Wil je dat we een specifiek modern lettertype (zoals 'Inter' of 'Roboto') inladen via Google Fonts, of moeten we het standaard font van jullie Alliance Auth installatie aanhouden?

## Proposed Changes

### 1. Centrale Design Styling (CSS)

We maken een nieuwe gecentraliseerde stylesheet aan (`industry.css`) die wordt ingeladen in `base.html`. Hierin definiëren we design tokens (CSS variabelen) zodat de hele plugin consistent is.

**Kenmerken van het design:**

- **Sci-Fi / EVE Thema:** Donkere achtergronden (`#1b1d22`), subtiele grid-lines of borders.
- **Glassmorphism:** Cards krijgen een lichte semi-transparante overlay (bijv. `rgba(255, 255, 255, 0.03)`) met een subtiele `backdrop-filter: blur()`. Hierdoor lijken ze te "zweven" boven de achtergrond.
- **Accenten & Neons:** Primaire acties (knoppen, actieve tabs) krijgen een opvallende neon-gloed bij een hover (bijv. helder cyaan of oranje).

### 2. Cards & Containers (Dashboards)

De standaard `card` classes van Bootstrap worden overschreven of aangevuld met specifieke classnamen:

- Standaard borders (bijv. `border-primary`) worden vervangen door subtiele, strakke randen (1px solid met lage opacity).
- Headers van cards krijgen een naadloze overgang met de body (geen harde lijnen meer).
- **Micro-animaties:** Als de gebruiker met de muis over een card gaat, schuift deze subtiel 2px omhoog met een lichte drop-shadow transformatie. Dit maakt de dashboards dynamisch en "alive".

### 3. Data Tabellen (DataTables)

Omdat industrie draait om data, moeten de tabellen perfect zijn:

- **Zebra-striping out, hover-effects in:** De standaard zebra-rijen worden vervangen door naadloze rijen die duidelijk oplichten (`rgba(0, 195, 255, 0.1)`) zodra je er met de muis over zweeft.
- **Typografie:** Nummers (zoals ISK bedragen en ME/TE) krijgen een monospaced / tabular-nums font instelling, zodat getallen netjes onder elkaar uitlijnen.
- **Badges:** De huidige standaard badges (groen, grijs) krijgen zachtere, "pastel" of "glow" kleuren met afgeronde hoeken voor een premium feel.

### 4. Navigatie & Knoppen

- Standaard knoppen (`btn-primary`, `btn-outline-info`) krijgen een custom styling. In plaats van platte kleuren werken we met lichte gradients en hover-effecten die de helderheid verhogen.
- Icoontjes (FontAwesome) krijgen iets meer ademruimte (margin) ten opzichte van de tekst.

## Verification Plan

### Manual Verification

- We controleren visueel elk dashboard (`director_dashboard`, `corporate_dashboard`, `personal_dashboard`, `director_discover_hangars`).
- We verifiëren of het nieuwe design niet breekt op mobiele apparaten (responsiveness blijft intact).
- We testen dark/light mode compatibiliteit indien jullie Alliance Auth installatie dit ondersteunt.
