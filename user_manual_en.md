# Industry Reforged - User Manual

This manual describes all features of the **Industry Reforged** plugin for Alliance Auth, categorized by user role.

______________________________________________________________________

## 1. For Members

### 1.1 Personal Dashboard

The Personal Dashboard is your primary hub for everything related to your personal EVE Online industry.

- **Manufacturing Jobs**: View the live status of all your personal manufacturing and reaction jobs. Real-time countdown timers show exactly when a job will finish, and a Character column shows exactly which character is running the job.
- **Research & Invention**: A dedicated tab to track your ME, TE, Copying, and Invention jobs. This tab features a grouped layout, neatly separating and organizing research jobs per character.
- **Planetary Interaction (PI)**: Track the status of your PI planets, including their exact System and Planet names. See at a glance if your extractor pins are still running, or view the real-time capacity and utilization of your Launchpads and Storage Facilities. You will automatically receive a Discord DM and an Alliance Auth notification if an extractor expires. Additionally, you can configure your own personal threshold (default 75%) to be warned when your storage facilities become full. The system also provides a "Supply & Demand" graph in the planet details view and visually warns you with an orange icon if an extraction deficit occurs (i.e., your factories consume more materials than you produce). You can configure a personalized threshold (e.g., 90%) to control when this deficit warning appears.
- **Discord Notifications**: If your Discord account is linked in Alliance Auth, the plugin will automatically send you a Direct Message (DM) as soon as an industry job finishes or when a PI extractor expires/storage fills up.

### 1.2 Orders Dashboard & Ordering

Members can use the plugin to order ships, modules, and structures from the corporation.

- **Placing an Order**: Click "New Order" and paste a complete *EFT/Pyfa fit* into the text box. Alternatively, you can copy-paste bulk item lists from the EVE Client (Multibuy format like `Drake 20`), or type items using natural language (e.g. `20 drakes`). The plugin will automatically parse the items, correct common plurals, and calculate the required Bill of Materials using your default Main Character.
- **Quoting Flow**: After submission, your order enters the `REQUESTED` status. A director will review the order and provide a price quote. Once done, the status changes to `QUOTED`.
- **Acceptance & Payment**: You can review the quote, compare it to estimated Jita prices to see your corporate discount (savings), and click "Accept Quote" to finalize it. The order is then forwarded to the corporate builders. Your order will be assigned a unique **Payment Reference** (e.g., `ORD-ABCD-1234`). You must transfer the ISK to the corporation wallet using this exact reference as the reason. The system will automatically detect your payment and mark the order as "Paid".
- **Delivery**: Once all builders complete their tasks, your order is ready. A director will contract the goods to you in-game and mark the order as "Delivered" in Auth, which will send you an in-app notification.

### 1.3 Buyback Program

The Buyback Program lets you sell items to the corporation: paste your inventory, get a price, and hand the items in with an in-game contract. Open it via **Buyback Program** in the menu.

**Selling items**

1. On the Buyback dashboard, click a program's name to see its **Rules & prices**: how items are valued, what is accepted, special prices per item or market group, where to drop off and who to make the contract out to.
1. Open the **Calculator**, choose a program and paste your items straight from the EVE inventory window (select the items, Ctrl+C, paste).
1. The calculator shows a price for every item, with a short note on how it was valued (for example market price, refined value or a fixed price) and why an item was refused, if it was. Below the list you see the base value, the program's modifier, any hauling cost and the net amount.
1. Optionally add a **donation** to the corporation (an ISK amount or a percentage) and a **note for the buyer**. Then submit to get your **tracking number** (for example `BB-1A2B3C4D`).
1. In EVE, create an **Item Exchange** contract:
   - make it out to the corporation or character shown on the contract page,
   - start it at one of the listed drop-off locations,
   - put the tracking number in the contract **title** (description),
   - ask exactly the **net amount** shown, and include exactly the appraised items.
1. Create the contract before the deadline shown on the contract page (7 days by default). If you don't, the tracking number expires.

**What happens next**

Every 15 minutes the plugin reads the in-game contracts and matches yours by its tracking number. It checks the items, price, location, recipient and title. A contract without issues is **Matched**; one with a difference is **Flagged** for a director to look at. Asking *less* than the quote is only noted; asking more gets the contract flagged.

