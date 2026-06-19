# Modernisering Industry Plugin - Amarr Gold Editie

De Industry plugin heeft een volledige make-over gekregen in lijn met het "Amarr Gold" thema, specifiek ontworpen om naadloos aan te sluiten op de dark-mode van Alliance Auth en het sci-fi / EVE Online gevoel.

## Wat is er gewijzigd?

### 1. Gecentraliseerde Design Styling

Er is een gloednieuwe stylesheet aangemaakt: `industry/static/industry/css/industry.css`. Hierin zitten alle custom styling elementen geconcentreerd.
Deze sheet is gekoppeld aan `base.html`, waardoor alle wijzigingen in de toekomst op één plek beheerd kunnen worden.

### 2. Visuele Kenmerken

- **Amarr Gold Accenten:** Elementen lichten op met een zacht goud/gele neon glow. Tekst in de headers en knoppen gebruikt accenten van Amarr Gold (`#D4AF37`) en de lichte variant (`#F2D35A`).
- **Glassmorphism:** De standaard platte Bootstrap cards zijn vervangen door zwevende kaarten met lichte semi-transparantie en een `backdrop-filter: blur()`. Zodra je er met de muis over zweeft lichten ze op.
- **Micro-Animaties:** Data-rijen in de tabellen hebben een vloeiende hover (`rgba(212, 175, 55, 0.08)`) om het scannen van data makkelijker en dynamischer te maken.

### 3. Scherm-updates

Elk dashboard is opgeschoond. We hebben afscheid genomen van de hard-coded Bootstrap basiskleuren (`bg-primary`, `bg-info`) die detoneren met een premium design.
De volgende schermen hebben de Amarr behandeling gekregen:

- Corporate Dashboard
- Director Configuraties & Hangar Discovery
- Director Dashboard (Control Panel)
- Industrialist Dashboard (Job Market)
- Industrialist Leaderboards
- Personal Dashboard
- Create Order & Quote Weergave

## Hoe test je dit?

Navigeer simpelweg door je lokale applicatie heen. Alles moet nu strakker, donkerder en hoogwaardiger aanvoelen met gouden accenten en strakke, afgeronde (glass) badjes.

> [!TIP]
> Omdat er een nieuwe `.css` file is toegevoegd, moet je mogelijk even je browser cache legen (`Ctrl + F5` of `Cmd + Shift + R`) zodat de nieuwe styling direct geladen wordt!

Mocht je in de toekomst (of direct) een tweede kleurenschema willen introduceren (bijv. Caldari Blue of een meer neutraal thema), dan hoeven we alleen maar de variabelen in `industry.css` aan te passen!
