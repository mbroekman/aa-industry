# Discord Webhook Notifications Implementation

## What has been implemented?

1. **Configuration Models**

   - The `CorporationWebhookConfig` model has been completed and is available.
   - The database fields for timers (`last_warning` for wallets and `last_low_stock_warning` for inventory) are active in `CorpWalletDivision` and `CorpItemConfig`.
   - The configuration has been successfully registered in the Django Admin, where directors can easily configure the URLs.

1. **Discord Utility**

   - The `send_discord_webhook` function in `industry_reforged/utils/discord.py` is available and used to send beautifully formatted "Embed" messages with color coding to the Discord webhooks.

1. **Database Migrations**

   - A correct migration was already generated (`0011_corpitemconfig_last_low_stock_warning_and_more.py`).

1. **Order Webhooks (`views.py`)**

   - **New Orders**: When a quote/order is requested, a notification is posted to Discord.
   - **Quote Accepted**: As soon as a player accepts the quote and tasks are generated, a green success message follows.
   - **Quote Rejected**: A warning message follows upon rejection.

1. **Background Tasks & Triggers (`tasks.py`)**

   - **Corporate Jobs**: When a corporate industry job reaches the "ready" status via the ESI sync, a yellow/gold message is sent to Discord.
   - **Wallets**: The ESI sync for corp wallets now checks whether the balance drops below the configured `wallet_warning_threshold` (default 500 million ISK). If so, and no warning has been sent in the past 24 hours, a red alert message is dispatched.
   - **Inventory**: The ESI sync for corp inventory checks across all configured hangars. If the total stock of an item drops below the configured threshold, and the last warning was issued more than 24 hours ago, a red warning is sent to Discord.

## Verification

- **Pre-commit**: All changes have been validated with the `pre-commit` tool suite. The code is safe and correctly formatted using `black`.

> [!TIP]
> The functionality is now ready for use! Make sure to fill in the Discord Webhook URLs in the Django Admin for the respective channels to receive the notifications.