As soon as the corporation accepts the contract in-game, it is marked **Paid** automatically. If it is rejected in-game or by a director you see **Rejected**, and if no contract shows up in time, **Expired**. If you delete your in-game contract the tracking number goes back to *Pending*, so you can create a new contract. While a contract is still *Pending* you can cancel it yourself from its page.

The contract page shows the status, the instructions and the appraised items. You get a Discord DM and an Auth notification when your contract is paid, rejected or expired. Use the **bell icon** on the Buyback dashboard to turn these messages off (or on again).

**More pages**

- **FAQ**: how the program works, plus questions and answers from your corporation's directors.
- **Statistics**: per program the total paid out, top sellers, top items, donations and a daily activity chart.
- **Monthly leaderboard**: sellers ranked by ISK paid out per month, with donations. You only see programs you are allowed to use.

**Public calculator**: a program can be opened to people without an Auth account (for example on a public link). They get a tracking number and a simple status page; they don't get messages.

Some items are never accepted: blueprints are always refused, and a program can refuse specific items or groups, assembled (unpacked) items, or everything without a rule. Depending on the program, one refused item either leaves just that item out or refuses the whole appraisal.

______________________________________________________________________

## 2. For Builders (Industrialists)

### 2.1 Industrialist Dashboard (Job Market)

This is the central marketplace for corporate builders.

- **Industry Status (MOTD)**: The top of the dashboard displays a real-time summary of the corporate industry, including the number of active orders, open tasks on the market, active corporate jobs, and the total ISK value in progress. This acts as a dynamic Message of the Day, complementing any manual announcements set by directors.
- **Job Market (Unclaimed)**: Once a member accepts an order, the system breaks the order down into individual Production Tasks. As a builder, you can "Claim" these tasks here. You can also select parent tasks to automatically claim all their sub-components.
- **Skill-Gated Jobs**: Some items (capital ships and components, Strategic Cruiser hulls/subsystems, advanced reaction formulas) require a specific EVE skill to build at all - independent of how many industry slots you have free. If none of your characters in this corp have the required skill, the job's row is disabled (checkbox and Claim button greyed out) with a tooltip naming exactly which skill and level is missing. This is a hard rule, not just a visual hint: claiming is also blocked server-side against whichever character the claim would be attributed to, even if a different alt on your account happens to qualify. When you do open the Claim modal for an eligible item, the "Your Live Detected Available Slots" badge shows the number of slots realistically usable for *that specific item* (only characters that are both in the corp and skill-eligible), not the generic total across your whole account.
- **Sub-Component Release**: If a job is skill-gated and you can't build it directly, its Bill-of-Materials sub-components (already broken down into their own tasks behind the scenes) become individually claimable in the Job Market instead, marked with a small "Released: parent needs a skill most members lack" note. This lets you contribute to an order even without the top-level skill - someone with the right skill can later claim the remaining assembly step directly, or the whole chain if they prefer. If a released sub-component is itself skill-gated for you, the same rule cascades one level deeper automatically.
- **Overdue Reminders**: If a job you've claimed runs past its estimated completion time (plus your corporation's configured grace period), you'll receive a reminder via an in-app Alliance Auth notification and a Discord DM, repeating periodically for as long as the job stays overdue. Unclaiming and reclaiming a task resets this.
- **Claimed Jobs**: A unified overview of the tasks you have claimed. You can dynamically filter this view to show only "Open (Active) Tasks", only "Completed Tasks", or "Show All Tasks". The lists are flattened for better oversight. Once you finish a job in EVE Online, you can mark the active tasks as "Complete" here. There are two types of complete buttons: the blue button marks just that single task as complete, while the yellow button marks that task and automatically completes all its child components as well. A "Material Progress" badge shows how much of the required components are available, accurately deducting materials that have already been consumed by EVE jobs in progress or completed parent tasks.
- **Build Steps**: A summarized, aggregated list of all items you need to build across all your claimed jobs. This view is logically grouped by Activity Type (such as Reactions, Manufacturing) to streamline your production process. It includes a text search bar, and clicking the copy icon next to an item name will copy it to your clipboard for easy pasting in-game. EVE Jobs in progress are subdivided into "EVE Active" (still cooking) and "EVE Ready" (ready to deliver), giving you clear insight into your production pipeline.
- **My Corporate Jobs**: A dedicated overview of all the EVE Online corporate jobs installed by your characters. This tab defaults to showing "Active" jobs. It features a smart time-window filter: it will automatically display unlinked jobs (such as EVE Reactions) as long as they were started on or after your oldest currently active claimed task, keeping your dashboard free of old, unrelated private jobs.
- **Builder Payouts**: Completed tasks that have an ISK reward are queued up for a payout. Directors will regularly bundle these into "Payout Batches". Once the corporation transfers the ISK to you with the batch's unique `PAY-` reference, the system automatically marks it as Paid.

