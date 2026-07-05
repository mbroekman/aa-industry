# Alliance Auth Industry Plugin

[![PyPI version](https://img.shields.io/pypi/v/aa-industry-reforged)](https://pypi.org/project/aa-industry-reforged/)
[![Python versions](https://img.shields.io/pypi/pyversions/aa-industry-reforged)](https://pypi.org/project/aa-industry-reforged/)
[![Tests](https://github.com/mbroekman/aa-industry/actions/workflows/automated-checks.yml/badge.svg)](https://github.com/mbroekman/aa-industry/actions/workflows/automated-checks.yml)


A powerful plugin for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) to help corporation and alliance members track their EVE Online industry operations. This app utilizes the EVE Swagger Interface (ESI) to synchronize industry jobs directly into your Alliance Auth environment.

## Features

- **Personal Dashboard**: Users can easily track their active, completed, and delivered industry jobs.
- **Corporate Dashboard**: Directors and Managers can monitor all corporate industry jobs from a centralized overview.
- **Member Portal (Self-Service)**: Members can request hulls, structures, or components, paste EFT fits directly to automatically parse requirements, and go through a professional quoting flow (Director approval -> User acceptance).
- **Industrialist Dashboard (Job Market)**: Corp builders can claim automated production tasks, track their history, compete on Gamification Leaderboards, and view real-time industry statistics via the Dynamic MOTD.
- **Recursive BOM Drilldown & Shopping List Treeview**: Builders and Directors can interactively drill down through complex order Bills of Materials to the base raw materials, generating customized EVE Multibuy shopping lists for specific intermediate components, and view fully interactive Production Trees directly within the Consolidated Shopping Lists.
- **Director Control Panel**: Complete ERP solution for directors to manage orders, provide custom quotes, prioritize tasks, analyze missing stock, and set rules for Material Efficiency and Prices entirely from the front-end (no Django Admin access required).
- **Corporate Wallets**: Track ISK balances and journal transactions across all 7 corporate wallet divisions.
- **Smart ISK Formatting**: Features a built-in abbreviation engine that automatically formats large ISK values and displays precise tooltip translations (e.g., K, M, B, T) when hovered.
- **Core Engine & Automation**: Automated Celery tasks to synchronize Corporate ESI Hangars, calculate complex Bills of Materials (SDE vs Fuzzwork API), and trigger jobs based on Target Thresholds.
- **Planetary Interaction (PI)**: Monitor PI planets, extractor pins, production facilities, and countdown timers for active extraction.
- **Discord Integration**: 
  - **Direct Messages**: Receive automatic DMs via Discord when a personal industry job finishes or when PI extractors expire / storage fills up.
  - **Corporate Webhooks**: Send alerts to a designated Discord channel when new orders are placed, quotes are updated, or orders are fully built and ready for delivery.
- **Automated Payment Tracking**: Generate unique references for member orders and builder payouts. The background ESI Wallet Sync task automatically reads the corporate wallet journal, accumulates partial payments, logs them as order notes, and marks orders as "Paid" once the full amount is reached. Supports upfront payment requirements (downpayments).
- **System Health Monitor**: A dedicated tab in the Director Configurations page that provides real-time logging and status updates for all Celery background tasks, including exact execution duration and Python error stack traces.
- **Multilingual Support (i18n)**: Fully translatable UI using Django gettext (`django.po`). Prepare custom translations for your community (e.g., English, Dutch, etc.).
- **DataTables**: Clean, sortable, and searchable tables for quick insights.
- **Modern UI**: Consistent, tab-based layouts integrating natively with standard Alliance Auth themes.
- **SDE Integration**: Resolves blueprint and product Type IDs into readable names and official EVE Online icons automatically by typing item names.

## Prerequisites

Before installing this plugin, ensure your Alliance Auth instance meets the following requirements:

- Alliance Auth v5.x
- **django-esi** v4.0.0+ (Included by default in Alliance Auth v5.x)
- **django-eveuniverse**: Used for resolving Type IDs to Item Names and Icons.
- **Alliance Auth Discord Bot** (`aadiscordbot`): Required if you want users to receive Direct Messages upon job completion or if you intend to use Corporate Webhooks.
- A working Celery setup (standard in Alliance Auth) for background synchronization tasks.

## Installation

1. **Activate your virtual environment**:

   ```bash
   source /path/to/venv/bin/activate
   ```

1. **Install the App**:
   From your application directory (or via PyPI if published):

   ```bash
   pip install -e /path/to/aa-industry-reforged
   ```

1. **Configure Settings**:
   Add the app and its dependencies to your `INSTALLED_APPS` inside `myauth/settings/local.py`:

   ```python
   INSTALLED_APPS += [
       "eveuniverse",
       "industry_reforged",
   ]
   ```

1. **Load Industry Data**:
   To ensure the app can calculate Bills of Materials for both Manufacturing and Reactions without relying on third-party APIs, you must load the EVE Online Industry Activities into your local database:

   ```bash
   python manage.py eveuniverse_load_data types --types-enabled-sections industry_activities
   ```
   *(Note: This creates background tasks. Depending on your Celery workers, it may take a few minutes to fully populate the database).*

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
- `industry.industrialist_access`: Grants access to the Industrialist Dashboard, allowing users to view the job market and claim production tasks (intended for corporate builders).
- `industry.corp_access`: Grants access to the Corporate Dashboard and Director Control Panel (intended for Directors or Industry Managers).

### 3. Required ESI Scopes (SSO Grants)

This plugin requires specific ESI scopes depending on the features you want to use. Make sure these are configured in your Alliance Auth Eve Online SSO settings:

- **`esi-industry.read_character_jobs.v1`**: Required for Personal Dashboard. Users grant this via the "Add Personal Token" button.
- **`esi-industry.read_corporation_jobs.v1`**: Required for Corporate Dashboard. Directors grant this via the "Add Corporate Token" button.
- **`esi-planets.manage_planets.v1`**: Required for Planetary Interaction tracking. Users grant this via the AA Tokens page.
- **`esi-assets.read_corporation_assets.v1`**: Required for the Core Engine to synchronize Corporate Inventory Hangars. Directors grant this via the "Add Corporate Token" button.
- **`esi-universe.read_structures.v1`**: Required to resolve public Upwell structure names in EVE. Directors grant this via the "Add Corporate Token" button.
- **`esi-corporations.read_structures.v1`**: Required for the Director Control Panel to discover and resolve names for structures owned by the corporation. Directors grant this via the "Add Corporate Token" button.
- **`esi-wallet.read_corporation_wallets.v1`**: Required to track corporate wallet balances and journal transactions. Directors grant this via the "Add Corporate Token" button.

#### Automating Scopes for all Users
To prevent members from having to manually authorize additional PI or Industry tokens, you can configure Alliance Auth to **automatically request these scopes** during the standard "Add Character" login flow. Add the following to your `myauth/settings/local.py`:

```python
LOGIN_TOKEN_SCOPES = [
    'publicData',
    'esi-planets.manage_planets.v1',
    'esi-industry.read_character_jobs.v1',
]
```
*(This ensures every character added to your Auth natively supports the personal dashboards without requiring a separate "Grant Token" button click).*

### 4. Corporate Inventory Setup

To track your corporate inventory, you **must explicitly configure which hangars to track** (to avoid syncing thousands of irrelevant items and hitting ESI rate limits):

1. Navigate to the **Director Dashboard** and click **Configurations**.
1. Click the **Discover Hangars** button to scan your corporation's assets via ESI.
1. Add the specific hangars (e.g. "Corp Hangar 1") that you want to track.
1. Go to the **Director Inventory** page and click the **Sync Inventory** button to manually force an initial sync. After that, the background Celery task will keep it updated.

*Note: Corporate Sync Configuration is automatically created when a Director clicks the 'Add Corporate Token' button.*

### 5. Pricing & Builder Rewards

By default, the Industry Reforged quote engine uses raw Jita prices (and `0%` builder rewards). To customize this:

1. Navigate to the **Director Dashboard** and click **Configurations**.
2. Under the **Global Pricing** tab, you can set:
   - **Default Discount**: A global discount applied to raw materials (e.g., `10.0` for 10% off Jita for alliance members).
   - **Builder Reward Percent**: The percentage of the total ship/item value that should be calculated and presented as a direct ISK payout for the industrialist who builds it.

### 6. Background Syncing

The app relies on Celery tasks to periodically fetch data from EVE Online. To run these tasks automatically, add the following to your `myauth/settings/local.py`:

```python
from celery.schedules import crontab

if "CELERYBEAT_SCHEDULE" not in locals():
    CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE["industry_update_character_jobs"] = {
    "task": "industry_reforged.tasks.update_character_jobs",
    "schedule": crontab(minute="*/30"),
}

CELERYBEAT_SCHEDULE["industry_update_corporation_jobs"] = {
    "task": "industry_reforged.tasks.update_corporation_jobs",
    "schedule": crontab(minute="*/30"),
}

CELERYBEAT_SCHEDULE["industry_update_character_pi"] = {
    "task": "industry_reforged.tasks.update_character_pi",
    "schedule": crontab(minute="0"),
}

CELERYBEAT_SCHEDULE["industry_sync_corp_inventory"] = {
    "task": "industry_reforged.tasks.task_sync_corp_inventory",
    "schedule": crontab(minute="*/15"),
}

CELERYBEAT_SCHEDULE["industry_pull_market_data"] = {
    "task": "industry_reforged.tasks.task_pull_market_data",
    "schedule": crontab(hour="11", minute="30"),  # Around EVE Downtime
}

CELERYBEAT_SCHEDULE["industry_sync_corp_wallets"] = {
    "task": "industry_reforged.tasks.task_sync_corp_wallets",
    "schedule": crontab(minute="*/30"),
}

CELERYBEAT_SCHEDULE["industry_notify_pi_extractors"] = {
    "task": "industry_reforged.tasks.task_notify_expired_extractors",
    "schedule": crontab(minute="15,45"),  # Twice an hour
}
```

After updating `local.py`, be sure to restart your Celery worker and Celery Beat services.

## License
Copyright (c) 2026 Maddog Broekman. All rights reserved.
Licensed under the [MIT License](LICENSE).
