# Walkthrough: Director Control Panel & Core Engine

Domein 3 (Director Control Panel) en de bijbehorende architectuur voor Domein 4 (Core Engine) zijn met succes geïmplementeerd! Dit transformeert het systeem in een beheersbaar ERP-systeem.

## Wat is er gebouwd?

1. **Director Control Panel (`/industry/director/`):**
   - Het hoofdscherm geeft een vogelvlucht over **alle actieve Member Orders** en **alle openstaande Production Tasks**.
   - Je kunt in de Admin direct prioriteiten aanpassen (`HIGH`, `NORMAL`, `LOW`) en taken markeren als `hidden` zodat gewone bouwers ze niet zien.
1. **Item Configuraties (`/industry/director/config/`):**
   - De fundering is gelegd om per EVE Item (`CorpItemConfig`) aan te geven hoe de Core Engine ermee moet omgaan.
   - **Build vs Buy logica:** Geef aan of een sub-onderdeel standaard gekocht of gebouwd moet worden.
   - **BOM Source logica:** Kies per item (bij het bouwen) of je de ingebouwde **SDE (Database)** logica wil gebruiken, of real-time berekeningen via de **Fuzzwork API** voor de Bill of Materials.
   - Stel **Target Thresholds** in voor strategische minimale voorraadniveaus, inclusief de optie "Auto Produce".
   - Stel handmatige Material Efficiency (ME), Time Efficiency (TE) en prijsoverrides in.
1. **Inventory Analytics (`/industry/director/inventory/`):**
   - Een weergave van de virtuele/huidige voorraad op basis van ESI pulls uit de specifiek geselecteerde Corp Hangars.
   - Een speciale **Low Stock** waarschuwingssectie, die items markeert waarvan de huidige voorraad lager is dan de ingestelde *Target Threshold*.
1. **Celery Tasks (Core Engine in `industry/tasks.py`):**
   - `task_sync_corp_inventory`: Leest de corp assets uit via ESI en update lokaal de specifieke gedefinieerde hangars.
   - `task_pull_market_data`: Een dagelijkse taak placeholder om Fuzzwork Jita prijzen in te laden.
   - `task_bom_explosion`: De core logica is geplaatst om straks daadwerkelijk de geneste blauwdruk structuur uit te pluizen.

## Hoe test en configureer je dit?

1. **Rechten:** Zorg dat je bent ingelogd met een account dat Director/Corp rechten heeft.
1. **Menu:** Ververs de pagina en klik in de linker zijbalk op de nieuwe optie **"Director CP"**.
1. **Navigatie:** Vanuit het dashboard kun je via de blauwe en gele knoppen naar de *Inventory Analytics* en *Configurations* schermen doorklikken.
1. **Instellingen (Django Admin):** Ga in de Alliance Auth Admin naar de sectie "INDUSTRY" en maak je eerste configuraties aan:
   - **Corp Item Configs:** Maak een config aan voor bijvoorbeeld *Drake*. Zet hem op BUILD, kies Fuzzwork API, en zet een Target Threshold op 10.
   - **Corp Hangar Configs:** Geef hier aan uit welke Station Location ID en Flag ID (bijv. Corp Hangar 1) de ESI taak de voorraad moet synchroniseren.

Alle datastructuren en schermen voor de Directors en de achterliggende automatiseringstaken staan nu live in de database en code.