### 2.2 Leaderboards & Gamification

- Every completed task rewards you with points (based on the ISK value of the produced item).
- On the **Leaderboard**, you can see who the most active builders in the corporation are, ranked both by total tasks completed and total ISK value produced.

### 2.3 Shopping List & Full Production Tree

- **Order & Task Shopping Lists**: Extremely useful for buyers and builders: generate a "Shopping List" of required raw materials for a specific order or a group of tasks. The flattened shopping list explicitly displays the currently available "Corp Stock" for each required material. You can copy this list with a single click in the EVE Online "Multibuy" format. The list uses a collapsible accordion design grouped by logical EVE categories (Minerals, Moon Goo, etc.), with automatic "Shortage" badges highlighting missing stock. Top-level items that are set to "BUY" (not built) are smartly excluded to prevent clutter.
- **Recursive BOM Drilldown**: When viewing the details of an Order, Industrialists have access to an exclusive **"Full Production Tree"** tab. This provides an interactive, recursive breakdown of the Bill of Materials based on the local SDE database. You can drill down through complex intermediate components all the way down to base raw materials (Minerals, PI, Moon Goo, etc.), including full support for **Reactions**.
- **Component Sourcing**: Next to every intermediate component in the Production Tree, you will find a dedicated Shopping Cart icon. Clicking it instantly generates a specific raw material shopping list for *that particular component* at the exact quantity required. This gives builders full flexibility to decide which sub-components they want to build themselves and which they prefer to buy off the market.

______________________________________________________________________

## 3. For Directors & Managers

### 3.1 Director Control Panel

The command center for the industrial backbone of the corporation.

- **Active Member Orders**: A comprehensive overview of all incoming member orders. You can use the quick filters to sort and view orders by their specific status (`Requested`, `Quoted`, `Accepted`, `In Production`, `Ready`, `Delivered`, etc.), showing their progress and automated payment status. Once an order's tasks are fully built, it shifts to `READY`. You can then contract the items in-game and click **"Deliver"** to notify the buyer.
- **Corporate Jobs Overview**: A master overview of all corporate EVE jobs across the alliance that are linked to a production task. Features a convenient status dropdown filter to quickly narrow down jobs by their EVE state (e.g., Active, Paused, Ready).
- **Quoting Flow (Profit & Loss)**: Click on any `REQUESTED` order to view its Profit & Loss analysis. This default view shows you the estimated raw material costs, current Jita market value, estimated build costs, and your final profit margin in one clear breakdown while setting the price.
- **Order Splitting & Suborders**: While an order is still in the `REQUESTED` state (before a quote is provided), you can split specific items or BOM components into separate "Child Orders". This is highly useful for routing different items or components to different production facilities.
  - **Suborder Management**: Child orders are managed entirely via their parent order. They do not have their own independent quotes or states; their status is strictly synchronized with the parent order.
  - **Important**: Once the parent order is quoted (status `QUOTED` or higher), the splitting options disappear. Additionally, if you split all items out of a main order into suborders, the main order will no longer show an itemized invoice, as it acts purely as a structural umbrella for the suborders.
