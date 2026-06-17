# Domein 3 & 4: Director Control Panel & Core Engine

Dit plan beslaat de architectuur voor de geavanceerde Director management tools en de onzichtbare achterliggende berekenings- en synchronisatie-engine. Het transformeert de plugin van een simpel portaal naar een volledige ERP- en Supply Chain-oplossing voor EVE Online.

## User Review Required

> [!CAUTION]
> **Enorme complexiteit: SDE vs Fuzzwork API**
> Domein 4 spreekt over *BOM Explosion* (Bill of Materials) en een *Critical Path Optimizer*. Het berekenen van exacte grondstoffen vereist toegang tot de blauwdruk-data van EVE Online. Alliance Auth `eveuniverse` heeft standaard niet de volledige Industry Blueprint SDE ingebouwd.
> *Wil je dat ik deze data live (on-the-fly) ophaal via de Fuzzwork/ESI API voor specifieke blueprints, óf wil je handmatige "Recepten" (Formulas) kunnen aanmaken in Domein 3 voor alleen de schepen die jullie bouwen? (Dat laatste is aanzienlijk sneller en betrouwbaarder te bouwen).*

## Open Questions

> [!IMPORTANT]
> **Vraag 1: BOM Calculatie Systeem**
> Bij BOM (Bill of Materials) explosie: Soms bouwen jullie modules of componenten zelf, soms kopen jullie ze in. Hoe besluit het systeem of een `ProductionTask` moet worden aangemaakt voor sub-componenten, of dat ze uit de voorraad/markt worden gehaald? Wil je een setting "Always Build" / "Always Buy" per item?

> [!IMPORTANT]
> **Vraag 2: ESI Corp Hangars**
> Om de voorraad van de corporatie uit te lezen, heb ik een ESI token nodig van een Director met `esi-assets.read_corporation_assets.v1` rechten. Er moet gedefinieerd worden *welke* hangars (op welke locatie) tot de "Industry Materials" behoren. Gaan we dit instellen via een lijst met Office ID's / Flag ID's in de Director settings?

> [!IMPORTANT]
> **Vraag 3: Market Data Sync frequentie**
> Je geeft aan dagelijks of periodiek de Jita data op te halen voor specifieke items (PI, Moon, Gas). Zullen we hier een dagelijkse Celery task (rond Downtime) voor instellen die alle configuraties automatisch update?

______________________________________________________________________

## Proposed Changes

### Database Modellen (`industry/models.py`)

#### [NEW] Domein 3: Configuratie & Inventaris

- `CorpItemConfig`: Instellingen per item (EveType). Bevat:
  - `manual_me` (int, default 0) - Material Efficiency overschrijving.
  - `manual_price` (Decimal) - Voor Faction BPC's etc.
  - `target_threshold` (int) - Minimum stock level.
  - `auto_produce` (bool) - Maak job aan als stock < threshold.
- `CorpInventory`: Lokale cache van de corp hangars.
  - `item_type`, `quantity`, `location_id`, `last_updated`, `manual_override`.
- `TaxConfig`: Instellingen voor commissies/taxes op orders.

#### [MODIFY] `ProductionTask` & `MemberOrder`

- `priority`: Toevoegen aan `ProductionTask` (`HIGH`, `NORMAL`, `LOW`).
- `hidden`: Boolean om jobs te verbergen voor standaard industrialists.
- `BOM_parent`: Zodat we hiërarchische jobs (Critical Path) kunnen maken (bijv: Job A is een sub-onderdeel voor Job B).

______________________________________________________________________

### Domein 3: Views & Templates (`industry/views.py`)

Een compleet nieuw "Director Dashboard" (`/industry/director/`) met tabbladen:

1. **Order Management:** Tabel met Member Orders met knoppen om alles handmatig te editen/verwijderen.
1. **Job Prioritization:** Drag-and-drop of simpele selectielijsten om prioriteiten aan te passen en jobs te verbergen.
1. **Item Configuration:** Een mass-edit tabel voor het instellen van ME, prijzen en Thresholds.
1. **Inventory & Analytics:**
   - Huidige (virtuele) voorraad vs Thresholds.
   - Cost Analysis (Market Sell vs. Berekende bouw-kosten).
   - Low/Missing stocks waarschuwingen.

______________________________________________________________________

### Domein 4: Core Engine (Celery Tasks in `industry/tasks.py`)

#### [NEW] `task_sync_corp_inventory`

- Trekt data uit ESI `corporations/{corp_id}/assets/`.
- Filtert op specifieke gedefinieerde Hangars/Containers.
- Updatet de `CorpInventory` tabel.

#### [NEW] `task_pull_market_data`

- Haalt via Fuzzwork API de actuele Jita Sell/Buy prijzen op voor de benodigde lijst (PI, Goos, Gases, Minerals).
- Haalt System Cost Index op voor jullie doelsysteem (b.v. een Nullsec of Lowsec systeem ID die in te stellen is).

#### [NEW] `task_bom_explosion`

- Functie die wordt aangeroepen na goedkeuring van een order óf een threshold breach.
- Berekent exact de materialen die nodig zijn, trekt de huidige (virtuele) voorraad eraf, en genereert `ProductionTask`s voor de ontbrekende delen. Neemt hiërarchie mee voor het *Critical Path*.

______________________________________________________________________

## Verification Plan

### Test scenario's:

1. Als Director een target threshold instellen voor 500x 'Morphite'.
1. Celery task voorraad laten controleren -> Systeem genereert automatisch een ProductionTask als de voorraad op 0 staat.
1. Handmatig een MemberOrder overrulen en annuleren; gerelateerde jobs moeten correct geannuleerd/verborgen worden.
1. Celery market task aanroepen en verifiëren dat prijzen lokaal kloppen met Jita Fuzzwork data.
