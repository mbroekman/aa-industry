# Multilanguage-implementatie

Zoals afgesproken in Optie B, is de gehele plugin "vertaal-klaar" gemaakt en is de basisstructuur voor de Nederlandse taal (nl) klaargezet. We hebben echt alles gepakt: van alle Director schermen, Member schermen, tot de backend logica en database modellen.

## Wat is er gedaan?

1. **Python Bestanden**: Er is een script gedraaid dat alle hardgecodeerde teksten in `views.py` en `models.py` netjes in een `_()` (gettext) functie heeft gewikkeld, zodat Django weet dat dit te vertalen tekst is. Speciale aandacht ging hierbij uit naar "f-strings" en multi-line log meldingen.
1. **Templates**: De HTML-bestanden stonden voor een groot deel al vol met de juiste `{% trans %}` tags.
1. **Taalbestand gegenereerd**: Het commando `django-admin makemessages -l nl` is uitgevoerd. Hierdoor heeft Django de gehele codebase doorzocht en een centraal vertaalbestand aangemaakt met maar liefst **630+ te vertalen zinnen**.

## Wat moet je nu doen?

Omdat je controle wilt houden over de vertaling van EVE Online specifieke termen, is de bal nu aan jou!

**Actiepunten:**

1. Open het volgende bestand in je code editor of een programma zoals [Poedit](https://poedit.net/):
   `/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/locale/nl/LC_MESSAGES/django.po`
1. In dit bestand zie je paren van `msgid` (Engels) en `msgstr` (Leeg).
1. Vul bij `msgstr ""` de Nederlandse vertaling in tussen de aanhalingstekens. (Als je iets in het Engels wilt laten staan, kopieer dan de Engelse tekst naar de `msgstr`).
1. Zodra je klaar bent met vertalen en het `.po` bestand hebt opgeslagen, moet je de vertalingen "compileren" zodat Alliance Auth ze kan lezen.

### Vertalingen Compileren (als je klaar bent)

Draai in je terminal (vanuit de map `aa-industry/industry_reforged` met je virtual environment geactiveerd) het volgende commando:

```bash
django-admin compilemessages
```

Dit genereert een `.mo` bestand. Herstart daarna even Gunicorn/je lokale Django server. Als de gebruiker in Alliance Auth de voorkeurstaal op "Nederlands" heeft staan, zal de volledige Industry Reforged plugin direct in het Nederlands verschijnen!