- **Production Tasks**: Manage the individual building tasks. See who claimed which task and manually complete or revoke tasks if necessary. The table includes **Claimed At** (when the task was claimed) and **Estimated Done** columns - the latter prefers the real completion time reported by EVE's own industry job timer once the builder has started the job (shown with an "ESI" badge), and falls back to a claim-time estimate (shown with an "Est." badge) if they haven't started it yet or no job has been linked. Jobs running past their estimated completion time plus the configured grace buffer are highlighted in red. Filter the status dropdown to `IN_PRODUCTION` for a focused "who has what, and when it's due" overview.
- **Pending Payouts & Batches**: View a summary of unpaid rewards per builder. You can click **"Generate Batch"** to bundle a builder's pending tasks into a single payout with a unique `PAY-` reference. In the Active Payout Batches list, you can use the copy icons to easily copy the exact ISK amount and `PAY-` reference to your clipboard. When you transfer the ISK from the corp wallet to the builder using this reference, the system will automatically mark the batch as Paid.
- **Ledger Transactions**: A dedicated tab for tracking a comprehensive history of all internal payments (incoming order payments) and payouts (outgoing builder rewards). This ledger provides clear accountability and a financial overview of internal operations.
- **Procurement Buy Orders**: A dedicated tab for tracking purchases of items configured as "Buy" (e.g. Tritanium, PI). These are generated automatically or manually via the Inventory Analytics system. Directors can update the status of these orders (`Open`, `In Progress`, `Fulfilled`) to coordinate purchasing efforts.

### 3.2 Inventory & Analytics

- Full insight into the corporation's assets based on linked ESI Hangars.
- **Low Stock Alerts & Restocking**: Define target thresholds for specific items directly from the frontend interface. If the stock drops below this threshold, it appears in the "Restock Needed" alerts tab.
- **Auto-Produce / Procurement**: When setting a threshold, you can enable `Auto-Produce`. The background system will intelligently generate either a `ProductionTask` (if the item is marked as "Build") or a `CorpBuyOrder` (if marked as "Buy") whenever the stock falls short. You can also manually trigger this via the **"Spawn Job"** button.
- **Master Shopping List**: Generate a single, consolidated "Multibuy" shopping list containing all currently identified deficits across all items in a single click.

### 3.3 Corporate Wallets

- **View Balances**: Monitor the ISK balance across all 7 corporate wallet divisions.
- **Set Thresholds**: Directors can click the "Set Threshold" button inside any wallet division card to configure a specific **Warning Threshold** directly from the frontend using formatted ISK inputs. If the ISK balance drops below this amount, an automatic alert is sent to the configured Discord channel.
- **Automated Wallet Processing**: The background task that synchronizes wallets will automatically read journal entries. If it spots incoming ISK matching an `ORD-` payment reference, it marks the order as paid. If it spots outgoing ISK matching a `PAY-` reference, it marks the builder's payout batch as paid.

### 3.4 Configuration & Rules (Director Config)

- **Global Configurations**: Set whether the corporation "Builds" (BUILD) or "Buys" (BUY) specific items.
- Define manual ME/TE (Material/Time Efficiency) values and the desired threshold for "Low Stock Alerts" per item.
- **Order Item Exclusion**: Directors can configure specific items (e.g. Deadspace or Faction modules) to be automatically stripped from member orders. When checking the "Exclude from orders" option in the Item Configuration, you can also provide a custom warning message. When a member attempts to order the excluded item via an EFT fit, it is automatically removed from their order and they are shown your warning message (e.g. "Please acquire deadspace items yourself in Jita").
- **Tracked Hangars (Hangar Configurations)**: Before inventory can be synced, you must use "Discover Hangars" to instruct the plugin to scan your corporate assets. Discovered hangars will appear in the **Hangar Configurations** tab. To activate them for tracking in your Inventory and Low Stock Alerts, you must currently toggle them to *Active* via the Django Admin interface.
- **Production Facilities**: The plugin automatically discovers registered corporate Upwell structures and private structures based on active jobs and assets. Directors can then explicitly configure these discovered structures as active **Production Facilities** via the "Add Facility" dropdown. The true security space of the facility (Highsec, Lowsec, Nullsec/W-Space) is automatically determined. Installed structure rigs are synchronized automatically in the background using ESI corporate assets, providing a centralized overview of your industrial footprint. You can designate a primary default facility for manufacturing, and a separate default facility specifically for Reactions (Activity 11). This ensures your bill-of-materials accurately reflect your structure bonuses and rigs.
- **System Health Monitor**: Track the real-time execution status of all Celery background tasks directly from the frontend. This tab provides insights into the success/failure state, execution duration, and full Python error logs for tasks like ESI synchronizations and PI notifications.
- **Job Alerts (Overdue Buffer)**: Configure how long (in hours) a claimed job may run past its estimated completion time before the builder is notified it's overdue. The same number also sets the interval between repeat reminders for as long as a job stays overdue. Defaults to 2 hours if left unconfigured.

