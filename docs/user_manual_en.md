# Industry Reforged - User Manual

This manual describes all features of the **Industry Reforged** plugin for Alliance Auth, categorized by user role.

______________________________________________________________________

## 1. For Members

### 1.1 Personal Dashboard

The Personal Dashboard is your primary hub for everything related to your personal EVE Online industry.

- **My Industry Jobs**: View the live status of all your personal manufacturing and research jobs. Real-time countdown timers show exactly when a job will finish.
- **Planetary Interaction (PI)**: Track the status of your PI planets. See at a glance if your extractor pins are still running or if your storage facilities are nearing maximum capacity.
- **Discord Notifications**: If your Discord account is linked in Alliance Auth, the plugin will automatically send you a Direct Message (DM) as soon as an industry job finishes or when a PI extractor expires/storage fills up.

### 1.2 Orders Dashboard & Ordering

Members can use the plugin to order ships, modules, and structures from the corporation.

- **Placing an Order**: Click "New Order", select a character, and paste a complete *EFT/Pyfa fit* into the text box. The plugin will automatically parse and calculate the required Bill of Materials.
- **Quoting Flow**: After submission, your order enters the `REQUESTED` status. A director will review the order and provide a price quote. Once done, the status changes to `QUOTED`.
- **Acceptance**: You can review the quote, compare it to estimated Jita prices to see your corporate discount (savings), and click "Accept Quote" to finalize it. The order is then forwarded to the corporate builders.

______________________________________________________________________

## 2. For Builders (Industrialists)

### 2.1 Industrialist Dashboard (Job Market)

This is the central marketplace for corporate builders.

- **Industry Status (MOTD)**: The top of the dashboard displays a real-time summary of the corporate industry, including the number of active orders, open tasks on the market, active corporate jobs, and the total ISK value in progress. This acts as a dynamic Message of the Day, complementing any manual announcements set by directors.
- **Job Market (Unclaimed)**: Once a member accepts an order, the system breaks the order down into individual Production Tasks. As a builder, you can "Claim" these tasks here.
- **My Active Production**: An overview of the tasks you have claimed and are currently building. Once you finish a job in EVE Online, you can mark the task as "Complete" here.

### 2.2 Leaderboards & Gamification

- Every completed task rewards you with points (based on the ISK value of the produced item).
- On the **Leaderboard**, you can see who the most active builders in the corporation are, ranked both by total tasks completed and total ISK value produced.

### 2.3 Shopping List & Full Production Tree

- **Order & Task Shopping Lists**: Extremely useful for buyers and builders: generate a "Shopping List" of required raw materials for a specific order or a group of tasks. You can copy this list with a single click in the EVE Online "Multibuy" format.
- **Recursive BOM Drilldown**: When viewing the details of an Order, Industrialists have access to an exclusive **"Full Production Tree"** tab. This provides an interactive, recursive breakdown of the Bill of Materials. You can drill down through complex intermediate components all the way down to base raw materials (Minerals, PI, etc.).
- **Component Sourcing**: Next to every intermediate component in the Production Tree, you will find a dedicated Shopping Cart icon. Clicking it instantly generates a specific raw material shopping list for *that particular component* at the exact quantity required. This gives builders full flexibility to decide which sub-components they want to build themselves and which they prefer to buy off the market.

______________________________________________________________________

## 3. For Directors & Managers

### 3.1 Director Control Panel

The command center for the industrial backbone of the corporation.

- **Active Member Orders**: A comprehensive overview of all incoming member orders.
- **Quoting Flow**: Click on any `REQUESTED` order to view its Bill of Materials and provide a custom, manual Quote. You will immediately see the estimated raw material costs while setting the price.
- **Production Tasks**: Manage the individual building tasks. See who claimed which task and manually complete or revoke tasks if necessary.

### 3.2 Inventory & Analytics

- Full insight into the corporation's assets based on linked ESI Hangars.
- **Low Stock Alerts**: Define target thresholds for specific items. If the stock drops below this threshold, a red "Action Required" badge will appear, ensuring you never run out of essential ships or modules.

### 3.3 Corporate Wallets

- Monitor the ISK balance across all 7 corporate wallet divisions.
- View and filter the detailed **Journal** to analyze corporate income and expenses (e.g., order payments or tax incomes).

### 3.4 Configuration & Rules (Director Config)

- **Global Configurations**: Set whether the corporation "Builds" (BUILD) or "Buys" (BUY) specific items.
- Define manual ME/TE (Material/Time Efficiency) values, fixed prices, and the desired threshold for "Low Stock Alerts" per item.
- **Discover Hangars**: Before inventory can be synced, you must use "Discover Hangars" to instruct the plugin *which* specific corporate hangars in which structures should be monitored.

### 3.5 Corporate Discord Webhooks

- In addition to Direct Messages for members, directors can configure corporate webhooks.
- Add your webhook URL via the Django Admin Panel (`Discord Webhook Configurations`). The plugin will then send automated alerts to your designated Discord channel whenever a member places a **New Order** or when a **Quote is provided**.

______________________________________________________________________

## 4. System & Automation

The plugin runs largely autonomously in the background via Celery tasks:

- **Pricing Engine**: The plugin fetches live market data from the Fuzzwork API to calculate reliable ISK values for Bills of Materials and orders.
- **Synchronization**: Every 15 to 30 minutes, the plugin synchronizes Wallets, Corporate Inventory, Personal Jobs, and Planetary Interaction via the EVE Swagger Interface (ESI).
- **Multilingual Support (i18n)**: The interface supports multiple languages. If users change their preferred language in Alliance Auth (e.g., to Dutch), the plugin will automatically display the translated interface.
