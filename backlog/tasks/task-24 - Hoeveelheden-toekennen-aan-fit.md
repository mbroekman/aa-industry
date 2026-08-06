# Task 24: Hoeveelheden toekennen aan een fit

## Status

DONE

## Description

Gebruikers gaven aan dat het niet mogelijk is om aantallen toe te kennen aan een fit via het `create order` formulier. Het steeds opnieuw plakken van een EFT fit of handmatig aantallen aanpassen is niet wenselijk.
De oplossing hiervoor is een globaal `Quantity (Multiplier)` veld toevoegen. Hiermee wordt de gehele output (alle items en hoeveelheden) na het inlezen van de fit vermenigvuldigd.

## Acceptance Criteria

- [x] HTML Formulier op de `Create Order` pagina bevat een 'Quantity (Multiplier)' nummerveld.
- [x] In `create_order.py` wordt deze uitgelezen (`fit_multiplier`) en worden de `parsed_items` hiermee vermenigvuldigd.
- [x] Aan de originele fit tekst wordt een kleine melding geprepend zodat zichtbaar is dat er een multiplier is toegepast in de database.
- [x] Getest en gecommit.
