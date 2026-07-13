# Industry Reforged - User Manual

This manual describes all features of the **Industry Reforged** plugin for Alliance Auth, categorized by user role.

______________________________________________________________________

## 1. For Members

### 1.1 Personal Dashboard

The Personal Dashboard is your primary hub for everything related to your personal EVE Online industry.

- **My Industry Jobs**: View the live status of all your personal manufacturing and research jobs. Real-time countdown timers show exactly when a job will finish.
- **Planetary Interaction (PI)**: Track the status of your PI planets. See at a glance if your extractor pins are still running or view the real-time capacity and utilization of your Launchpads and Storage Facilities.
- **Discord Notifications**: If your Discord account is linked in Alliance Auth, the plugin will automatically send you a Direct Message (DM) as soon as an industry job finishes or when a PI extractor expires/storage fills up.

### 1.2 Orders Dashboard & Ordering

Members can use the plugin to order ships, modules, and structures from the corporation.

- **Placing an Order**: Click "New Order" and paste a complete *EFT/Pyfa fit* into the text box. Alternatively, you can copy-paste bulk item lists from the EVE Client (Multibuy format like `Drake 20`), or type items using natural language (e.g. `20 drakes`). The plugin will automatically parse the items, correct common plurals, and calculate the required Bill of Materials using your default Main Character.
- **Quoting Flow**: After submission, your order enters the `REQUESTED` status. A director will review the order and provide a price quote. Once done, the status changes to `QUOTED`.
- **Acceptance & Payment**: You can review the quote, compare it to estimated Jita prices to see your corporate discount (savings), and click "Accept Quote" to finalize it. The order is then forwarded to the corporate builders. Your order will be assigned a unique **Payment Reference** (e.g., `ORD-ABCD-1234`). You must transfer the ISK to the corporation wallet using this exact reference as the reason. The system will automatically detect your payment and mark the order as "Paid".
- **Delivery**: Once all builders complete their tasks, your order is ready. A director will contract the goods to you in-game and mark the order as "Delivered" in Auth, which will send you an in-app notification.

______________________________________________________________________

## 2. For Builders (Industrialists)

### 2.1 Industrialist Dashboard (Job Market)

This is the central marketplace for corporate builders.

- **Industry Status (MOTD)**: The top of the dashboard displays a real-time summary of the corporate industry, including the number of active orders, open tasks on the market, active corporate jobs, and the total ISK value in progress. This acts as a dynamic Message of the Day, complementing any manual announcements set by directors.
- **Job Market (Unclaimed)**: Once a member accepts an order, the system breaks the order down into individual Production Tasks. As a builder, you can "Claim" these tasks here. You can also select parent tasks to automatically claim all their sub-components.
- **My Member Tasks**: A unified overview of the tasks you have claimed. You can dynamically filter this view to show only "Open (Active) Tasks", only "Completed Tasks", or "Show All Tasks". Once you finish a job in EVE Online, you can mark the active tasks as "Complete" here. Parent tasks can only be completed once all sub-tasks are done.
- **Builder Payouts**: Completed tasks that have an ISK reward are queued up for a payout. Directors will regularly bundle these into "Payout Batches". Once the corporation transfers the ISK to you with the batch's unique `PAY-` reference, the system automatically marks it as Paid.

### 2.2 Leaderboards & Gamification

- Every completed task rewards you with points (based on the ISK value of the produced item).
- On the **Leaderboard**, you can see who the most active builders in the corporation are, ranked both by total tasks completed and total ISK value produced.

### 2.3 Shopping List & Full Production Tree

- **Order & Task Shopping Lists**: Extremely useful for buyers and builders: generate a "Shopping List" of required raw materials for a specific order or a group of tasks. You can copy this list with a single click in the EVE Online "Multibuy" format.
- **Recursive BOM Drilldown**: When viewing the details of an Order, Industrialists have access to an exclusive **"Full Production Tree"** tab. This provides an interactive, recursive breakdown of the Bill of Materials based on the local SDE database. You can drill down through complex intermediate components all the way down to base raw materials (Minerals, PI, Moon Goo, etc.), including full support for **Reactions**.
- **Component Sourcing**: Next to every intermediate component in the Production Tree, you will find a dedicated Shopping Cart icon. Clicking it instantly generates a specific raw material shopping list for *that particular component* at the exact quantity required. This gives builders full flexibility to decide which sub-components they want to build themselves and which they prefer to buy off the market.

______________________________________________________________________

## 3. For Directors & Managers

### 3.1 Director Control Panel

The command center for the industrial backbone of the corporation.

- **Active Member Orders**: A comprehensive overview of all incoming member orders, showing their progress and automated payment status. Once an order's tasks are fully built, it shifts to `READY`. You can then contract the items in-game and click **"Deliver"** to notify the buyer.
- **Quoting Flow**: Click on any `REQUESTED` order to view its Bill of Materials and provide a custom, manual Quote. You will immediately see the estimated raw material costs while setting the price.
- **Production Tasks**: Manage the individual building tasks. See who claimed which task and manually complete or revoke tasks if necessary.
- **Pending Payouts & Batches**: View a summary of unpaid rewards per builder. You can click **"Generate Batch"** to bundle a builder's pending tasks into a single payout with a unique `PAY-` reference. When you transfer the ISK from the corp wallet to the builder using this reference, the system will automatically mark the batch as Paid.

