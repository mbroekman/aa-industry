# Alliance Auth Industry Plugin Development Guide

## 1. Introduction

Building an Industry plugin for Alliance Auth (AA) is a great way to help corporation and alliance members track their manufacturing, research, and reaction jobs. This document provides strategic advice and an architectural overview for developing this plugin using the EVE Online Swagger Interface (ESI).

## 2. Core Objectives

The primary goal of the plugin should be to provide visibility into industry operations.
Recommended MVP (Minimum Viable Product) features:

- **Personal Dashboard**: Users can view their own active and completed industry jobs.
- **Corporate Dashboard**: Directors/Managers can view corporation-level industry jobs.
- **System Cost Indices**: View current system cost indices for planning.
- **Discord Notifications**: Automated Discord alerts for completed corporate industry jobs, and private DMs for completed personal jobs.

## 3. Architecture & Tech Stack

Since Alliance Auth is built on the Django framework, your plugin will be a standard Django App integrated into the AA ecosystem.

- **Backend**: Python 3, Django (aligned with your current AA version).
- **Frontend**: HTML/Django Templates, Bootstrap 3/5 (depending on AA version and theme), jQuery/Vanilla JS.
- **Task Queue**: Celery (for background syncing of ESI data).
- **API Client**: `django-esi` (standard ESI client used by Alliance Auth).

## 4. ESI API Integration

The EVE Online API provides specific endpoints for Industry under the [API Explorer](https://esi.evetech.net/ui/#/Industry).

### Handling Corporations and Members

Alliance Auth natively manages the relationship between users (Main Accounts), their Characters, Corporations, and Alliances via the `eveonline` module. You don't need to reinvent the wheel for this.

- **Personal Jobs**: Any member who adds a token with the required scope will have their jobs synced.
- **Corporate Jobs**: To fetch corporate jobs, the ESI API requires a token from a character that holds the **Director** (or Factory Manager) role in the game. You should create a configuration model (e.g., `CorporationSyncConfig`) where a Director can register their corporation to be tracked by providing their token.

### Required ESI Scopes

To fetch data, users will need to authorize your application with the following scopes via `django-esi`:

- `esi-industry.read_character_jobs.v1` (For personal jobs)
- `esi-industry.read_corporation_jobs.v1` (For corporate jobs - requires Director roles)

### Key Endpoints to Utilize

1. **Character Jobs**: `GET /characters/{character_id}/industry/jobs/`
1. **Corporation Jobs**: `GET /corporations/{corporation_id}/industry/jobs/`
1. **Facilities**: `GET /industry/facilities/` (To map facility IDs to names/locations)
1. **System Indices**: `GET /industry/systems/` (To help users find cheap manufacturing systems)

> [!WARNING]
> **Data Caching & Rate Limits**
> ESI responses contain standard cache headers (e.g., `Expires` or `Cache-Control`). It is critical to respect these timers and not poll the API more frequently than allowed to avoid being error-rate limited.

## 5. Data Modeling

Avoid fetching data from ESI on page load. Instead, use Celery tasks to synchronize ESI data into local Django database models.

Recommended Django Models:

- `CharacterIndustryJob`: Stores character-level jobs.
- `CorporationIndustryJob`: Stores corp-level jobs.
- `IndustryFacility`: Local cache of facilities.

*Example Model Concept:*

```python
from django.db import models
from eveonline.models import EveCharacter


class CharacterIndustryJob(models.Model):
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    job_id = models.IntegerField(primary_key=True)
    activity_id = models.IntegerField()
    blueprint_type_id = models.IntegerField()
    status = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    # ... other fields mapped from ESI
```

## 6. Background Tasks (Celery)

Set up Celery periodic tasks (`@shared_task`) to synchronize the database with ESI.

- **Task 1: Update Character Jobs**: Runs every 1-2 hours. Iterates through all users who have granted the required token and fetches their active jobs.
- **Task 2: Update Corporation Jobs**: Runs periodically for tracked corporations using a director's token.
- **Task 3: Cleanup**: Periodically purges jobs that have been completed/delivered for more than 30 days to save database space.

> [!TIP]
> **Use Celery Task Chaining**
> Instead of one massive task that updates everyone, create a master task that spawns a sub-task for each character. This prevents one failing ESI call from stopping the entire sync process.

## 7. Discord Integration (Alerts)

To implement the requested Discord notification functionality, you can utilize the `allianceauth.services.modules.discord` module (if the AA Discord service is enabled) or standard webhooks.

- **Corporate Jobs**: When the Celery task detects a corporation job has transitioned to 'completed', use a Discord webhook to send an alert to a designated Industry channel.
- **Personal Jobs**: When a character's personal job finishes, use the AA Discord service to send a Private Message (DM) to the linked Discord user. This requires that the user has their Discord account linked in Alliance Auth.

## 8. Permissions and Security

Security is paramount in Alliance Auth. Utilize Django's permission system to restrict access.

- `industry.basic_access`: Allows a user to view the app and their own personal jobs.
- `industry.corp_access`: Allows a user to view corporation-level jobs. Assign this only to Director/Logistics roles.

## 9. Dashboard Data Definitions

To provide a clear and actionable overview, the dashboards should display specific data columns extracted from ESI.

### Personal Dashboard (Character Jobs)

- **Activity Type**: An icon or label (e.g., Manufacturing, ME Research, TE Research, Copying, Invention, Reactions).
- **Blueprint / Output Item**: The name and icon of the item being produced or researched.
- **Runs**: The number of runs for the job.
- **Success Probability**: The percentage chance of a successful invention job.
- **Successful Runs**: The amount of successful runs (applicable after an invention job is completed).
- **Install Cost**: The ISK cost paid to install the job.
- **Status**: Current state of the job (e.g., Active, Ready to Deliver, Completed, Cancelled).
- **Time Remaining / End Date**: A live countdown timer for active jobs, or the exact date it finished.
- **Location**: The solar system or facility where the job is installed.

### Corporate Dashboard (Corporation Jobs)

Includes all columns from the Personal Dashboard, plus:

- **Installer**: The name (and avatar) of the corporation member who started the job.
- **Wallet Division**: The corp wallet division used to pay for the job (useful for auditing).

## 10. Frontend & UI Best Practices

- **DataTables**: Industry jobs generate a lot of tabular data. Use the DataTables library (included in AA) to allow users to sort, filter, and search their jobs easily.
- **Timers**: Use JavaScript (or libraries like moment.js) to show live countdown timers for active jobs based on the `end_date`.
- **Eve Images**: Utilize the EVE Image Server (`images.evetech.net`) to display icons for blueprints and output products, making the UI visually appealing.

## 11. Next Steps

1. Define your Django models in `models.py`.
1. Set up the `django-esi` token requirements in your app configuration.
1. Write the Celery tasks in `tasks.py` to fetch and store data.
1. Create views and templates to display the data to the user.
1. Test thoroughly with a dev character before deploying to a live Alliance Auth instance.
