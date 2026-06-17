# Walkthrough: Industrialist Dashboard

Domein 2 is met succes geïmplementeerd! De "Industrialist Dashboard" is nu een actieve module in Alliance Auth voor bouwers.

## Wat is er gebouwd?

1. **Automatisering Member Orders:** Zodra een Director (of geautoriseerde gebruiker) een Quote accepteert in de *Member Orders* weergave, knipt het systeem de order automatisch op in losse `ProductionTask`s voor elk type onderdeel en plaatst deze in de Job Market.
1. **Industrialist Dashboard (`/industry/industrialist/`):**
   - **MOTD (Message of the Day):** Een notificatiepaneel (beheerd via de Django Admin `CorpMOTD`) waar instructies voor de industriëlen kunnen worden achtergelaten.
   - **Job Market:** Een dynamische lijst van openstaande productietaken ("Unclaimed"). Met één druk op de "Claim" knop wijst de industrialist de taak aan zijn of haar gekozen EVE character toe.
   - **My Active Production:** Een persoonlijk overzicht van geclaimde taken die momenteel 'In Production' zijn. Zodra het bouwen (in-game) is afgerond, kan de speler hier op "Complete" klikken.
1. **Smart Order Tracking:** Zodra een industrialist een taak op "Complete" zet, checkt het systeem of de *volledige* originele Member Order nu klaar is. Als er geen openstaande taken meer zijn voor die order, verspringt de Order Status automatisch naar `READY` (Ready for Pickup).
1. **Leaderboards & Historie (`/industry/industrialist/leaderboard/`):**
   - **Top Builders (Taken):** Een ranglijst gesorteerd op wie de meeste losse taken succesvol heeft afgerond.
   - **Top Builders (ISK):** Een ranglijst gesorteerd op de ISK-waarde (de gamification punten) van wat ze hebben geproduceerd.
   - **Personal History:** Een archief per speler van alles wat ze tot dusver gebouwd hebben.

## Hoe test je dit?

1. Zorg ervoor dat je account in Alliance Auth de `industrialist_access` permissie heeft. (Of log in als superuser).
1. Ververs de pagina; je zou in het linkermenu nu **"Industrialist Dash"** moeten zien.
1. **Trigger:** Maak via de `Member Orders` tab een nieuwe order aan en Accepteer de Quote.
1. Ga nu naar het `Industrialist Dash`. Je ziet alle onderdelen uit die order in de **Job Market** staan.
1. Claim een taak door op de groene knop te drukken. Hij verplaatst zich naar de "My Active Production" tabel.
1. Druk op **Complete**.
1. Ga vervolgens naar **Leaderboards & History** via de blauwe knop rechtsboven om je verdiende score en persoonlijke productiegeschiedenis te bekijken!