### 3.2 Inventory & Analytics

- Full insight into the corporation's assets based on linked ESI Hangars.
- **Low Stock Alerts**: Define target thresholds for specific items. If the stock drops below this threshold, a red "Action Required" badge will appear, ensuring you never run out of essential ships or modules.

### 3.3 Corporate Wallets

- Monitor the ISK balance across all 7 corporate wallet divisions.
- View and filter the detailed **Journal** to analyze corporate income and expenses (e.g., order payments or tax incomes).
- **Automated Wallet Processing**: The background task that synchronizes wallets will automatically read journal entries. If it spots incoming ISK matching an `ORD-` payment reference, it marks the order as paid. If it spots outgoing ISK matching a `PAY-` reference, it marks the builder's payout batch as paid.

### 3.4 Configuration & Rules (Director Config)

- **Global Configurations**: Set whether the corporation "Builds" (BUILD) or "Buys" (BUY) specific items.
- Define manual ME/TE (Material/Time Efficiency) values and the desired threshold for "Low Stock Alerts" per item.
- **Order Item Exclusion**: Directors can configure specific items (e.g. Deadspace or Faction modules) to be automatically stripped from member orders. When checking the "Exclude from orders" option in the Item Configuration, you can also provide a custom warning message. When a member attempts to order the excluded item via an EFT fit, it is automatically removed from their order and they are shown your warning message (e.g. "Please acquire deadspace items yourself in Jita").
- **Tracked Hangars (Hangar Configurations)**: Before inventory can be synced, you must use "Discover Hangars" to instruct the plugin to scan your corporate assets. Discovered hangars will appear in the **Hangar Configurations** tab. To activate them for tracking in your Inventory and Low Stock Alerts, you must currently toggle them to *Active* via the Django Admin interface.
- **Production Facilities**: The plugin automatically discovers registered corporate Upwell structures and private structures based on active jobs and assets. Directors can then explicitly configure these discovered structures as active **Production Facilities** via the "Add Facility" dropdown. The true security space of the facility (Highsec, Lowsec, Nullsec/W-Space) is automatically determined. Installed structure rigs are synchronized automatically in the background using ESI corporate assets, providing a centralized overview of your industrial footprint.
- **System Health Monitor**: Track the real-time execution status of all Celery background tasks directly from the frontend. This tab provides insights into the success/failure state, execution duration, and full Python error logs for tasks like ESI synchronizations and PI notifications.

### 3.5 Corporate Configurations (Pricing & Taxes)

All business and pricing rules are managed strictly via the **Director Control Panel -> Configurations** tab in the frontend. This allows you to set rules for all allied corporations without requiring Django Admin access:

- **Global Pricing**: Configure the default corporate discount percentage and the builder reward percentage per corporation.
- **Type Discounts**: Specify granular discounts per item category (e.g., ships vs. modules) for specific corporations.
- **Item Configurations**: Manually override the Jita buy/sell price for specific items (highly useful for unique Faction items with erratic market histories).
- **System Taxes**: Define the standard Industry Tax and Broker Fee percentages applicable to your corporate production calculations.

### 3.6 Corporate Discord Webhooks

- In addition to Direct Messages for members, directors can configure corporate webhooks.
- Add your webhook URLs via the Django Admin Panel (`Discord Webhook Configurations`).
  - **Orders Webhook**: A general webhook for announcements when a member places a **New Order** or when a **Quote is provided**.
  - **Directors Webhook**: A specific webhook for Director-only action alerts, such as when a new quote needs to be calculated or when an order is **Ready for Delivery**.

______________________________________________________________________

## 4. System & Automation

The plugin runs largely autonomously in the background via Celery tasks:

- **Synchronization**: Every 15 to 30 minutes, the plugin synchronizes Wallets, Corporate Inventory, Personal Jobs, and Planetary Interaction via the EVE Swagger Interface (ESI).
- **Multilingual Support (i18n)**: The interface supports multiple languages. If users change their preferred language in Alliance Auth (e.g., to Dutch), the plugin will automatically display the translated interface.

### 4.1 Bill of Materials (BOM) Calculation Engine

The plugin calculates the required materials for any job or order completely autonomously without relying on external API calls. This is achieved by utilizing the local EVE Online Static Data Export (SDE) provided by the `eveuniverse` package.

The calculation process follows these steps:

1. **Blueprint Resolution**: When an item is requested, the system queries the local database to find the specific blueprint and the corresponding activity (e.g., Manufacturing or Reactions) required to produce it.
1. **Yield & Run Calculation**: The system determines the base product yield per production run. It then divides the total requested quantity by this yield (rounding up) to calculate the exact number of production "runs" required.
1. **Material Efficiency (ME) Application**: Before calculating the total material cost, the system checks if a Director has configured a "Manual ME" discount for that specific item via the **Item Configurations** tab in the Director Dashboard.
1. **Material Requirements**: The system retrieves the raw list of required materials from the SDE and applies the standard EVE Online ME mathematical formula to calculate the exact amount of minerals, PI, or components needed.
1. **Recursive Drilldown**: When generating a "Full Production Tree" in the user interface, the system recursively repeats this entire process for all intermediate components, allowing users to drill down all the way to the rawest base materials (e.g., Moon Goo or Minerals).
