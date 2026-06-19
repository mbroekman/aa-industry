# Alliance Auth Industry Plugin

A powerful plugin for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) to help corporation and alliance members track their EVE Online industry operations. This app utilizes the EVE Swagger Interface (ESI) to synchronize industry jobs directly into your Alliance Auth environment.

## Features

- **Personal Dashboard**: Users can easily track their active, completed, and delivered industry jobs.
- **Corporate Dashboard**: Directors and Managers can monitor all corporate industry jobs from a centralized overview.
- **Member Portal (Self-Service)**: Members can request hulls, structures, or components, paste EFT fits directly to automatically parse requirements, and receive real-time quotes.
- **Industrialist Dashboard (Job Market)**: Corp builders can claim automated production tasks, track their history, and compete on the Gamification Leaderboards.
- **Director Control Panel**: Complete ERP solution for directors to manage orders, prioritize tasks, analyze missing stock, and set rules for Material Efficiency and Prices.
- **Core Engine & Automation**: Automated Celery tasks to synchronize Corporate ESI Hangars, calculate complex Bills of Materials (SDE vs Fuzzwork API), and trigger jobs based on Target Thresholds.
- **Planetary Interaction (PI)**: Monitor PI planets, extractor pins, production facilities, and countdown timers for active extraction.
- **Discord Integration**: Receive automatic Direct Messages via Discord when a personal industry job finishes.
- **DataTables**: Clean, sortable, and searchable tables for quick insights.
- **Countdown Timers**: Real-time countdown timers indicating exactly when active jobs will finish.
- **SDE Integration**: Resolves blueprint and product Type IDs into readable names and official EVE Online icons.

## Prerequisites

Before installing this plugin, ensure your Alliance Auth instance meets the following requirements:

- Alliance Auth v5.x
- **django-esi** v4.0.0+ (Included by default in Alliance Auth v5.x)
- **django-eveuniverse**: Used for resolving Type IDs to Item Names and Icons.
- **Alliance Auth Discord Service**: Required if you want users to receive Direct Messages upon job completion.
- A working Celery setup (standard in Alliance Auth) for background synchronization tasks.

## Installation

1. **Activate your virtual environment**:

   ```bash
   source /path/to/venv/bin/activate
   ```

1. **Install the App**:
   From your application directory (or via PyPI if published):

   ```bash
   pip install -e /path/to/aa-industry
   ```

1. **Configure Settings**:
   Add the app and its dependencies to your `INSTALLED_APPS` inside `myauth/settings/local.py`:

   ```python
   INSTALLED_APPS += [
       "eveuniverse",
       "industry",
   ]
   ```

1. **Run Migrations**:
   Update your database to include the new models.

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

1. **Restart Services**:
   Restart your Gunicorn/Supervisor and Celery worker so the changes take effect.

   ```bash
   sudo systemctl restart myauth
   sudo systemctl restart myauth-celery
   ```

## Configuration & Usage

### 1. Load EveUniverse Data

Since this plugin relies on `django-eveuniverse` to resolve Item Types, make sure the basic EVE universe data is loaded. You may need to run the standard EveUniverse load commands to pull the latest SDE types if you haven't already.

### 2. Permissions

Assign the following permissions in the Django Admin panel:

- `industry.basic_access`: Grants access to the Personal Dashboard (intended for all members).
- `industry.corp_access`: Grants access to the Corporate Dashboard (intended for Directors or Industry Managers).

### 3. Required ESI Scopes (SSO Grants)

This plugin requires specific ESI scopes depending on the features you want to use. Make sure these are configured in your Alliance Auth Eve Online SSO settings:

- **`esi-industry.read_character_jobs.v1`**: Required for Personal Dashboard. Users grant this via the "Add Personal Token" button.
- **`esi-industry.read_corporation_jobs.v1`**: Required for Corporate Dashboard. Directors grant this via the "Add Corporate Token" button.
- **`esi-planets.manage_planets.v1`**: Required for Planetary Interaction tracking. Users grant this via the AA Tokens page.
- **`esi-assets.read_corporation_assets.v1`**: Required for the Core Engine to synchronize Corporate Inventory Hangars. Directors grant this via the "Add Corporate Token" button.
- **`esi-universe.read_structures.v1`**: Required to resolve public Upwell structure names in EVE. Directors grant this via the "Add Corporate Token" button.
- **`esi-corporations.read_structures.v1`**: Required for the Director Control Panel to discover and resolve names for structures owned by the corporation. Directors grant this via the "Add Corporate Token" button.

### 4. Corporate Inventory Setup

To track your corporate inventory, you **must explicitly configure which hangars to track** (to avoid syncing thousands of irrelevant items and hitting ESI rate limits):

1. Navigate to the **Director Dashboard** and click **Configurations**.
1. Click the **Discover Hangars** button to scan your corporation's assets via ESI.
1. Add the specific hangars (e.g. "Corp Hangar 1") that you want to track.
1. Go to the **Director Inventory** page and click the **Sync Inventory** button to manually force an initial sync. After that, the background Celery task will keep it updated.

*Note: For Corporate Syncs, an Admin must link the Director character in the Django Admin interface under **Corporation Sync Configuration**.*

### 5. Background Syncing

The app relies on Celery tasks to periodically fetch data from EVE Online. To run these tasks automatically, add the following to your `myauth/settings/local.py`:

```python
from celery.schedules import crontab

if "CELERYBEAT_SCHEDULE" not in locals():
    CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE["industry_update_character_jobs"] = {
    "task": "industry.tasks.update_character_jobs",
    "schedule": crontab(minute="*/30"),
}

CELERYBEAT_SCHEDULE["industry_update_corporation_jobs"] = {
    "task": "industry.tasks.update_corporation_jobs",
    "schedule": crontab(minute="*/30"),
}

CELERYBEAT_SCHEDULE["industry_update_character_pi"] = {
    "task": "industry.tasks.update_character_pi",
    "schedule": crontab(minute="0"),
}

CELERYBEAT_SCHEDULE["industry_sync_corp_inventory"] = {
    "task": "industry.tasks.task_sync_corp_inventory",
    "schedule": crontab(minute="*/15"),
}

CELERYBEAT_SCHEDULE["industry_pull_market_data"] = {
    "task": "industry.tasks.task_pull_market_data",
    "schedule": crontab(hour="11", minute="30"),  # Around EVE Downtime
}
```

After updating `local.py`, be sure to restart your Celery worker and Celery Beat services.
