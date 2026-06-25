# Release Notes: Industry Reforged v0.1.0b2

We are excited to announce the release of **v0.1.0b2**! This beta update introduces the highly anticipated "Bill of Materials" (BOM) engine, vastly improving the quality of life for our corporation industrialists by automating material calculations and streamlining the procurement process.

## 🚀 New Features

- **Dynamic Bill of Materials (BOM) Engine**

  - Integrated a fully functional BOM engine that automatically fetches the exact manufacturing material requirements for any item directly via the Fuzzwork Blueprint API.
  - *Smart Efficiency:* The BOM engine intelligently detects your Corporation's Material Efficiency (ME) configurations (`CorpItemConfig`) and automatically applies the discounts to the required quantities.

- **Consolidated Shopping Lists**

  - **Order Bulk Selection:** Users can now select multiple active orders from the Orders Dashboard using checkboxes and generate a single, consolidated shopping list.
  - **Task Bulk Selection:** Extended to the Industrialist Dashboard! Industrialists can check off multiple unclaimed jobs from the Job Market, or active jobs in their queue, to calculate the aggregate materials needed to fulfill them.

- **EVE Multibuy Integration**

  - The Consolidated Shopping List page now includes a **"Copy for EVE Multibuy"** button. One click copies all your required materials and quantities to the clipboard, perfectly formatted so you can paste it straight into EVE Online's Multibuy window in Jita.

- **Quote Breakdown UI**

  - Detailed quotes now feature a sleek, dark-themed accordion element revealing the complete Bill of Materials needed for that specific quote, alongside estimated Jita unit prices and total material costs.

## 🐛 Bug Fixes & Improvements

- **Duplicate Notification Fix:** Addressed an issue where Django's `messages` were being rendered twice across all dashboard templates (Orders, Industrialist, Create Order, Shopping List, Quotes). The plugin now fully defers to Alliance Auth's native base template for displaying flash messages, ensuring a cleaner UI.
- **Database ID Resolution:** Fixed an edge-case bug in the BOM generation logic on the Industrialist dashboard where the application mistakenly compared internal Django database IDs against EVE Online character IDs, which previously resulted in empty shopping lists for claimed tasks.
- **Nested Forms Refactor:** Replaced nested HTML forms in the Industrialist Dashboard with a robust Javascript-based checkbox collection system. This resolves the issue where only the first selected item would be passed to the Shopping List generator.

______________________________________________________________________

*Thank you for testing the beta! We're constantly working to improve your manufacturing workflows.*
