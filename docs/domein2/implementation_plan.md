# Domein 2: Industrialist Dashboard (Execution & Tracking)

Dit domein voegt een compleet operationeel dashboard toe voor de bouwers ("Industrialists") binnen de corporatie. Het vertaalt geaccepteerde bestellingen (Member Orders) of Director-doelen naar interne *Production Tasks* in een **Job Market**. Bouwers kunnen deze tasks claimen, uitvoeren en afronden, waarbij hun prestaties worden bijgehouden voor **Gamification** en **Leaderboards**.

## User Review Required

> [!IMPORTANT]
> Voordat ik begin met bouwen, heb ik de onderstaande vragen. Jouw feedback bepaalt de definitieve workflow!

## Open Questions

> [!WARNING]
> **1. Automatisering van Jobs (Member Orders)**
> Als een Director een `MemberOrder` accepteert, wil je dan dat het systeem **automatisch** voor elk besteld onderdeel (bijv. de Hull en de Modules) een losse `ProductionTask` in de *Job Market* zet?

> [!WARNING]
> **2. Afhandeling van voltooide Jobs**
> Als een bouwer een job heeft geclaimd en deze in EVE Online daadwerkelijk aflevert (Deliver), wil je dat ze in het Industrialist Dashboard handmatig op een "Mark as Completed" knop drukken? (Dit is het meest robuust en makkelijk te bouwen).
> *Alternatief:* We kunnen proberen dit te koppelen aan de automatische ESI-sync, maar dat is vaak foutgevoelig als bouwers via andere characters/corps produceren.

> [!WARNING]
> **3. Leaderboard Metrics (Punten vs ISK)**
> Voor de gamification wil ik de Fuzzwork Jita-waarde van het gebouwde item gebruiken als 'score'. Dus als je een schip van 50 miljoen ISK bouwt, krijg je "50M" aan punten op het leaderboard. Is dit wenselijk, of werk je liever met een plats "Aantal jobs afgerond" scorebord?

______________________________________________________________________

## Proposed Changes

We gaan de applicatie uitbreiden met nieuwe datamodellen, een nieuw hoofddashboard en diverse kleine views om de workflows te ondersteunen.

### Models & Database (`industry/models.py`)

#### [NEW] ProductionTask

Dit wordt het hart van de Job Market. Het abstraheert een behoefte binnen de corporatie.

- `item_type`: Wat er gebouwd of gereageerd moet worden (`EveType`).
- `quantity`: Hoeveel stuks (`Integer`).
- `status`: `UNCLAIMED`, `IN_PRODUCTION`, `COMPLETED`.
- `created_from_order`: Koppeling naar de `MemberOrder` (optioneel).
- `assigned_to`: Welk character (`EveCharacter`) deze job heeft geclaimd.
- `assigned_at` & `completed_at`: Tijdstempels.
- `gamification_value`: De ISK-waarde (op moment van claimen) voor het leaderboard.

#### [NEW] CorpMOTD

- Een simpel model waar een Director een "Message of the Day" in kan opslaan. Bijv: *"Focus op Drakes deze week!"*

#### [MODIFY] General Permissions

- Toevoegen van een nieuwe permissie: `"industrialist_access"`.

______________________________________________________________________

### Logic & Signals (`industry/signals.py`)

#### [NEW] `create_tasks_from_order`

- (Afhankelijk van antwoord op Q1): Een automatische trigger die kijkt of een `MemberOrder` de status `ACCEPTED` krijgt. Zo ja, dan genereert hij voor alle `OrderItems` onzichtbaar een `ProductionTask` in de Job Market.

______________________________________________________________________

### Views & UI (`industry/views.py` & templates)

#### [NEW] `industrialist_dashboard.html` / `views.py`

Een gloednieuw, breed dashboard speciaal voor bouwers met meerdere secties:

1. **Message of the Day (MOTD):** Prominent bovenaan.
1. **The Job Market (Unclaimed):** Een lijst met alle openstaande taken (inclusief item iconen). Bevat een **[Claim Job]** knop.
1. **My Active Production:** Overzicht van de taken die de ingelogde gebruiker zojuist geclaimd heeft. Bevat een **[Mark Completed]** knop.
1. **Corp Active Jobs:** Een high-level overzicht van wie wat aan het bouwen is (geanonimiseerd/gestripte versie van de `CorporationIndustryJob` data uit ESI).

#### [NEW] `industrialist_leaderboard.html` / `views.py`

Een pagina toegewijd aan gamification:

- **Top Builders:** Ranglijst gesorteerd op `gamification_value` of aantal afgeronde jobs (deze maand of all-time).
- **Personal History:** Een uitklapbare log van alle `ProductionTasks` die deze specifieke speler ooit succesvol heeft afgerond.

______________________________________________________________________

## Verification Plan

### Automated / Manual Verification

1. Ik log in als Director en accepteer een Test Order.
1. Ik controleer of de items van de order correct verschijnen in de "Job Market".
1. Ik log in als Industrialist, zie de MOTD, en klik op [Claim Job].
1. Ik controleer of de job verschuift naar "My Active Production".
1. Ik voltooi de job en verifieer dat mijn score toeneemt op het Leaderboard.
