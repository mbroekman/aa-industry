# Proposal: Bill of Materials (BOM) for Market Orders

## 1. Doelstelling

Het doel van deze uitbreiding is om spelers en directors direct inzicht te geven in de benodigde materialen (Bill of Materials of BOM) om specifieke marktopdrachten (Market Orders of Production Tasks) te produceren. Door het koppelen van de orders aan de juiste Blueprints, kan de plugin de exacte hoeveelheid materialen en geschatte inkoopkosten presenteren, rekening houdend met Material Efficiency (ME) en eventuele structure bonussen.

## 2. Technische Architectuur & Databronnen

Om de materialen te berekenen hebben we een databron nodig die weet welke grondstoffen in een blueprint gaan. Er zijn twee primaire opties:

### Optie A: Fuzzwork Industry API (Aanbevolen voor snelle integratie)

Aangezien de plugin al succesvol Fuzzwork gebruikt voor prijzen (`pricing_engine.py`), kunnen we de Fuzzwork Blueprint API gebruiken (`https://fuzzwork.co.uk/blueprint/api/blueprint.php?typeid=X`).

- **Voordelen**: Geen zware lokale database (SDE) nodig. Altijd up-to-date. Zeer eenvoudig te implementeren.
- **Nadelen**: Afhankelijkheid van een externe third-party API. Mocht Fuzzwork offline gaan, werkt de BOM calculatie niet meer.

### Optie B: Lokale EVE SDE / eveuniverse

Gebruik maken van een geïnstalleerde SDE app (zoals `allianceauth-app-sde`) om lokaal de materialen op te vragen via de database modellen.

- **Voordelen**: Volledig lokaal, offline ondersteuning en zeer snel na de eerste import. Perfect voor nauwkeurige integratie van structure rigs (Athanor/Tatara/Raitaru bonussen).
- **Nadelen**: Vereist dat de alliance auth server periodiek de zware SDE industrie tabellen inlaadt en bijhoudt.

*Voorstel:* Begin met **Optie A (Fuzzwork API)** en voeg een caching laag toe in de backend. Dit sluit goed aan bij de huidige `BOM_CHOICES` die al deels gedefinieerd lijken te zijn in `models.py`.

## 3. Backend Implementatie (Python / Django)

### A. Calculator Functie

Voeg een functie toe (bijv. in `utils/bom_engine.py`) die de benodigde materialen berekent:

```python
def calculate_bom(product_type_id, quantity, me_level=0, structure_bonus=1.0):
    # Haal base materials op (bijv via Fuzzwork of SDE)
    # Formule: ROUND(Base_Quantity * (1 - (ME_Level / 100)) * Structure_Bonus)
    # Vermenigvuldig met de totale batch quantity
    return list_of_materials
```

### B. Opslag of Dynamisch Ophalen?

- **Dynamisch**: Voor kleine opdrachten berekenen we de BOM 'on the fly' in de View wanneer een gebruiker de details opvraagt.
- **Opslag**: Voeg een JSONField (`bom_data`) toe aan de `ProductionTask` of `MemberOrder` modellen om de berekende materialen in op te slaan zodra de order geaccepteerd/aangemaakt wordt. Dit bespaart rekentijd en API-limieten.

## 4. Frontend Implementatie (UI/UX)

De visuele weergave moet consistent zijn met het huidige Amarr Gold thema en gebruik maken van Bootstrap 5.

### A. Order Detail Modal / Accordion

Op het Dashboard (waar de marktopdrachten staan), voegen we een knop toe: **"View Blueprint Materials"**.
Wanneer hierop geklikt wordt, klapt er een tabel open (of een Modal venster verschijnt) met:

- Icoon + Naam van het materiaal
- Benodigde hoeveelheid (met duizendtallen scheiding, `intcomma`)
- Geschatte prijs per unit (via de bestaande pricing engine)
- Totale prijs voor de benodigde batch

### B. "Shopping List" / "Consolidated BOM" (Optioneel)

Een krachtige toevoeging is een tabblad of pagina genaamd **"Shopping List"**. Hier kunnen spelers meerdere orders aanvinken en op een knop drukken om één gigantische, opgetelde lijst van grondstoffen te genereren voor hun volgende Jita run.

## 5. Implementatie Stappenplan

1. **Fase 1 - Datalaag**: Aanmaken van `bom_engine.py` om met Fuzzwork (of SDE) de blueprint materialen op te halen op basis van een `type_id`.
1. **Fase 2 - Caching/Modellen**: Toevoegen van benodigde attributen of tabellen om de Blueprint configuratie per item op te slaan (welke ME en welke rigs gebruiken we?). De basis hiervoor lijkt al aanwezig in `CorpItemConfig`.
1. **Fase 3 - Backend Integratie**: Koppel de `MemberOrder` / `ProductionTask` logica aan de `bom_engine` zodat de data in de views beschikbaar wordt.
1. **Fase 4 - UI/UX**: Aanpassen van de HTML templates (`view_quote.html`, dashboards) met strakke tabellen om de materialen te presenteren.

______________________________________________________________________

*Auteur: Antigravity / EVE Online Alliance Auth Assistent*
