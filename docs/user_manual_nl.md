# Industry Reforged - Gebruikershandleiding

Deze handleiding beschrijft alle functionaliteiten van de **Industry Reforged** plugin voor Alliance Auth, opgedeeld per gebruikersrol.

______________________________________________________________________

## 1. Voor Leden (Members)

### 1.1 Personal Dashboard

Het Personal Dashboard is je persoonlijke overzicht voor alles wat met industrie te maken heeft.

- **My Industry Jobs**: Bekijk de live status van al je persoonlijke fabrieksopdrachten in EVE Online. Je ziet exact wanneer een job klaar is dankzij de realtime countdown timers.
- **Planetary Interaction (PI)**: Volg de status van je PI planeten. Je ziet in één oogopslag of je extractors nog lopen en of je opslagfaciliteiten vol dreigen te raken.
- **Discord Notificaties**: Als je jouw Discord-account hebt gekoppeld in Alliance Auth, stuurt de plugin je automatisch een privébericht (DM) zodra een fabriekstaak is afgerond of als een PI extractor verloopt/vol raakt.

### 1.2 Orders Dashboard & Bestellen

Leden kunnen via de plugin schepen, modules en structuren bestellen bij de corporatie.

- **Bestelling Plaatsen**: Klik op "New Order", selecteer een karakter en plak een complete *EFT/Pyfa fit* in het tekstvak. De plugin berekent automatisch de benodigde materialen.
- **Offerte Flow**: Na het indienen krijgt je bestelling de status `REQUESTED`. Een director zal de bestelling bekijken en een prijs (quote) opgeven. Zodra dit is gebeurd, verandert de status naar `QUOTED`.
- **Accepteren**: Je kunt de offerte inzien, je korting (savings) ten opzichte van Jita bekijken, en de order "Accepteren". Hierna wordt deze doorgestuurd naar de bouwers.

______________________________________________________________________

## 2. Voor Bouwers (Industrialists)

### 2.1 Industrialist Dashboard (Job Market)

Dit is de centrale marktplaats voor corporatie-bouwers.

- **Job Market (Unclaimed)**: Zodra een lid een bestelling accepteert, breekt het systeem de bestelling op in losse productie-taken (Production Tasks). Als bouwer kun je hier taken "Claimen".
- **My Active Production**: Een overzicht van de taken die jij hebt geclaimd en momenteel aan het bouwen bent. Zodra je klaar bent, markeer je ze als "Complete".

### 2.2 Leaderboards & Gamification

- Elke voltooide taak levert je punten op (gebaseerd op de ISK-waarde van de taak).
- In het **Leaderboard** kun je zien wie de meest actieve bouwers van de corporatie zijn, zowel op basis van het aantal voltooide taken als de totale ISK-waarde.

### 2.3 Shopping List

- Handig voor inkopers of bouwers: genereer een "Shopping List" van benodigde materialen voor een specifieke bestelling of groep taken. Je kunt deze lijst met één druk op de knop kopiëren in EVE Online "Multibuy" formaat.

______________________________________________________________________

## 3. Voor Directeuren (Directors & Managers)

### 3.1 Director Control Panel

Het commandocentrum voor de industriële ruggengraat van de corporatie.

- **Active Member Orders**: Een overzicht van alle binnengekomen bestellingen.
- **Quoting Flow**: Klik op een order die `REQUESTED` is om de Bill of Materials te bekijken en een handmatige offerte (Quote) op te geven. Je ziet hierbij direct de verwachte inkoopkosten.
- **Production Tasks**: Beheer de losse bouwtaken. Je kunt zien wie welke taak heeft geclaimd en je kunt indien nodig taken intrekken of handmatig voltooien.

### 3.2 Inventory & Analytics

- Volledig inzicht in de voorraden van de corporatie, op basis van de gekoppelde "ESI Hangars".
- **Low Stock Alerts**: Definieer een drempelwaarde (Target Threshold) voor items. Zakt de voorraad hieronder? Dan verschijnt er direct een rode "Action Required" melding en badge, zodat je nooit zonder essentiële schepen of modules komt te zitten.

### 3.3 Corporate Wallets

- Monitor de ISK-balans van alle 7 corporatie-portemonnees (divisions).
- Bekijk en filter het gedetailleerde **Journal** om inkomsten en uitgaven (bijv. orderbetalingen of belastinginkomsten) te analyseren.

### 3.4 Configuratie & Regels (Director Config)

- **Global Configurations**: Stel in welke items de corporatie "Bouwt" (BUILD) of "Koopt" (BUY).
- Bepaal per item de handmatige ME/TE (Material/Time Efficiency) waarden, vaste prijzen, en de gewenste drempelwaarde voor "Low Stock Alerts".
- **Discover Hangars**: Voordat de inventaris gesynchroniseerd kan worden, moet je via "Discover Hangars" aangeven *welke* specifieke corporatie-hangars in welke structuren door de plugin in de gaten gehouden moeten worden.

### 3.5 Corporate Discord Webhooks

- Naast privéberichten voor leden, kunnen directeuren webhooks configureren voor de corporatie.
- Voeg de webhook URL toe via de Admin Panel (`Discord Webhook Configurations`). De plugin stuurt vervolgens geautomatiseerde berichten naar je Discord-kanaal zodra een lid een **Nieuwe Bestelling** plaatst of wanneer een **Quote is verstrekt**.

______________________________________________________________________

## 4. Systeem & Automatisering

De plugin draait voor een groot deel autonoom op de achtergrond dankzij Celery taken:

- **Prijzen**: De plugin haalt live data op van Fuzzwork API om betrouwbare ISK-waarden te berekenen voor Bill of Materials en orders.
- **Synchronisatie**: Elke 15 tot 30 minuten synchroniseert de plugin de Wallets, Corporate Inventory, Personal Jobs en Planetary Interaction via de EVE Swagger Interface (ESI).
- **Meertaligheid**: De interface ondersteunt meertaligheid. Als gebruikers hun taal in Alliance Auth aanpassen (bijv. naar Nederlands), zal de plugin automatisch de vertaalde interface tonen.
