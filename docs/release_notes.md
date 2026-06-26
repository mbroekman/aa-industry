# Release Notes - Industry Reforged (Latest Update)

We are thrilled to announce a massive update to the **Industry Reforged** plugin! This release focuses on giving directors more control over the quoting process, introducing full Planetary Interaction (PI) tracking, expanding Discord integrations, and making the plugin fully translatable.

## 🚀 New Features

### 1. Planetary Interaction (PI) Tracking & Alerts

- **PI Dashboard**: Members can now track their PI planets directly from the Personal Dashboard.
- **Extractor & Storage Monitoring**: Keep an eye on active extractor pins and monitor storage facilities.
- **Discord DM Alerts**: Never let an extractor sit idle! The plugin automatically sends a Direct Message via Discord when an extractor cycle finishes or when a storage facility reaches its maximum capacity.

### 2. Professional Quoting Workflow

- **Director Approval Flow**: We transitioned from an automated quoting system to a manual, professional quoting flow. Orders now go through three stages: `REQUESTED` -> `QUOTED` -> `ACCEPTED`.
- **Custom Quotes**: Directors can click on any requested order, view the estimated Bill of Materials (BOM) cost based on live Fuzzwork data, and provide a custom quote.
- **Member Acceptance**: Members can review the provided quote, see exactly how much ISK they save compared to Jita estimates, and accept or reject the quote.
- **Traceability**: The Order Details screen now tracks and displays precise timestamps (with icons) for when the order was Created, Quoted, and Accepted.

### 3. Expanded Discord Integrations

- **Corporate Webhooks**: Directors can now configure a Discord Webhook URL via the Admin Panel.
- **Automated Alerts**: The designated Discord channel receives automatic pings whenever a member places a **New Order** or whenever a Director submits a **New Quote**.

### 4. Multilingual Support (i18n)

- **100% Translatable**: The entire plugin—every view, model, and template—has been wrapped in Django's translation framework (`gettext`).
- **Included structure**: A `django.po` file is now generated and ready. Server admins can easily translate the app into Dutch, German, or any other language, allowing the plugin to adapt seamlessly to the user's Alliance Auth language preferences.

## 💅 UI/UX Enhancements

- **Modern Tabbed Navigation**: Dashboards (like the Director Control Panel and Inventory Analytics) have been restructured using sleek, standard Bootstrap tabs. This removes clutter and fits perfectly with any native Alliance Auth theme.
- **Dynamic Warning Badges**: The Director Inventory page now features a dynamic red badge on the "Low Stock Alerts" tab, instantly showing the exact number of critical shortages.
- **Intelligent Navigation**: All hardcoded "Back" buttons have been replaced with dynamic `history.back()` logic, ensuring users always return to their previous context (e.g., specific tabs or filtered lists) without losing their place.

## 🛠️ Under the Hood

- Improved robust permission checking for accepting quotes (bypassing complex template nested relations by resolving ownership directly in the views).
- Added multi-line strings and `f-string` fixes to the translation extractor.
- Database models `MemberOrder` expanded with `quoted_at` and `accepted_at` fields.
