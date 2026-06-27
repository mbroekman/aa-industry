# Voorstel: Alliance Auth Groepen & Permissies (Industry Reforged)

Om de **Industry Reforged** plugin veilig en overzichtelijk in gebruik te nemen binnen jullie Alliance Auth installatie, adviseer ik om de toegangsrechten te verdelen over drie specifieke groepen.

De plugin heeft onder water drie kern-permissies gedefinieerd:

- `basic_access`
- `industrialist_access`
- `corp_access`

Hieronder vind je het voorstel voor de inrichting van de groepen (Groups) in Alliance Auth, en hoe je deze koppelt aan de permissies.

______________________________________________________________________

## 1. De "Member" of "Industry User" Groep

Deze groep is voor de gewone leden van de alliantie of corporatie. Zij zijn de "klanten" van jullie industrie-afdeling.

- **Doelgroep:** Iedereen in de corporatie/alliantie.
- **Benodigde Permissie:** `industry_reforged.basic_access`
- **Wat ze hiermee kunnen:**
  - De app openen in het zijmenu van Alliance Auth.
  - Hun persoonlijke Planetary Interaction (PI) dashboard inzien en de Discord-alerts hiervoor ontvangen.
  - Nieuwe orders aanvragen via de "Create Order" knop (EFT fits plakken).
  - Hun eigen actieve orders inzien, offertes (quotes) accepteren of weigeren, en de voortgang bekijken.

> [!TIP]
> Als jullie willen dat *iedereen* in de corporatie orders mag plaatsen en hun PI mag tracken, kun je de `basic_access` permissie simpelweg toevoegen aan de standaard `Member` groep in Alliance Auth (die iedereen automatisch krijgt bij het aanmaken van een account). Je hoeft dan geen aparte "Industry User" groep aan te maken.

______________________________________________________________________

## 2. De "Industrialist" of "Builder" Groep

Deze groep is voor de spelers die de daadwerkelijke productie voor hun rekening nemen. Zij zijn de werkbijen van de industrie.

- **Doelgroep:** Leden van het industrie-team / bouwers.
- **Benodigde Permissies:**
  - `industry_reforged.basic_access`
  - `industry_reforged.industrialist_access`
- **Wat ze hiermee kunnen:**
  - Alles wat de gewone leden kunnen.
  - Het **Industrialist Dashboard** openen.
  - Openstaande productietaken (Production Tasks) inzien die voortkomen uit de geaccepteerde orders.
  - Taken "claimen" om ze te gaan bouwen.
  - Taken markeren als "voltooid".
  - Meedoen in het Gamification/Leaderboard systeem.

> [!NOTE]
> Industrialists kunnen wél taken zien en oppakken, maar ze kunnen **geen** prijzen aanpassen, offertes opmaken of in de corp-portemonnee kijken. Dit beschermt de financiële kant van de corporatie.

______________________________________________________________________

## 3. De "Industry Director" Groep

Dit is de leidinggevende rol. Zij beheren de configuratie, accepteren de order-aanvragen en voorzien deze van een (custom) offerte.

- **Doelgroep:** Industrie-directeuren, corporatie-leiders.
- **Benodigde Permissies:**
  - `industry_reforged.basic_access`
  - `industry_reforged.industrialist_access`
  - `industry_reforged.corp_access`
- **Wat ze hiermee kunnen:**
  - Alles wat leden en bouwers kunnen.
  - Het **Director Dashboard** openen.
  - **Orders beheren:** Binnengekomen aanvragen (`REQUESTED`) inzien, BOM-kosten berekenen en een offerte (`QUOTED`) uitbrengen.
  - **Corporatie Configuratie:** Hangar-syncs opzetten, wallet-divisies in de gaten houden.
  - **Prijzen:** Winstmarges (kortingen/opslaan ten opzichte van Jita) instellen in de Pricing Config.
  - **Webhooks:** Discord webhooks configureren voor de hele corporatie.

______________________________________________________________________

## Samenvattend Overzicht

| Functionaliteit / View          | Member | Industrialist | Director |
| :------------------------------ | :----: | :-----------: | :------: |
| Persoonlijke PI Tracking        |   ✅   |      ✅       |    ✅    |
| Zelf Orders Aanvragen           |   ✅   |      ✅       |    ✅    |
| Zelf Quotes Accepteren/Weigeren |   ✅   |      ✅       |    ✅    |
| Leaderboard Bekijken            |   ✅   |      ✅       |    ✅    |
| Taken Claimen & Bouwen          |   ❌   |      ✅       |    ✅    |
| Quotes Maken voor Anderen       |   ❌   |      ❌       |    ✅    |
| Corp Config, Hangars & Wallets  |   ❌   |      ❌       |    ✅    |
