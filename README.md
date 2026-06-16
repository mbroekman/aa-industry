# Alliance Auth Industry Plugin

A powerful plugin for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) to help corporation and alliance members track their EVE Online industry operations. This app utilizes the EVE Swagger Interface (ESI) to synchronize industry jobs directly into your Alliance Auth environment.

## Features

- **Personal Dashboard**: Users can easily track their active, completed, and delivered industry jobs.
- **Corporate Dashboard**: Directors and Managers can monitor all corporate industry jobs from a centralized overview.
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

### 3. Adding ESI Tokens

- **Personal Jobs**: Users must log in, open the **Industry App**, and click the **Add Personal Token** button on the dashboard. This will prompt Eve SSO to grant the required `esi-industry.read_character_jobs.v1` scope.
- **Corporate Jobs**: A character with the **Director** role must click the **Add Corporate Token** button on the Corporate Dashboard. Afterwards, an admin must link this character in the Django Admin interface under **Corporation Sync Configuration**.
- **Planetary Interaction**: To view PI data, the user must authorize the `esi-planets.manage_planets.v1` scope via the Alliance Auth Tokens / Services page.

### 4. Background Syncing

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
```

After updating `local.py`, be sure to restart your Celery worker and Celery Beat services.
