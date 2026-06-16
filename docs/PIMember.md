# Voorstel: Planetary Interaction (PI) Tracking voor Members

## Doelstelling

Het toevoegen van uitgebreide Planetary Interaction (PI) tracking aan de Industry plugin. Hiermee kunnen leden (en eventueel de corporatie) inzicht krijgen in hun actieve PI planeten, de huidige extractie- en productiecycli, en de opslagcapaciteit.

## Benodigde ESI Endpoints & Scopes

Om deze data op te halen, hebben we de volgende ESI Scope nodig:

- `esi-planets.manage_planets.v1` (Geeft leesrechten op de PI setup van een karakter)

Endpoints die gebruikt gaan worden:

1. `GET /characters/{character_id}/planets/`: Haalt een lijst op van alle planeten waar het karakter een Command Center heeft.
1. `GET /characters/{character_id}/planets/{planet_id}/`: Haalt de gedetailleerde layout van een specifieke planeet op (pins, routes, links).
1. `GET /universe/schematics/{schematic_id}/`: Om te bepalen welk product een fabriek (Advanced/Basic Industry Facility) momenteel produceert.

## Datamodellen (Database)

Om alle details op te slaan, stellen we de volgende modellen voor:

1. **CharacterPlanet**

   - Karakter (Koppeling naar EveCharacter)
   - Planet ID & Systeem ID
   - Planet Type (Barren, Lava, Oceanic, etc.)
   - Upgrade Level (Command Center level 0-5)
   - Aantal Pins (gebouwen)
   - Laatste ESI Update

1. **PlanetPin (Gebouwen op de planeet)**

   - Planeet (Koppeling naar CharacterPlanet)
   - Pin ID
   - Type (Extractor Control Unit, Spaceport, Basic/Advanced/High-Tech Factory, Storage Facility, Command Center)
   - **Voor Extractors:**
     - Welk materiaal wordt gewonnen (Product Type ID)
     - Expiry Time (Wanneer stopt de extractor?)
     - Cycle Time
     - Huidige Yield
   - **Voor Factories:**
     - Welk Schematic draait er?
     - Laatste keer dat de cyclus draaide
   - **Voor Storage/Spaceports:**
     - Opslagcapaciteit en huidige vulling (om te waarschuwen als hij vol zit)

## Functionaliteiten & UI (Dashboard)

Op het PI Dashboard (of als nieuwe tab onder Personal Industry) willen we de volgende zaken visueel maken:

1. **Overzicht van Planeten:**
   Een lijst met alle gekoloniseerde planeten per karakter, inclusief het Command Center level.
1. **Detailweergave per Planeet:**
   - **Extractie Status:** Een aftelklok (countdown) die aangeeft wanneer de extractors stoppen met boren.
   - **Productie:** Welke materialen er momenteel worden gefabriceerd (bijv. "Coolant", "Enriched Uranium").
   - **Opslag Waarschuwingen:** Visuele progressie-balkjes (progress bars) voor de Spaceports en Storage Facilities. Als een opslag meer dan 90% vol is, kleurt deze rood.
1. **Discord Notificaties (Optioneel):**
   - "Je extractors op planeet X (Systeem Y) zijn gestopt."
   - "Je Spaceport op planeet X is voor 95% vol."

## Implementatie Stappen

1. **Modellen Toevoegen:** Bovenstaande datamodellen definiëren in `models.py` en migreren.
1. **Celery Taak Maken:** `update_character_pi()` schrijven om periodiek (bijv. elk uur) de planeet-data en pin-data van ESI te halen. Dit moet voorzichtig gebeuren qua rate-limits, aangezien het ophalen van individuele planeet layouts extra API calls kost per planeet.
1. **Views & Templates:** Een nieuwe view `pi_dashboard` maken met bijbehorende Bootstrap-gebaseerde templates.
1. **EveUniverse Integratie:** SDE data ophalen voor schematics en planet types, zodat we mooie iconen en namen kunnen tonen in plaats van abstracte ID's.

## Open Vragen / Keuzes voor jou:

1. Wil je dat deze data ook inzichtelijk is voor de corporatie (Directors), of is dit puur voor de members zelf?
1. Vind je het nuttig om ook Customs Offices (POCO's) en bijbehorende tax-rates inzichtelijk te maken op termijn?
1. Snelheid van updaten: Is 1x per uur voldoende voor PI, of wil je dit frequenter zien?