### 3.5 Corporate Configurations (Pricing & Taxes)

All business and pricing rules are managed strictly via the **Director Control Panel -> Configurations** tab in the frontend. This allows you to set rules for all allied corporations without requiring Django Admin access:

- **Global Pricing**: Configure the default corporate discount percentage and the builder reward percentage per corporation.
- **Minimum Margin Floor**: Define the minimum acceptable margin over the True Material Cost (the recursively calculated raw material cost) for item quotes and AI generated jobs.
- **Type Discounts**: Specify granular discounts per item category (e.g., ships vs. modules) for specific corporations.
- **Item Configurations (Manual Price Overrides)**: Manually override the Jita buy/sell price for specific items. This is highly useful for unique Faction items with erratic market histories, and is **strictly required for selling Blueprint Copies (BPCs)**.
  - *Note on Blueprint Pricing*: In EVE Online, both Blueprint Originals (BPOs) and Blueprint Copies (BPCs) share the exact same Type ID. Because BPCs cannot be listed on the regional market, the ESI API will always return the multi-billion ISK price of the BPO when you quote a Blueprint. To prevent your BPC quotes from being astronomically high, you must use this Item Configuration feature to explicitly set a manual price override (e.g., 500,000 ISK) for the blueprints you intend to sell.
- **System Taxes**: Define the standard Industry Tax and Broker Fee percentages applicable to your corporate production calculations.

### 3.6 Corporate Discord Webhooks

- In addition to Direct Messages for members, directors can configure corporate webhooks.
- **Language**: all posts to a corporation's webhooks use one fixed language, set in **Director Configurations -> Global Pricing -> Discord Messages** (empty means the installation default). It no longer depends on the language of the person who triggered the message. Direct messages to members use each member's own Alliance Auth language.
- Add your webhook URLs via the Django Admin Panel (`Discord Webhook Configurations`).
  - **Orders Webhook**: A general webhook for announcements when a member places a **New Order** or when a **Quote is provided**.
  - **Directors Webhook**: A specific webhook for Director-only action alerts, such as when a new quote needs to be calculated, when an order is **Ready for Delivery**, or a batched summary whenever claimed jobs become overdue (see **Job Alerts** in Director Config).
  - **AI Jobs Webhook**: Notifies the channel when the AI Market Manager automatically generates new Production Tasks based on your configured Baskets.
  - **Buyback Webhook**: New and flagged buyback contracts and suspicious contracts (see 3.8). Which contracts are posted, and whether the item list is included, is set per program on the Buyback tab.

### 3.7 AI Market Manager

The AI Market Manager automates the generation of Production Tasks by evaluating the market profitability and predicting future demand using an integrated AI Forecasting Service (LightGBM).

- **Baskets & Items**: Define Baskets and Basket Items via the Django Admin Panel to group items you want the AI to evaluate.
- **Profitability Calculation**: The system compares the Jita Sell price (adjusting for manual overrides) against the True Material Cost of the item. If the potential profit exceeds the `minimum_margin_floor` set in your Corporate Pricing Configuration, a Production Task is automatically generated.
- **Demand Forecasting**: The AI service ingests 90 days of ESI Market transaction data, along with external signals from Alliance Auth's **OpTimer module (Fleet Pings and Doctrines)**. It combines historical sales volume, price trends, and upcoming fleet deployments to predict the exact quantities needed over the next 7 days.
- **Automation**: The AI evaluation runs in the background (via Celery `industry_evaluate_ai_baskets`). Newly generated tasks automatically include the AI's predicted `qty_to_build` and appear on the Industrialist Job Market.

