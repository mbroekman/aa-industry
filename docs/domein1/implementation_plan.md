# Member Portal (Self-Service & Ordering)

De "Member Portal" voegt een compleet nieuw domein toe aan de Industry plugin. Het stelt alliantie- of corporatieleden in staat om (via een EFT-fit of losse items) schepen, modules en componenten aan te vragen. Vervolgens berekent een *Quote Engine* automatisch een prijs, die de gebruiker kan accepteren om een actieve order te plaatsen.

## User Review Required

> [!IMPORTANT]
> Om deze grote feature succesvol in te bouwen, heb ik een ontwerp gemaakt. Controleer met name de **Open Questions** hieronder en reageer hierop, zodat de implementatie exact aansluit bij jullie visie!

## Open Questions

> [!WARNING]
> **1. Prijzen (Jita vs Global Average)**
> Je vraagt specifiek om "actuele Jita-prijzen". De ingebouwde EVE API (via `django-eveuniverse`) ondersteunt standaard alleen *Global Average* prijzen. Om échte actuele Jita (buy/sell) prijzen te krijgen, moeten we integreren met een externe dienst zoals **Janice** (app.janice.com) of **Fuzzwork**. Hebben jullie al een voorkeur voor een prijs-API, of zal ik een standaard integratie bouwen met Janice/Fuzzwork?

> [!WARNING]
> **2. Kortingssysteem (Corp-korting)**
> Hoe werkt de "eventuele corp-korting"? Is dit een vast percentage over de Jita-prijs (bijv. 90% van Jita Sell) dat via de Admin-interface voor de hele corporatie kan worden ingesteld, of wil je kortingen per Item Category (Hulls, Modules, Capital parts)?

## Proposed Changes

We gaan de applicatie in de breedte uitbreiden met nieuwe datamodellen, views, parsers en Celery tasks.

### Models & Database (`industry/models.py`)

#### [NEW] MemberOrder

- Bevat de hoofdorder: Koper (`EveCharacter`), Totaalbedrag (Quote), Status, Aanvraagdatum, Corp Discount toegepast.
- Status velden: `REQUESTED`, `QUOTED`, `ACCEPTED`, `IN_PRODUCTION`, `READY`, `DELIVERED`, `REJECTED`.

#### [NEW] OrderItem

- Koppelt aan een `MemberOrder`.
- Bevat het aangevraagde onderdeel: `EveType` (het item), Aantal, Prijs per stuk (op moment van quoten).

#### [NEW] OrderFit

- (Optioneel) Bewaart de originele EFT-string die de speler heeft geplakt als naslagwerk.

#### [NEW] CorpPricingConfig

- Een instellingen-tabel waar beheerders een standaard Jita-prijs formule kunnen kiezen (bijv. Jita Sell, Jita Buy, Jita Split) en een kortingspercentage per corporatie.

______________________________________________________________________

### Logic & Parsing (`industry/utils/`)

#### [NEW] `fit_parser.py`

Een slimme parser die een tekstblok (EFT format) uitleest:

1. Herkent het `[Schipnaam, Fitnaam]` headerformaat om de hull te vinden.
1. Leest regel voor regel de modules uit (en negeert cargo-capaciteit of ammo text).
1. Koppelt de namen via `eveuniverse` direct aan een EVE `type_id`.

#### [NEW] `pricing_engine.py`

De rekenmodule die de Quote samenstelt.

1. Neemt een lijst met `OrderItems`.
1. Haalt de actuele Jita-prijs op (via externe API of interne cache).
1. Trekt de corp-korting eraf.
1. Berekent het eindtotaal en slaat de quote op in de order.

______________________________________________________________________

### Views & UI (`industry/views.py` & templates)

#### [MODIFY] `personal_dashboard.html` / `views.py`

We breiden het bestaande Personal Dashboard uit met een **"My Orders"** tab, of we maken er een geheel losse pagina van (`/industry/orders/`). Hier ziet het lid zijn bestellingen met badges voor de huidige status (Requested, In Production, etc.).

#### [NEW] `create_order.html`

Een laagdrempelig formulier met twee opties:

1. **Paste a Fit:** Een groot tekstvak om een EFT fit in te plakken.
1. **Add Individual Items:** Een zoekveld (met autocomplete voor EVE items) om losse schepen of componenten aan het mandje toe te voegen.

#### [NEW] `view_quote.html`

Een overzichtspagina van de aangevraagde order:

- Een gespecificeerde factuur met prijzen per item.
- Twee grote knoppen: **[Accept Quote]** of **[Reject Quote]**.

______________________________________________________________________

## Verification Plan

### Automated Tests

- Testen van de `fit_parser.py` met diverse in-game EFT strings (van frigates tot capitals) om er zeker van te zijn dat alle modules foutloos gekoppeld worden aan `EveType`s.
- Simuleren van de `pricing_engine.py` om kortingen correct te verifiëren.

### Manual Verification

1. Als de gebruiker (via de browser) een EFT fit plakt, moet deze worden omgezet in een net overzicht van losse items in de winkelmand.
1. Na indienen wordt er onzichtbaar op de achtergrond een Quote berekend.
1. De gebruiker kan de Quote accepteren, waarna de status in het Order Tracking dashboard verandert van `QUOTED` naar `ACCEPTED`.
