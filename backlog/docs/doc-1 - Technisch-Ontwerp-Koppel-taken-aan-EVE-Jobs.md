______________________________________________________________________

## id: doc-1 title: 'Technisch Ontwerp: Koppel taken aan EVE Jobs' type: guide created_date: '2026-08-03 18:08'

# Technical Design: Linking Claimed Tasks to EVE Industry Jobs

## Achtergrond

Wanneer een gebruiker een `ProductionTask` claimt (accepteert), zal hij of zij in EVE Online de daadwerkelijke industry jobs (manufacturing, reactions, etc.) installeren in een structure. Momenteel weet AA-Industry wel *dat* er jobs draaien via ESI, maar er is geen keiharde koppeling (foreign key) tussen een specifieke `ProductionTask` in de web-app en de `CharacterIndustryJob` / `CorporationIndustryJob` in EVE Online.

De wens is om deze te koppelen, met de volgende uitdagingen:

1. EVE Online biedt geen mogelijkheid om "metadata" (zoals een Task ID) mee te geven aan een industry job.
1. Gebruikers claimen een taak vaak met hun "Main" karakter in de applicatie, maar starten de jobs in EVE met gespecialiseerde "Alt" karakters.
1. Jobs kunnen zowel persoonlijke (Character) als corporatie (Corporation) jobs zijn.

## Haalbaarheid: Is het mogelijk?

**Ja, het is mogelijk via "Heuristische Matching".**
Omdat we in Alliance Auth exact weten welke EVE Characters tot de gebruiker behoren (via `CharacterOwnership`), kunnen we jobs van alle alts van de gebruiker monitoren en deze met een hoge mate van zekerheid koppelen aan de openstaande taken van de gebruiker.

## Implementatie Strategie

### 1. Alt-karakter herkenning (User Scope)

In Alliance Auth zijn alts gekoppeld aan de `User` via het `CharacterOwnership` model.
Om jobs te vinden die bij een taak horen, zoeken we niet alleen naar jobs gestart door het `assigned_to` karakter, maar door alle karakters van de user:

```python
user_characters = (
    task.assigned_to.character_ownerships.first()
    .user.character_ownerships.all()
    .values_list("character_id", flat=True)
)
```

### 2. Matching Logica (Heuristiek)

Om een inkomende ESI job te koppelen aan een `ProductionTask`, gebruiken we de volgende regels:

1. **Installer**: De `installer_id` van de job (Corp of Character) zit in `user_characters`.
1. **Type Match**: `job.product_type_id == task.item_type_id`.
1. **Activity Match**: `job.activity_id == task.activity_id`.
1. **Tijd Match**: De job is gestart (`start_date`) *nadat* (of vlak voordat, afhankelijk van een kleine marge) de taak is geclaimd.
1. **Beschikbaarheid**: De job is niet al (volledig) gekoppeld aan een andere task.

### 3. Datamodel Wijzigingen

In plaats van de ESI-gesyncte job-modellen (`CharacterIndustryJob` / `CorporationIndustryJob`) aan te passen, maken we een nieuw koppel-model in `industry_reforged/models/jobs.py` (of `orders.py`):

```python
class TaskJobLink(models.Model):
    task = models.ForeignKey(
        ProductionTask, on_delete=models.CASCADE, related_name="linked_jobs"
    )
    # Omdat jobs in twee verschillende tabellen kunnen staan (Char vs Corp), gebruiken we ofwel GenericForeignKey,
    # of twee nullable velden:
    character_job = models.ForeignKey(
        CharacterIndustryJob, on_delete=models.CASCADE, null=True, blank=True
    )
    corporation_job = models.ForeignKey(
        CorporationIndustryJob, on_delete=models.CASCADE, null=True, blank=True
    )

    # Hoeveel 'runs' van deze job gelinkt zijn aan deze specifieke taak (als 1 job meerdere taken dekt)
    linked_runs = models.IntegerField(default=1)
```

### 4. Background Celery Task (De Matcher)

Tijdens of direct na de reguliere ESI job sync (`update_character_jobs` en `update_corporation_jobs`), draait een nieuwe task: `link_orphaned_jobs_to_tasks`.
Deze task pakt alle ongekoppelde actieve jobs en zoekt naar openstaande `IN_PRODUCTION` tasks van dezelfde user die matchen op product, activity, en tijd.
Zodra een match is gevonden, wordt een `TaskJobLink` aangemaakt.

### 5. Frontend & UI

- **Dashboard**: Bij actieve taken (`ProductionTask`) kan een dropdown of lijst getoond worden met de gelinkte EVE Jobs, inclusief de resterende tijd (`end_date`) of status ("Delivered").
- **Auto-completion**: Als alle gekoppelde jobs op status `delivered` komen en het totaal aantal gefabriceerde eenheden gelijk is aan de `quantity` van de taak, kan het systeem de speler proactief voorstellen de taak af te ronden, of dit (optioneel) automatisch doen.

## Conclusie

Het is functioneel zeer goed mogelijk. De implementatie vereist het toevoegen van een koppel-model en een matching-algoritme dat periodiek (via Celery) draait om ESI data aan interne taken te binden, over alle alts van de gebruiker heen.