### 3.8 Buyback Program (Directors)

Everything is set up on the **Buyback** tab of **Director Configurations**. You only see and manage the programs of your own corporation. Contracts are read with the corporate token (`esi-contracts.read_corporation_contracts.v1`), or with the recipient character's personal token when a program sends contracts to a character.

**Program settings** (Add Program / edit icon)

- **Basics**: name, active, drop-off locations (one or more production facilities and/or known locations) and the deadline in days for members to create their contract.
- **Recipient**: the corporation, or a specific character (that character needs a personal token with `esi-contracts.read_character_contracts.v1`).
- **Tracking prefix**: the start of every tracking number (default `BB`, 1-10 capital letters or digits), so several programs can be told apart in-game.
- **Access**: limit the program to Auth groups and/or states (empty means everyone with basic access). Directors of the corporation always see their own programs. **Public** opens the calculator to people without an account; see the README for the required setting.
- **Price**: Jita **Buy**, **Sell** or **Split** price, plus a **price modifier** (for example `-10` pays 90%).
- **What is accepted**: *accept all items* (default) or only items and market groups that have a rule; optionally restricted to categories; assembled (unpacked) items on/off; and whether one refused item refuses the whole appraisal. Blueprints are always refused.
- **Ore, ice and moon ore**: value at the raw price, the compressed price and/or the refined minerals (at the refining rate); the highest enabled value is paid.
- **T1 scrap value**: ships, modules, charges, drones and subsystems up to meta level 4 can also be valued as reprocessed minerals (with their own scrap rate); the higher of market and scrap is paid.
- **NPC prices**: value Sleeper Components, Triglavian Survey Databases, Overseer's Personal Effects and/or SCC Encrypted Bonds at CCP's average price instead of the market.
- **Bulky items**: a *price density tax* (a percentage off items worth less than a set ISK/m³) or a *hauling cost* (ISK per m³ deducted from the total). Use one of the two, not both. Optionally use the compressed volume of ore for these.
- **Notifications**: post every new contract to the buyback Discord webhook (flagged contracts are always posted), optionally with the item list, and send a DM plus Auth notification to a manager character for each new contract.
- **Wallet division**: the corporation wallet that funds the program; its balance is shown on the program's performance page.

**Item rules, fixed prices and watchlist**

- **Item Rules**: raise, lower or block the price of one item or a whole market group (-100% to +100%, or *disallow*). A group rule also covers every group below it, and the most specific rule wins; the rule's percentage comes on top of the program modifier. Click **Load market groups** once before choosing a market group.
- **Fixed Prices**: pay a fixed ISK amount per unit for an item, regardless of the market (no modifier or density tax).
- **Watchlist**: items or item groups that need attention. Either flag the contract for review, or block the item in the calculator altogether.

Members see the item rules and fixed prices on the program's **Rules & prices** page; the watchlist is only shown to the program's directors.

**Review queue** (Review Flagged Contracts button)

- Lists contracts that are *Matched* or *Flagged*, with the reason for each flag (item, price, location, recipient, title, watchlist) and the seller's note. The contract page shows the appraised items next to the items in the actual in-game contract, with differences highlighted.
- Accepting the contract in-game is enough: at the next check the plugin marks it **Paid**, books the payout in the ledger and messages the seller. The **Pay** and **Reject** buttons (with a reason) are there for manual handling.
- **Suspicious contracts**: in-game contracts to the program's recipient that use its tracking prefix but a tracking number that was never issued. They are posted to Discord once and listed until you dismiss them.
- **Check contracts now** queues an immediate check instead of waiting for the next 15-minute run.

**What to do with the items (sell, reprocess, build material, to be sorted)**

Each contract page shows the program's directors what to do with every item it brings in, in four clearly coloured groups. The review queue shows how many items fall in each group per contract (*Advice* column).

- **Sell** (blue): worth more as-is.
- **Reprocess** (green): worth more as the materials it reprocesses into.
- **Build material** (teal): on the corporation's build-material list; it is kept, never sold.
- **To be sorted** (yellow): a director decides. Shown when no Jita price is known, when selling and reprocessing are within the margin you set, or when the advice would be to sell but the quantity is more than 5 days of Jita trade volume.

