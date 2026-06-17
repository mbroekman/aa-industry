# Walkthrough: Member Portal (Ordering & Quotes)

Het Member Portal is nu live! We hebben een gloednieuw self-service portaal gebouwd waarmee leden zelf schepen en modules kunnen aanvragen.

## Wat is er gebouwd?

1. **Nieuwe Navigatie:** In het linkermenu staat nu **Member Orders**. Dit is het centrale dashboard voor alle aanvragen.
1. **Fit Parser:** Leden kunnen via de "New Order" knop direct een in-game of Pyfa/EFT fit in het tekstvak plakken. De parser leest de hull, modules, en cargo (inclusief `x5` hoeveelheden) slim uit!
1. **Fuzzwork Pricing Engine:** Zodra het lid op "Generate Quote" klikt, zoekt de server real-time contact met de *Fuzzwork Market API* om de actuele **Jita 5% Sell Price** op te halen voor alle benodigde onderdelen.
1. **Corp Discounts:** Via de Django Admin (`/admin/industry/corppricingconfig/`) kan een beheerder per corporatie een basis-korting (bijv. 10%) instellen, én zelfs specifieke kortingen per item type overschrijven!
1. **Quote Workflow:** Het lid krijgt direct een gespecificeerde rekening ("Itemized Invoice") te zien met de kortingen en het totaalbedrag. Ze kunnen deze vervolgens **Accepten** of **Rejecten**.
1. **Order Tracking:** Op het orders dashboard zien leden de actuele status van hun bestellingen (bijv. In Production, Ready for Pickup).

## Hoe test je dit?

1. Zorg ervoor dat je bent ingelogd op Alliance Auth.
1. Klik in het linkermenu op de nieuwe knop **Member Orders**.
1. Klik op **New Order**.
1. Kopieer een willekeurige fit uit EVE (Copy to Clipboard) of verzin er eentje (bijv. `[Drake, Test]`) en plak deze in het tekstvak.
1. Druk op **Generate Quote**. Het systeem praat nu met Fuzzwork en toont je binnen een seconde een factuur met actuele Jita prijzen!

> [!TIP]
> Vergeet niet om in het Admin panel een `Corp Pricing Config` aan te maken als je kortingen wilt toepassen. Zonder config rekent het systeem gewoon de 100% Jita prijs!