For every item you see the value sold straight to Jita buy orders and through a Jita sell order (after broker fee and sales tax), and the same two for the materials it reprocesses into (after the reprocessing tax). Only whole reprocessing batches count; the remainder is counted as sold. Below the table are two material lists with copy buttons: **Keep as build material** and **Sell after reprocessing**.

Reprocessed materials that are build materials, or that fill a low-stock shortage (when *Count stock shortages* is on), count as used in-house: they are valued at what buying them at Jita would cost, which can tip an item to *Reprocess*. A shortage is counted only once per contract.

**Build Materials** (Buyback tab): add single items (e.g. Tritanium) or market groups (e.g. Minerals; a group covers every group below it). Load the market groups once (Item Rules section) before choosing a group.

**Selling or reprocessing** (Buyback tab): the route the advice is based on (straight to buy orders or through a sell order), the reprocessing yield for ore/ice/moon ore and for everything else, the reprocessing tax, broker fee, sales tax, the margin for *To be sorted* and whether stock shortages count.

**FAQ**: add your own questions and answers in the Buyback FAQ section; members see them on the FAQ page next to the built-in explanation.

**Statistics**

- **Statistics** (all members): per program the totals, flag/rejection/expiry rates, average turnaround, top sellers, items and donors, and a daily chart for 7, 30 or 90 days.
- **Monthly leaderboard** (all members): sellers ranked by ISK paid out per month.
- **Performance** (the program's directors; chart icon on the Buyback tab or on the Statistics page): 12 months of contracts per status, ISK paid out and donations with a chart, the top item groups and items of the last 3 months, and the funding wallet's balance.
- **CSV export** (on the Performance page): every paid contract line with tracking number, dates, seller, item, group, quantity and price.

The buyback Discord webhook URL itself is set in the Django Admin (see 3.6).

______________________________________________________________________

## 4. System & Automation

The plugin runs largely autonomously in the background via Celery tasks:

- **Synchronization**: Every 15 to 30 minutes, the plugin synchronizes Wallets, Corporate Inventory, Personal Jobs, and Planetary Interaction via the EVE Swagger Interface (ESI).
- **Buyback Contracts**: Every 15 minutes the plugin reads the in-game contracts of each buyback program, matches them to tracking numbers and follows their status (paid, rejected, expired). Once a day, tracking numbers without a contract past their deadline are expired.
- **Overdue Job Checks**: Every 30 minutes, a background task scans all claimed jobs for anything past its estimated completion time (plus the configured grace buffer) and sends reminders to the builder and a summary to the directors' Discord webhook.
- **Multilingual Support (i18n)**: The interface supports multiple languages. If users change their preferred language in Alliance Auth (e.g., to Dutch), the plugin will automatically display the translated interface.

### 4.1 Bill of Materials (BOM) Calculation Engine

The plugin calculates the required materials for any job or order completely autonomously without relying on external API calls. This is achieved by utilizing the local EVE Online Static Data Export (SDE) provided by the `eveuniverse` package.

The calculation process follows these steps:

1. **Blueprint Resolution**: When an item is requested, the system queries the local database to find the specific blueprint and the corresponding activity (e.g., Manufacturing or Reactions) required to produce it.
1. **Yield & Run Calculation**: The system determines the base product yield per production run. It then divides the total requested quantity by this yield (rounding up) to calculate the exact number of production "runs" required.
1. **Material Efficiency (ME) Application**: Before calculating the total material cost, the system checks if a Director has configured a "Manual ME" discount for that specific item via the **Item Configurations** tab in the Director Dashboard.
1. **Material Requirements**: The system retrieves the raw list of required materials from the SDE and applies the standard EVE Online ME mathematical formula to calculate the exact amount of minerals, PI, or components needed.
1. **Recursive Drilldown**: When generating a "Full Production Tree" in the user interface, the system recursively repeats this entire process for all intermediate components, allowing users to drill down all the way to the rawest base materials (e.g., Moon Goo or Minerals).
